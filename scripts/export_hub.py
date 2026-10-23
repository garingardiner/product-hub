#!/usr/bin/env python3
"""Export initiative manifests and data files as JSON rows for the Product Hub page.

Usage: python scripts/export_hub.py   (requires: pip install pyyaml)
Writes build/hub/*.json (row arrays) and build/hub/db/*.json ({"rows": [...]} documents for the
interactive hub's `snapshot` collection). Skips _template and any folder with "example" in its slug.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import status

ROOT = status.ROOT
OUT = ROOT / "build" / "hub"
ARTIFACT_LABELS = {
    "concept": "Concept", "feedback": "Feedback", "project_spec": "Project spec", "ux_spec": "UX spec",
    "success_metrics": "Success metrics", "engineering_scope": "Engineering scope", "feature_benefits": "Feature/Benefits",
}

def text(v):
    return "" if v is None else str(v)

def main():
    rows = {k: [] for k in ("initiatives", "artifacts", "requirements", "hypotheses", "metrics", "decisions",
                            "feedback", "evidence", "feedback_snapshot", "attachments")}
    lib_path = ROOT / "feedback" / "library.json"
    lib = json.loads(lib_path.read_text(encoding="utf-8")) if lib_path.exists() else {}
    for e in lib.get("entries") or []:
        rows["feedback"].append({
            "id": e.get("id"), "date": text(e.get("date")), "customer": text(e.get("customer")),
            "contact": text(e.get("contact")), "link": text(e.get("link")),
            "segment": text(e.get("segment")), "type": text(e.get("type")), "sentiment": text(e.get("sentiment")),
            "source": text(e.get("source")), "quote": text(e.get("quote")), "summary": text(e.get("summary")),
            "tags": ", ".join(e.get("tags") or []), "initiative": text(e.get("initiative")),
            "requirements": ", ".join(e.get("requirements") or []),
        })
    rows["feedback_snapshot"].append({
        "exported_at": text(lib.get("exported_at")), "exported_on": text(lib.get("exported_at"))[:10], "entries": len(lib.get("entries") or []), "note": text(lib.get("note")),
    })
    folders = sorted(p for p in (ROOT / "initiatives").iterdir()
                     if p.is_dir() and not p.name.startswith("_") and "example" not in p.name)
    for f in folders:
        m, errors, gate = status.check(f)
        slug, phase = m.get("slug", f.name), m.get("phase")
        arts = m.get("artifacts") or {}
        reqs = status.load(f / "requirements.yaml").get("requirements") or []
        fb = status.load(f / "feedback.yaml")
        hyps = fb.get("hypotheses") or []
        data_gaps = status.data_checks(f, phase)
        nxt = status.PHASES[status.PHASES.index(phase) + 1] if phase in status.PHASES[:5] else ""
        rows["initiatives"].append({
            "slug": slug, "name": m.get("name", slug), "priority": m.get("priority", ""), "phase": phase,
            "phase_index": status.PHASES.index(phase) + 1 if phase in status.PHASES else None,
            "owner": text(m.get("owner")), "team": text(m.get("team")), "size": text(m.get("size")),
            "archived": bool(m.get("archived")),
            "target": text(m.get("target_release")),
            "problem": text(m.get("problem")),
            "ready": "n/a" if phase in ("done", "parked") else ("Ready" if not gate else "Not ready"),
            "gate_gaps": "; ".join(gate), "blockers": "; ".join(m.get("blockers") or []),
            "blocker_count": len(m.get("blockers") or []),
            "artifacts_approved": sum(1 for a in arts.values() if a.get("status") in ("approved", "synthesized")),
            "artifacts_total": len(arts),
            "requirements": len(reqs), "p0_requirements": sum(1 for r in reqs if r.get("priority") == "P0"),
            "open_hypotheses": sum(1 for h in hyps if h.get("verdict") in (None, "open")),
            "manifest_errors": "; ".join(errors),
            # For the interactive hub: data-file gaps (not editable on the page) apart from artifact-status gaps
            "gate_data": data_gaps, "next_phase": nxt, "blockers_list": [text(b) for b in m.get("blockers") or []],
        })
        for key, a in arts.items():
            loc = a.get("path") if a.get("form") in ("repo-md", "data") else a.get("link")
            rows["artifacts"].append({
                "slug": slug, "key": key, "artifact": ARTIFACT_LABELS.get(key, key), "form": text(a.get("form")),
                "status": text(a.get("status")), "owner": text(a.get("owner")), "location": text(loc),
            })
        for r in reqs:
            rows["requirements"].append({
                "slug": slug, "id": r.get("id"), "title": text(r.get("title")), "priority": text(r.get("priority")),
                "status": text(r.get("status")), "evidence": len(r.get("evidence") or []),
            })
        # Cited library entries, from feedback.yaml evidence and requirement evidence, merged per entry
        cited = {}
        for ev in fb.get("evidence") or []:
            if isinstance(ev, dict) and ev.get("id"):
                c = cited.setdefault(ev["id"], {"hypotheses": set(), "requirements": set(), "note": ""})
                c["hypotheses"].update(ev.get("hypotheses") or [])
                c["requirements"].update(ev.get("requirements") or [])
                c["note"] = c["note"] or text(ev.get("note"))
        for r in reqs:
            for fid in r.get("evidence") or []:
                cited.setdefault(fid, {"hypotheses": set(), "requirements": set(), "note": ""})["requirements"].add(r.get("id"))
        for fid, c in sorted(cited.items()):
            rows["evidence"].append({"slug": slug, "id": fid, "hypotheses": ", ".join(sorted(c["hypotheses"])),
                                     "requirements": ", ".join(sorted(c["requirements"])), "note": c["note"]})
        for h in hyps:
            rows["hypotheses"].append({"slug": slug, "id": h.get("id"), "statement": text(h.get("statement")),
                                       "verdict": text(h.get("verdict") or "open")})
        for x in status.load(f / "metrics.yaml").get("metrics") or []:
            rows["metrics"].append({
                "slug": slug, "name": text(x.get("name")), "type": text(x.get("type")), "target": text(x.get("target")),
                "method": text(x.get("method")), "review_date": text(x.get("review_date")), "verdict": text(x.get("verdict")),
            })
        for at in m.get("attachments") or []:
            rows["attachments"].append({
                "slug": slug, "id": text(at.get("id")), "phase": text(at.get("phase")), "title": text(at.get("title")),
                "kind": text(at.get("kind")), "link": text(at.get("link")), "filename": text(at.get("filename")),
                "asset": text(at.get("asset")), "use_as": text(at.get("use_as")), "note": text(at.get("note")),
                "added": text(at.get("added")), "read": bool(at.get("read")), "summary": text(at.get("summary")),
                "source": text(at.get("source")), "repo_link": text(at.get("repo_link")),
                "source_link": f"https://github.com/garingardiner/product-hub/blob/main/initiatives/{slug}/{at['source']}"
                               if at.get("source") else "",
            })
        for d in m.get("decisions") or []:
            rows["decisions"].append({"slug": slug, "date": text(d.get("date")), "decision": text(d.get("decision")),
                                      "by": text(d.get("by"))})
    if not rows["evidence"]:
        # The hub page treats a file with no rows as a failed load; this row has no id and the page skips it
        rows["evidence"].append({"slug": "", "id": "", "hypotheses": "", "requirements": "",
                                 "note": "Placeholder: no initiative cites feedback yet"})
    (OUT / "db").mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for name, data in rows.items():
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        (OUT / "db" / f"{name}.json").write_text(json.dumps({"rows": data, "exported_at": now}, ensure_ascii=False),
                                                 encoding="utf-8")
        print(f"{name}.json: {len(data)} rows")

if __name__ == "__main__":
    main()
