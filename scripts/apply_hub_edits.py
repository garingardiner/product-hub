#!/usr/bin/env python3
"""Apply edits made on the Product Hub page to initiative manifests ("sync hub").

Usage: python scripts/apply_hub_edits.py <dir> [--skip-deletes]    (requires: pip install pyyaml ruamel.yaml)
--skip-deletes leaves delete requests pending (for the unattended scheduled sync) and lists them in applied.json.
<dir> holds the hub's `edits` documents as saved by ArtifactData `list` with `out_dir`
(<dir>/edits/<slug>.json, each {"id", "version", "data": {create, patch, artifacts, decisions_add,
attachments_add, attachments_remove}}).

- `create` makes initiatives/<slug>/ from the template with the given basics.
- Edits are validated and written to initiative.yaml with comments kept.
- Any phase can be chosen; a forward move records the gate items still open at the time in its decision.
- Attachments are recorded under `attachments:`; a link used as an artifact becomes that artifact's link.
- `patch.archived` archives or restores (logged as a decision); `delete` removes the initiative's folder.
Writes <dir>/applied.json: {"applied": [{id, version}], "to_read": [attachments Claude still has to read]}.
"""
import json, re, shutil, sys
from datetime import date
from io import StringIO
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import status

ROOT = status.ROOT
FIELDS = {"name", "problem", "priority", "owner", "team", "size", "target_release"}
PRIORITIES = {"P0", "P1", "P2"}
TEAMS = {"", "Build", "Analyze", "Orchestrate"}   # keep in sync with TEAMS in pages/product-hub.html
OWNERS = {"", "Tristan Antonsen", "Bryce Mazurowski", "Patrick Ogdin"}   # keep in sync with OWNERS there
SIZES = {"", "Small", "Medium", "Large"}   # keep in sync with SIZES there
SLUG = re.compile(r"^\d{4}-q[1-4]-[a-z0-9][a-z0-9-]{1,60}$")

def flow(d):
    m = CommentedMap(d)
    m.fa.set_flow_style()
    return m

def dump(yaml, doc):
    s = StringIO()
    yaml.dump(doc, s)
    return s.getvalue()

def form_for(url):
    u = url.lower()
    if "figma.com" in u: return "figma"
    if "docs.google.com" in u or "drive.google.com" in u: return "drive"
    if "claude.ai/artifact" in u: return "claude-artifact"
    if "asana.com" in u: return "asana"
    return "other"

def create(slug, basics, msgs):
    folder = ROOT / "initiatives" / slug
    if folder.exists():
        msgs.append(f"{slug}: already exists, create skipped (other edits still applied)")
        return
    if not SLUG.match(slug):
        msgs.append(f"{slug}: not a valid slug (yyyy-qn-short-name), not created")
        return
    shutil.copytree(ROOT / "initiatives" / "_template", folder)
    msgs.append(f"{slug}: created from template")

def apply_one(slug, data, yaml):
    msgs, to_read = [], []
    if data.get("delete"):
        folder = ROOT / "initiatives" / slug
        if not SLUG.match(slug) or not (folder / "initiative.yaml").exists():
            return False, [f"{slug}: nothing to delete"], []
        shutil.rmtree(folder)
        return True, [f"{slug}: deleted (folder removed; recoverable from Git history)"], []
    if data.get("create"):
        create(slug, data["create"], msgs)
    path = ROOT / "initiatives" / slug / "initiative.yaml"
    if not path.exists():
        return False, msgs + [f"{slug}: no such initiative, skipped"], []
    doc = yaml.load(path.read_text(encoding="utf-8"))
    if data.get("create") and not doc.get("slug"):
        doc["slug"] = slug
    patch = {**(data.get("create") or {}), **(data.get("patch") or {})}
    for k, v in patch.items():
        if k in FIELDS:
            v = str(v).strip()
            if k == "priority" and v not in PRIORITIES:
                msgs.append(f"{slug}: priority '{v}' not allowed, kept {doc.get('priority')}")
                continue
            if k == "owner" and v not in OWNERS:
                msgs.append(f"{slug}: owner '{v}' not on the owner list; kept {doc.get('owner')}")
                continue
            if k == "target_release" and v and not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
                msgs.append(f"{slug}: target '{v}' isn't a month (YYYY-MM); kept {doc.get('target_release')}")
                continue
            if k == "size" and v not in SIZES:
                msgs.append(f"{slug}: size '{v}' not one of Small, Medium, Large; kept {doc.get('size')}")
                continue
            if k == "team" and v not in TEAMS:
                msgs.append(f"{slug}: team '{v}' not one of Build, Analyze, Orchestrate; kept {doc.get('team')}")
                continue
            if k == "name" and not v:
                msgs.append(f"{slug}: empty name ignored")
                continue
            doc[k] = v
        elif k == "blockers":
            doc["blockers"] = [str(b).strip() for b in v if str(b).strip()]
        elif k == "skip_phases":
            new = [p for p in status.PHASES[:5] if p in (v or [])]
            old = list(doc.get("skip_phases") or [])
            if new != old:
                if new:
                    doc["skip_phases"] = new
                else:
                    doc.pop("skip_phases", None)
                added, back = [p for p in new if p not in old], [p for p in old if p not in new]
                note = "; ".join(filter(None, [f"Marked {', '.join(added)} not needed" if added else "",
                                               f"{', '.join(back)} needed again" if back else ""]))
                doc.setdefault("decisions", []).append(flow({
                    "date": date.today().isoformat(), "decision": note, "by": "Product Hub page"}))
                msgs.append(f"{slug}: {note}")
        elif k == "archived" and bool(v) != bool(doc.get("archived")):
            if v:
                doc["archived"] = True
            else:
                doc.pop("archived", None)
            doc.setdefault("decisions", []).append(flow({
                "date": date.today().isoformat(), "decision": "Archived" if v else "Restored from archive",
                "by": "Product Hub page"}))
            msgs.append(f"{slug}: {'archived' if v else 'restored'}")
    arts = doc.get("artifacts") or {}
    for key, ch in (data.get("artifacts") or {}).items():
        a = arts.get(key)
        if a is None:
            msgs.append(f"{slug}: unknown artifact '{key}', skipped")
            continue
        if "owner" in ch:
            a["owner"] = str(ch["owner"]).strip()
        if "link" in ch:
            # Repo-file artifacts keep their path and gain an optional link (e.g. an Asana project for the scope)
            a["link"] = str(ch["link"]).strip()
        if "status" in ch:
            st = ch["status"]
            loc = a.get("path") if a.get("form") in ("repo-md", "data") else a.get("link")
            if st not in status.STATUSES:
                msgs.append(f"{slug}: {key} status '{st}' not allowed")
            elif st not in status.NOT_STARTED and not loc:
                # status.py treats a started artifact with no document as an error; keep the manifest valid
                msgs.append(f"{slug}: {key} not set to {st}: it has no link yet. Add the document's link "
                            f"(or mark its phase not needed) and set the status again")
            else:
                a["status"] = st
    for d in data.get("decisions_add") or []:
        text = str(d.get("decision", "")).strip()
        if text:
            doc.setdefault("decisions", []).append(flow({
                "date": str(d.get("date") or date.today().isoformat()), "decision": text,
                "by": str(d.get("by") or "Product Hub page").strip()}))

    # Attachments: links and uploaded files per phase
    gone = set(data.get("attachments_remove") or [])
    if gone and doc.get("attachments"):
        keep = [x for x in doc["attachments"] if x.get("id") not in gone]
        msgs.append(f"{slug}: removed {len(doc['attachments']) - len(keep)} attachment(s)")
        doc["attachments"] = keep
    for at in data.get("attachments_add") or []:
        aid, phase, kind = str(at.get("id", "")), at.get("phase"), at.get("kind")
        if not aid or phase not in status.PHASES or kind not in ("link", "file"):
            msgs.append(f"{slug}: attachment '{at.get('title')}' skipped (missing id, phase or kind)")
            continue
        if any(x.get("id") == aid for x in doc.get("attachments") or []):
            continue
        rec = {"id": aid, "phase": phase, "title": str(at.get("title") or "").strip() or aid, "kind": kind}
        if kind == "link":
            url = str(at.get("url") or "").strip()
            if not url.startswith("https://"):
                msgs.append(f"{slug}: attachment '{rec['title']}' skipped (link must start with https://)")
                continue
            rec["link"] = url
        else:
            rec["asset"] = str(at.get("asset_id") or "")
            rec["filename"] = str(at.get("filename") or "")
        use_as = at.get("use_as") or ""
        if use_as:
            rec["use_as"] = use_as
        if at.get("note"):
            rec["note"] = str(at["note"]).strip()
        rec.update({"added": str(at.get("added_at") or date.today().isoformat())[:10], "read": False})
        doc.setdefault("attachments", []).append(flow(rec))
        if kind == "link" and use_as in arts:
            a = arts[use_as]
            if a.get("form") in ("repo-md", "data"):
                a["link"] = rec["link"]          # keep the repo file; add the link beside it
            else:
                a["form"], a["link"] = form_for(rec["link"]), rec["link"]
                a.pop("path", None)
            if a.get("status") == "not-started":
                a["status"] = "draft"
            msgs.append(f"{slug}: {use_as} now links to {rec['title']}")
        to_read.append({"slug": slug, **rec, "asset_url": at.get("asset_url", "")})
    path.write_text(dump(yaml, doc), encoding="utf-8", newline="\n")

    target = patch.get("phase")
    if target and target != doc.get("phase"):
        cur = doc.get("phase")
        if target not in status.PHASES or cur not in status.PHASES:
            msgs.append(f"{slug}: phase '{target}' not allowed")
        else:
            # Gates are a checklist, not a lock: any phase can be chosen, and open items are logged with the move
            ti, ci = status.PHASES.index(target), status.PHASES.index(cur)
            if ti < ci:
                note = f"Phase moved back from {cur} to {target}"
            else:
                _, errors, gate = status.check(path.parent)
                skip = set(doc.get("skip_phases") or [])
                passed = [p for p in status.PHASES[ci + 1:ti] if p not in skip]
                note = f"Moved from {cur} to {target}"
                if passed:
                    note += f", passing over {', '.join(passed)}"
                note += f"; open at the time: {'; '.join(gate)}" if gate else "; gate passed"
            if target:
                doc["phase"] = target
                doc.setdefault("decisions", []).append(flow({
                    "date": date.today().isoformat(), "decision": note, "by": "Product Hub page"}))
                path.write_text(dump(yaml, doc), encoding="utf-8", newline="\n")
                msgs.append(f"{slug}: {note}")
    msgs.insert(0, f"{slug}: applied")
    return True, msgs, to_read

def main():
    args = [a for a in sys.argv[1:] if a != "--skip-deletes"]
    skip_deletes = "--skip-deletes" in sys.argv[1:]
    if len(args) != 1:
        sys.exit(__doc__)
    src = Path(args[0])
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    applied, to_read, held = [], [], []
    for p in sorted((src / "edits").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        # ArtifactData out_dir saves the bare document body; older test files wrapped it as {id, version, data}
        if not isinstance(d.get("data"), dict):
            d = {"id": p.stem, "version": None, "data": d}
        data = d.get("data") or {}
        if skip_deletes and data.get("delete"):
            held.append(d.get("id") or p.stem)
            print(f"{d.get('id') or p.stem}: delete held for confirmation in chat")
            continue
        ok, msgs, reads = apply_one(d.get("id") or p.stem, data, yaml)
        print("\n".join(msgs))
        if ok:
            applied.append({"id": d.get("id") or p.stem, "version": d.get("version")})
            to_read += reads
    (src / "applied.json").write_text(json.dumps({"applied": applied, "to_read": to_read, "held_deletes": held}, indent=1),
                                      encoding="utf-8")
    print(f"{len(applied)} edit document(s) applied; {len(to_read)} attachment(s) to read; {len(held)} delete(s) held")

if __name__ == "__main__":
    main()
