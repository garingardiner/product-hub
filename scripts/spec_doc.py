#!/usr/bin/env python3
"""Specs filled in on the Product Hub's forms: write them to the repo and render their docs.

Project spec: sections go to spec.yaml, requirements to requirements.yaml (merged by ID), project-spec.md is generated.
UX spec: ux-spec.yaml (design links, flows mapped to requirement IDs, states, accessibility, questions), ux-spec.md.
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

def render_all(folder):
    if (folder / "spec.yaml").exists():
        render(folder)
    if (folder / UX_DATA).exists():
        render_ux(folder)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    render_all(ROOT / "initiatives" / sys.argv[1])
    print(f"{sys.argv[1]}: docs rendered")
