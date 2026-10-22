#!/usr/bin/env python3
"""Export initiative manifests and data files as JSON rows for the Product Hub page.

Usage: python scripts/export_hub.py   (requires: pip install pyyaml)
Writes build/hub/*.json; attach each file to the hub's matching source.
Skips _template and any folder with "example" in its slug.
"""
import json
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
    rows = {k: [] for k in ("initiatives", "artifacts", "requirements", "hypotheses", "metrics", "decisions")}
    folders = sorted(p for p in (ROOT / "initiatives").iterdir()
                     if p.is_dir() and not p.name.startswith("_") and "example" not in p.name)
    for f in folders:
        m, errors, gate = status.check(f)
        slug, phase = m.get("slug", f.name), m.get("phase")
        arts = m.get("artifacts") or {}
        reqs = status.load(f / "requirements.yaml").get("requirements") or []
        fb = status.load(f / "feedback.yaml")
        hyps = fb.get("hypotheses") or []
        rows["initiatives"].append({
            "slug": slug, "name": m.get("name", slug), "priority": m.get("priority", ""), "phase": phase,
            "phase_index": status.PHASES.index(phase) + 1 if phase in status.PHASES else None,
            "owner": text(m.get("owner")), "team": text(m.get("team")), "target": text(m.get("target_release")),
            "problem": text(m.get("problem")),
            "ready": "n/a" if phase in ("done", "parked") else ("Ready" if not gate else "Not ready"),
            "gate_gaps": "; ".join(gate), "blockers": "; ".join(m.get("blockers") or []),
            "blocker_count": len(m.get("blockers") or []),
            "artifacts_approved": sum(1 for a in arts.values() if a.get("status") in ("approved", "synthesized")),
            "artifacts_total": len(arts),
            "requirements": len(reqs), "p0_requirements": sum(1 for r in reqs if r.get("priority") == "P0"),
            "open_hypotheses": sum(1 for h in hyps if h.get("verdict") in (None, "open")),
            "manifest_errors": "; ".join(errors),
        })
        for key, a in arts.items():
            loc = a.get("path") if a.get("form") in ("repo-md", "data") else a.get("link")
            rows["artifacts"].append({
                "slug": slug, "artifact": ARTIFACT_LABELS.get(key, key), "form": text(a.get("form")),
                "status": text(a.get("status")), "owner": text(a.get("owner")), "location": text(loc),
            })
        for r in reqs:
            rows["requirements"].append({
                "slug": slug, "id": r.get("id"), "title": text(r.get("title")), "priority": text(r.get("priority")),
                "status": text(r.get("status")), "evidence": len(r.get("evidence") or []),
            })
        for h in hyps:
            rows["hypotheses"].append({"slug": slug, "id": h.get("id"), "statement": text(h.get("statement")),
                                       "verdict": text(h.get("verdict") or "open")})
        for x in status.load(f / "metrics.yaml").get("metrics") or []:
            rows["metrics"].append({
                "slug": slug, "name": text(x.get("name")), "type": text(x.get("type")), "target": text(x.get("target")),
                "method": text(x.get("method")), "review_date": text(x.get("review_date")), "verdict": text(x.get("verdict")),
            })
        for d in m.get("decisions") or []:
            rows["decisions"].append({"slug": slug, "date": text(d.get("date")), "decision": text(d.get("decision")),
                                      "by": text(d.get("by"))})
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in rows.items():
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{name}.json: {len(data)} rows")

if __name__ == "__main__":
    main()
