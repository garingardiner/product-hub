#!/usr/bin/env python3
"""Specs filled in on the Product Hub's forms: write them to the repo and render their docs.

Project spec: sections go to spec.yaml, requirements to requirements.yaml (merged by ID), project-spec.md is generated.
UX spec: ux-spec.yaml (design links, flows mapped to requirement IDs, states, accessibility, questions), ux-spec.md.
Engineering scope: scope.yaml (the artifact itself; items merged by ID), engineering-scope.md.
Feature/Benefits: feature-benefits.yaml (features mapped to requirement IDs, segments, proof points by feedback ID),
feature-benefits.md (quotes pulled from feedback/library.json).
The YAML is the source of truth; edit the form (or the YAML), never the generated docs.

Usage: python scripts/spec_doc.py <slug>    re-renders the initiative's docs from the YAML
"""
import re, sys
from io import StringIO
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
import status

ROOT = status.ROOT
DOC = "project-spec.md"
UX_DOC = "ux-spec.md"
UX_DATA = "ux-spec.yaml"
STATE_KINDS = ("empty", "loading", "error", "edge")
REPO_BLOB = "https://github.com/garingardiner/product-hub/blob/main/initiatives"
REQ_ID = re.compile(r"^R-\d{3,}$")
FB_ID = re.compile(r"^F-\d{6}-[A-Z0-9]{4}$")
PRIORITIES = ("P0", "P1", "P2")
HEADER = ("# Project spec sections, filled in on the Product Hub's form. Requirements live in requirements.yaml.\n"
          "# project-spec.md is generated from both by scripts/spec_doc.py; edit this file or the form, not the doc.\n")

def _yaml():
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    return y

def _t(v, n=4000):
    return re.sub(r"[\x00-\x08\x0b-\x1f]", "", str(v or "")).strip()[:n]

def _ids(v):
    return list(dict.fromkeys(x for x in (str(i).strip() for i in (v or [])) if FB_ID.match(x)))

def clean(spec):
    """Validate the form's payload into plain data (sections and requirements apart)."""
    s = spec or {}
    sup = s.get("support") or {}
    sections = {
        "problem": _t(s.get("problem")),
        "evidence": _ids(s.get("evidence")),
        "goals": [{"goal": _t(g.get("goal"), 500), "why": _t(g.get("why"), 500)} for g in s.get("goals") or [] if _t(g.get("goal"))],
        "non_goals": [{"item": _t(g.get("item"), 500), "why": _t(g.get("why"), 500)} for g in s.get("non_goals") or [] if _t(g.get("item"))],
        "stories": [{"persona": _t(x.get("persona"), 200), "want": _t(x.get("want"), 500), "so_that": _t(x.get("so_that"), 500)}
                    for x in s.get("stories") or [] if _t(x.get("want"))],
        "open_questions": [{"question": _t(q.get("question"), 500), "owner": _t(q.get("owner"), 100), "blocking": bool(q.get("blocking"))}
                           for q in s.get("open_questions") or [] if _t(q.get("question"))],
        "no_open_questions": bool(s.get("no_open_questions")),
        "support": {k: _t(sup.get(k), 2000) for k in ("docs", "edge_cases", "tickets")},
    }
    reqs, bad = [], []
    for r in s.get("requirements") or []:
        rid = _t(r.get("id"), 20)
        if not REQ_ID.match(rid):
            bad.append(rid or "(no id)")
            continue
        reqs.append({
            "id": rid, "title": _t(r.get("title"), 300), "description": _t(r.get("description")),
            "priority": r.get("priority") if r.get("priority") in PRIORITIES else "P1",
            "dropped": r.get("status") == "dropped",
            "acceptance_criteria": [_t(c, 500) for c in r.get("acceptance_criteria") or [] if _t(c)],
            "evidence": _ids(r.get("evidence")),
        })
    return sections, reqs, bad

def _flow_list(items):
    seq = CommentedSeq(items)
    seq.fa.set_flow_style()
    return seq

def write(folder, spec, msgs, slug):
    """Write the form's content; returns True when the doc was (re)generated."""
    sections, reqs, bad = clean(spec)
    if bad:
        msgs.append(f"{slug}: project spec requirements skipped (bad ID): {', '.join(bad)}")
    y = _yaml()
    out = StringIO()
    y.dump(sections, out)
    (folder / "spec.yaml").write_text(HEADER + out.getvalue(), encoding="utf-8", newline="\n")

    rpath = folder / "requirements.yaml"
    doc = y.load(rpath.read_text(encoding="utf-8")) if rpath.exists() else CommentedMap()
    if doc is None:
        doc = CommentedMap()
    if not isinstance(doc.get("requirements"), list) or not doc["requirements"]:
        doc["requirements"] = CommentedSeq()
    have = {r.get("id"): r for r in doc["requirements"]}
    added = updated = dropped = 0
    for r in reqs:
        cur = have.get(r["id"])
        if r["dropped"]:
            if cur is not None and cur.get("status") != "dropped":
                cur["status"] = "dropped"
                dropped += 1
            continue
        if not r["title"]:
            continue
        if cur is None:
            cur = CommentedMap(id=r["id"], title="", description="", priority="P1", status="draft",
                               acceptance_criteria=[], evidence=[])
            doc["requirements"].append(cur)
            have[r["id"]] = cur
            added += 1
        else:
            updated += 1
            if cur.get("status") == "dropped":
                cur["status"] = "draft"   # brought back on the form
        cur["title"], cur["description"], cur["priority"] = r["title"], r["description"], r["priority"]
        cur["acceptance_criteria"] = r["acceptance_criteria"]
        cur["evidence"] = _flow_list(r["evidence"])
    out = StringIO()
    y.dump(doc, out)
    rpath.write_text(out.getvalue(), encoding="utf-8", newline="\n")
    msgs.append(f"{slug}: project spec saved ({added} requirement(s) added, {updated} updated, {dropped} dropped)")
    render(folder)
    return True

def render(folder):
    m = status.load(folder / "initiative.yaml")
    s = status.load(folder / "spec.yaml")
    reqs = [r for r in status.load(folder / "requirements.yaml").get("requirements") or [] if r.get("status") != "dropped"]
    arts = m.get("artifacts") or {}
    L = [f"# Project spec: {m.get('name', folder.name)}", "",
         "_Generated from `spec.yaml` and `requirements.yaml` by `scripts/spec_doc.py`. Edit the form on the Product Hub, "
         "not this file._", ""]
    facts = [f"**Owner:** {m.get('owner') or '—'}", f"**Team:** {m.get('team') or '—'}",
             f"**Priority:** {m.get('priority') or '—'}", f"**Target:** {m.get('target_release') or '—'}",
             f"**Spec status:** {(arts.get('project_spec') or {}).get('status', '—')}"]
    L += [" · ".join(facts), ""]
    cite = lambda ids: f" ({', '.join(ids)})" if ids else ""
    L += ["## Problem", "", s.get("problem") or "_Not written yet._", ""]
    if s.get("evidence"):
        L += ["**Evidence:** " + ", ".join(s["evidence"]) + " (feedback library IDs; `python scripts/feedback.py show <ID>`)", ""]
    else:
        L += ["**Evidence:** none cited yet. Treat the problem as unconfirmed until feedback backs it.", ""]
    L += ["## Goals", ""] + ([f"- {g['goal']}" + (f": {g['why']}" if g.get("why") else "") for g in s.get("goals") or []] or ["_None yet._"]) + [""]
    L += ["## Non-goals", ""] + ([f"- {g['item']}" + (f": {g['why']}" if g.get("why") else "") for g in s.get("non_goals") or []] or ["_None yet._"]) + [""]
    L += ["## User stories", ""] + ([f"- As a {x.get('persona') or 'user'}, I want {x['want']}" + (f", so that {x['so_that']}" if x.get("so_that") else "") + "."
                                     for x in s.get("stories") or []] or ["_None yet._"]) + [""]
    L += ["## Requirements", "", "Source of truth: `requirements.yaml`.", ""]
    if reqs:
        for r in sorted(reqs, key=lambda r: (r.get("priority", "P9"), r.get("id"))):
            L += [f"### {r.get('id')} · {r.get('priority')} · {r.get('title')}", ""]
            if r.get("description"):
                L += [r["description"], ""]
            if r.get("acceptance_criteria"):
                L += ["Acceptance criteria:", ""] + [f"- {c}" for c in r["acceptance_criteria"]] + [""]
            L += [f"Status: {r.get('status')}" + cite(r.get("evidence") or []), ""]
    else:
        L += ["_None yet._", ""]
    ux = arts.get("ux_spec") or {}
    L += ["## Linked artifacts", "",
          f"- UX spec: {ux.get('link') or ('not needed' if ux.get('status') == 'n/a' else 'no link yet')}"
          + (f" (details: [{UX_DOC}]({UX_DOC}))" if (folder / UX_DOC).exists() else ""), ""]
    qs = s.get("open_questions") or []
    L += ["## Open questions", ""]
    if qs:
        L += [f"- {'**Blocking:** ' if q.get('blocking') else ''}{q['question']} (owner: {q.get('owner') or 'unassigned'})" for q in qs]
    else:
        L += ["_None right now._" if s.get("no_open_questions") else "_None listed yet._"]
    sup = s.get("support") or {}
    L += ["", "## Support considerations", "",
          f"- **Docs:** {sup.get('docs') or '—'}", f"- **Known edge cases:** {sup.get('edge_cases') or '—'}",
          f"- **Expected tickets:** {sup.get('tickets') or '—'}", ""]
    (folder / DOC).write_text("\n".join(L), encoding="utf-8", newline="\n")

# ---------- UX spec ----------
def _https(v):
    v = _t(v, 1000)
    return v if re.match(r"^https://\S+$", v) else ""

def _questions(s):
    return [{"question": _t(q.get("question"), 500), "owner": _t(q.get("owner"), 100), "blocking": bool(q.get("blocking"))}
            for q in s.get("open_questions") or [] if _t(q.get("question"))]

def clean_ux(spec):
    s = spec or {}
    a = s.get("a11y") or {}
    return {
        "designs": [{"title": _t(d.get("title"), 200) or "Design", "url": _https(d.get("url"))}
                    for d in s.get("designs") or [] if _https(d.get("url"))],
        "flows": [{"name": _t(f.get("name"), 200), "steps": _t(f.get("steps")), "link": _https(f.get("link")),
                   "requirements": list(dict.fromkeys(x for x in (str(i).strip() for i in f.get("requirements") or [])
                                                      if REQ_ID.match(x)))}
                  for f in s.get("flows") or [] if _t(f.get("name"))],
        "states": [{"kind": x.get("kind") if x.get("kind") in STATE_KINDS else "edge", "where": _t(x.get("where"), 200),
                    "description": _t(x.get("description"), 1000)} for x in s.get("states") or [] if _t(x.get("description"))],
        "a11y": {k: _t(a.get(k), 2000) for k in ("keyboard", "screen_reader", "visual")},
        "open_questions": _questions(s),
        "no_open_questions": bool(s.get("no_open_questions")),
    }

def write_ux(folder, spec, msgs, slug):
    ux = clean_ux(spec)
    out = StringIO()
    _yaml().dump(ux, out)
    (folder / UX_DATA).write_text("# UX spec, filled in on the Product Hub's form. ux-spec.md is generated from this by "
                                  "scripts/spec_doc.py; edit this file or the form, not the doc.\n" + out.getvalue(),
                                  encoding="utf-8", newline="\n")
    msgs.append(f"{slug}: UX spec saved ({len(ux['flows'])} flow(s), {len(ux['states'])} state(s), "
                f"{len(ux['designs'])} design link(s))")
    missing = uncovered_p0(folder)
    if missing:
        msgs.append(f"{slug}: P0 requirements not in any UX flow yet: {', '.join(missing)}")
    render_ux(folder)

def uncovered_p0(folder):
    """P0 requirements no UX flow covers ([] when there's no UX spec form yet)."""
    if not (folder / UX_DATA).exists():
        return []
    ux = status.load(folder / UX_DATA)
    covered = {r for f in ux.get("flows") or [] for r in f.get("requirements") or []}
    p0 = [r.get("id") for r in status.load(folder / "requirements.yaml").get("requirements") or []
          if r.get("priority") == "P0" and r.get("status") != "dropped"]
    return [r for r in p0 if r not in covered]

def render_ux(folder):
    m = status.load(folder / "initiative.yaml")
    u = status.load(folder / UX_DATA)
    reqs = {r.get("id"): r for r in status.load(folder / "requirements.yaml").get("requirements") or []}
    art = (m.get("artifacts") or {}).get("ux_spec") or {}
    L = [f"# UX spec: {m.get('name', folder.name)}", "",
         f"_Generated from `{UX_DATA}` by `scripts/spec_doc.py`. Edit the form on the Product Hub, not this file._", "",
         f"**Owner:** {art.get('owner') or m.get('owner') or '—'} · **Spec status:** {art.get('status', '—')} · "
         f"Project spec: [{DOC}]({DOC})", ""]
    L += ["## Design files", ""] + ([f"- [{d['title']}]({d['url']})" for d in u.get("designs") or []] or ["_None linked yet._"]) + [""]
    L += ["## Flows and screens", ""]
    for f in u.get("flows") or []:
        ids = f.get("requirements") or []
        L += [f"### {f['name']}", ""]
        if ids:
            L += ["Covers: " + ", ".join(f"{i} ({reqs[i].get('title')})" if i in reqs else i for i in ids), ""]
        if f.get("steps"):
            L += [f["steps"], ""]
        if f.get("link"):
            L += [f"Design: {f['link']}", ""]
    if not u.get("flows"):
        L += ["_None yet._", ""]
    missing = uncovered_p0(folder)
    L += ["**P0 coverage:** " + ("every P0 requirement is in a flow." if not missing
                                 else "not yet in any flow: " + ", ".join(missing)), ""]
    names = {"empty": "Empty", "loading": "Loading", "error": "Error", "edge": "Edge case"}
    L += ["## Empty, error and edge states", ""]
    L += [f"- **{names.get(x.get('kind'), 'Edge case')}**" + (f" ({x['where']})" if x.get("where") else "") + f": {x['description']}"
          for x in u.get("states") or []] or ["_None yet._"]
    a = u.get("a11y") or {}
    L += ["", "## Accessibility", "", f"- **Keyboard:** {a.get('keyboard') or '—'}",
          f"- **Screen readers:** {a.get('screen_reader') or '—'}",
          f"- **Visual (contrast, color, zoom):** {a.get('visual') or '—'}", ""]
    qs = u.get("open_questions") or []
    L += ["## Open design questions", ""]
    L += [f"- {'**Blocking:** ' if q.get('blocking') else ''}{q['question']} (owner: {q.get('owner') or 'unassigned'})"
          for q in qs] or ["_None right now._" if u.get("no_open_questions") else "_None listed yet._"]
    (folder / UX_DOC).write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")

# ---------- Engineering scope ----------
# scope.yaml is the artifact itself (form `data`); the form writes it and engineering-scope.md is generated from it.
SCOPE_DOC = "engineering-scope.md"
SCOPE_DATA = "scope.yaml"
SCOPE_ID = re.compile(r"^S-\d{2,}$")
SCOPE_STATUSES = ("planned", "in-progress", "done", "cut")

def _strs(v, n=500):
    return [x for x in (_t(i, n) for i in v or []) if x]

def clean_scope(spec):
    s = spec or {}
    qa = s.get("qa") or {}
    items, bad = [], []
    for it in s.get("items") or []:
        sid = _t(it.get("id"), 20)
        if not SCOPE_ID.match(sid):
            bad.append(sid or "(no id)")
            continue
        if not _t(it.get("title")):
            continue
        items.append({"id": sid, "title": _t(it.get("title"), 300),
                      "requirements": list(dict.fromkeys(x for x in (str(i).strip() for i in it.get("requirements") or []) if REQ_ID.match(x))),
                      "estimate": _t(it.get("estimate"), 50), "asana_task": _https(it.get("asana_task")),
                      "status": it.get("status") if it.get("status") in SCOPE_STATUSES else "planned"})
    risks = []
    for r in s.get("risks") or []:
        r = r if isinstance(r, dict) else {"risk": r}
        if _t(r.get("risk")):
            risks.append({"risk": _t(r.get("risk"), 500), "mitigation": _t(r.get("mitigation"), 500)})
    return {"release": _t(s.get("release"), 100), "items": items, "out_of_scope": _strs(s.get("out_of_scope")),
            "dependencies": _strs(s.get("dependencies")), "risks": risks,
            "qa": {"owner": _t(qa.get("owner"), 100), "approach": _t(qa.get("approach")),
                   "automated": _t(qa.get("automated")), "manual": _t(qa.get("manual"))},
            "support_readiness": _t(s.get("support_readiness"))}, bad

def write_scope(folder, spec, msgs, slug):
    new, bad = clean_scope(spec)
    if bad:
        msgs.append(f"{slug}: scope items skipped (bad ID): {', '.join(bad)}")
    y = _yaml()
    path = folder / SCOPE_DATA
    doc = (y.load(path.read_text(encoding="utf-8")) if path.exists() else None) or CommentedMap()
    # Merge items by ID so fields the form doesn't show (added by hand or by the Asana sync) survive
    old = {i.get("id"): i for i in doc.get("items") or [] if isinstance(i, dict)}
    items = CommentedSeq()
    for it in new["items"]:
        cur = old.get(it["id"], CommentedMap())
        for k, v in it.items():
            cur[k] = _flow_list(v) if k == "requirements" else v
        items.append(cur)
    kept_cut = [i for sid, i in old.items() if sid not in {x["id"] for x in new["items"]} and i.get("status") == "cut"]
    items.extend(kept_cut)
    doc["release"] = new["release"]
    doc["items"] = items
    for k in ("out_of_scope", "dependencies", "risks", "support_readiness"):
        doc[k] = new[k]
    qa = doc.get("qa") if isinstance(doc.get("qa"), dict) else CommentedMap()
    qa.update(new["qa"])
    doc["qa"] = qa
    out = StringIO()
    y.dump(doc, out)
    path.write_text(out.getvalue(), encoding="utf-8", newline="\n")
    live = [i for i in new["items"] if i["status"] != "cut"]
    msgs.append(f"{slug}: engineering scope saved ({len(live)} item(s) in scope, "
                f"{len(new['items']) - len(live) + len(kept_cut)} cut)")
    render_scope(folder)

def render_scope(folder):
    m = status.load(folder / "initiative.yaml")
    s = status.load(folder / SCOPE_DATA)
    reqs = {r.get("id"): r for r in status.load(folder / "requirements.yaml").get("requirements") or []}
    art = (m.get("artifacts") or {}).get("engineering_scope") or {}
    items = s.get("items") or []
    inputs = [f"[{d}]({d})" for d in (DOC, UX_DOC) if (folder / d).exists()] + ["`requirements.yaml`"]
    L = [f"# Engineering scope: {m.get('name', folder.name)}", "",
         f"_Generated from `{SCOPE_DATA}` by `scripts/spec_doc.py`. Edit the form on the Product Hub, not this file._", "",
         f"**Release:** {s.get('release') or '—'} · **Scope status:** {art.get('status', '—')} · Inputs: {', '.join(inputs)}", ""]
    L += ["## In scope", ""]
    live = [i for i in items if i.get("status") != "cut"]
    if live:
        L += ["| ID | Item | Requirements | Estimate | Status | Asana |", "|---|---|---|---|---|---|"]
        for i in live:
            asana = f"[task]({i['asana_task']})" if i.get("asana_task") else "—"
            L.append(f"| {i.get('id')} | {i.get('title')} | {', '.join(i.get('requirements') or []) or '—'} | "
                     f"{i.get('estimate') or '—'} | {i.get('status') or 'planned'} | {asana} |")
    else:
        L += ["_None yet._"]
    covered = {r for i in live for r in i.get("requirements") or []}
    p0 = [rid for rid, r in reqs.items() if r.get("priority") == "P0" and r.get("status") != "dropped"]
    miss = [r for r in p0 if r not in covered]
    L += ["", "**P0 coverage:** " + ("every P0 requirement is in scope." if not miss else "not in scope yet: " + ", ".join(miss)), ""]
    cut = [i for i in items if i.get("status") == "cut"]
    L += ["## Out of scope for this release", ""] + [f"- {x}" for x in s.get("out_of_scope") or []] \
         + [f"- {i.get('id')} {i.get('title')} (cut)" for i in cut]
    if not (s.get("out_of_scope") or cut):
        L += ["_Nothing listed._"]
    L += ["", "## Dependencies", ""] + ([f"- {d}" for d in s.get("dependencies") or []] or ["_None listed._"])
    L += ["", "## Risks", ""]
    for r in s.get("risks") or []:
        r = r if isinstance(r, dict) else {"risk": r}
        L.append(f"- {r.get('risk')}" + (f" (mitigation: {r['mitigation']})" if r.get("mitigation") else ""))
    if not s.get("risks"):
        L += ["_None listed._"]
    qa = s.get("qa") or {}
    L += ["", "## QA approach", "", f"- **Test plan owner:** {qa.get('owner') or '—'}",
          f"- **Approach:** {qa.get('approach') or '—'}", f"- **Automated:** {qa.get('automated') or '—'}",
          f"- **Manual:** {qa.get('manual') or '—'}", "", "Acceptance criteria to cover:", ""]
    ac = [(rid, c) for rid in sorted(covered) for c in (reqs.get(rid) or {}).get("acceptance_criteria") or []]
    L += [f"- {rid}: {c}" for rid, c in ac] or ["_No acceptance criteria on the in-scope requirements yet._"]
    L += ["", "## Support readiness", "", s.get("support_readiness") or "—", ""]
    (folder / SCOPE_DOC).write_text("\n".join(L), encoding="utf-8", newline="\n")

# ---------- Feature/Benefits ----------
FB_DOC = "feature-benefits.md"
FB_DATA = "feature-benefits.yaml"

def clean_fb(spec):
    s = spec or {}
    av = s.get("availability") or {}
    rids = lambda v: list(dict.fromkeys(x for x in (str(i).strip() for i in v or []) if REQ_ID.match(x)))
    return {
        "features": [{"feature": _t(f.get("feature"), 300), "benefit": _t(f.get("benefit"), 1000), "requirements": rids(f.get("requirements"))}
                     for f in s.get("features") or [] if _t(f.get("feature"))],
        "segments": [{"segment": _t(x.get("segment"), 60), "problem": _t(x.get("problem"), 1000)}
                     for x in s.get("segments") or [] if _t(x.get("segment"))],
        "proof_points": [{"id": _t(p.get("id"), 20), "note": _t(p.get("note"), 500)}
                         for p in s.get("proof_points") or [] if FB_ID.match(_t(p.get("id"), 20))],
        "does_not": _strs(s.get("does_not")),
        "availability": {k: _t(av.get(k), 1000) for k in ("release", "plans", "limitations")},
    }

def write_fb(folder, spec, msgs, slug):
    fb = clean_fb(spec)
    out = StringIO()
    _yaml().dump(fb, out)
    (folder / FB_DATA).write_text("# Feature/Benefits, filled in on the Product Hub's form. feature-benefits.md is generated "
                                  "from this by scripts/spec_doc.py; edit this file or the form, not the doc.\n" + out.getvalue(),
                                  encoding="utf-8", newline="\n")
    msgs.append(f"{slug}: Feature/Benefits saved ({len(fb['features'])} feature(s), {len(fb['proof_points'])} proof point(s))")
    bad = unshipped_claims(folder)
    if bad:
        msgs.append(f"{slug}: Feature/Benefits claims requirements that aren't in scope: {', '.join(bad)}")
    render_fb(folder)

def in_scope_reqs(folder):
    """Requirement IDs delivered by scope items that aren't cut."""
    return {r for i in status.load(folder / SCOPE_DATA).get("items") or [] if i.get("status") != "cut"
            for r in i.get("requirements") or []}

def unshipped_claims(folder):
    if not (folder / FB_DATA).exists():
        return []
    ok = in_scope_reqs(folder)
    return sorted({r for f in status.load(folder / FB_DATA).get("features") or [] for r in f.get("requirements") or []} - ok)

def render_fb(folder):
    import json
    m = status.load(folder / "initiative.yaml")
    s = status.load(folder / FB_DATA)
    reqs = {r.get("id"): r for r in status.load(folder / "requirements.yaml").get("requirements") or []}
    lib_path = ROOT / "feedback" / "library.json"
    lib = {e.get("id"): e for e in (json.loads(lib_path.read_text(encoding="utf-8")).get("entries") or [])} if lib_path.exists() else {}
    art = (m.get("artifacts") or {}).get("feature_benefits") or {}
    L = [f"# Feature/Benefits: {m.get('name', folder.name)}", "",
         f"_Generated from `{FB_DATA}` by `scripts/spec_doc.py`. Edit the form on the Product Hub, not this file. "
         "Every claim must map to a shipped requirement; quotes come only from the feedback library._", "",
         f"**Status:** {art.get('status', '—')} · **Owner:** {art.get('owner') or m.get('owner') or '—'}", ""]
    L += ["## Features and benefits", ""]
    for f in s.get("features") or []:
        ids = f.get("requirements") or []
        L += [f"### {f['feature']}", "", f.get("benefit") or "_Benefit not written yet._", ""]
        if ids:
            L += ["Delivers: " + ", ".join(f"{i} ({reqs[i].get('title')})" if i in reqs else i for i in ids), ""]
    if not s.get("features"):
        L += ["_None yet._", ""]
    bad = unshipped_claims(folder)
    if bad:
        L += [f"**Check before sharing:** {', '.join(bad)} {'is' if len(bad) == 1 else 'are'} not in the engineering scope.", ""]
    L += ["## Target segments", ""] + ([f"- **{x['segment'].title()}:** {x.get('problem') or '—'}" for x in s.get("segments") or []] or ["_None yet._"])
    L += ["", "## Proof points", ""]
    for p in s.get("proof_points") or []:
        e = lib.get(p["id"]) or {}
        said = f"“{e['quote']}”" if e.get("quote") else (e.get("summary") or "_Entry not found in the synced library._")
        who = ", ".join(x for x in (e.get("contact"), e.get("customer")) if x)
        L.append(f"- {said}" + (f" ({who})" if who else "") + f" [{p['id']}]" + (f": {p['note']}" if p.get("note") else ""))
    if not s.get("proof_points"):
        L += ["_None yet. Use only quotes and data from the feedback library._"]
    L += ["", "## What it does not do", ""] + ([f"- {x}" for x in s.get("does_not") or []] or ["_Not listed yet._"])
    av = s.get("availability") or {}
    L += ["", "## Availability", "", f"- **Release:** {av.get('release') or '—'}", f"- **Plans / tiers:** {av.get('plans') or '—'}",
          f"- **Limitations:** {av.get('limitations') or '—'}", ""]
    (folder / FB_DOC).write_text("\n".join(L), encoding="utf-8", newline="\n")

def render_all(folder):
    if (folder / "spec.yaml").exists():
        render(folder)
    if (folder / UX_DATA).exists():
        render_ux(folder)
    if (folder / SCOPE_DOC).exists():
        render_scope(folder)   # only once the scope form has been used
    if (folder / FB_DATA).exists():
        render_fb(folder)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    render_all(ROOT / "initiatives" / sys.argv[1])
    print(f"{sys.argv[1]}: docs rendered")
