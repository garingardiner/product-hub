#!/usr/bin/env python3
"""Apply edits made on the Product Hub page to initiative manifests ("sync hub").

Usage: python scripts/apply_hub_edits.py <dir>    (requires: pip install pyyaml ruamel.yaml)
<dir> holds the hub's `edits` documents as saved by ArtifactData `list` with `out_dir`
(<dir>/edits/<slug>.json, each {"id", "version", "data": {create, patch, artifacts, decisions_add,
attachments_add, attachments_remove}}).

- `create` makes initiatives/<slug>/ from the template with the given basics.
- Edits are validated and written to initiative.yaml with comments kept.
- Phase moves only forward one step when the gate passes (or backward).
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
        if "status" in ch:
            if ch["status"] in status.STATUSES:
                a["status"] = ch["status"]
            else:
                msgs.append(f"{slug}: {key} status '{ch['status']}' not allowed")
        if "owner" in ch:
            a["owner"] = str(ch["owner"]).strip()
        if "link" in ch:
            a["path" if a.get("form") in ("repo-md", "data") else "link"] = str(ch["link"]).strip()
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
            ti, ci = status.PHASES.index(target), status.PHASES.index(cur)
            if ti < ci:
                note = f"Phase moved back from {cur} to {target}"
            elif ti == ci + 1:
                _, errors, gate = status.check(path.parent)
                if gate or errors:
                    msgs.append(f"{slug}: not moved to {target}; gate open: {'; '.join(gate + errors)}")
                    target = None
                note = f"Advanced from {cur} to {target} (gate passed)"
            else:
                msgs.append(f"{slug}: can't skip from {cur} to {target}")
                target = None
            if target:
                doc["phase"] = target
                doc.setdefault("decisions", []).append(flow({
                    "date": date.today().isoformat(), "decision": note, "by": "Product Hub page"}))
                path.write_text(dump(yaml, doc), encoding="utf-8", newline="\n")
                msgs.append(f"{slug}: {note}")
    msgs.insert(0, f"{slug}: applied")
    return True, msgs, to_read

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    applied, to_read = [], []
    for p in sorted((src / "edits").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        ok, msgs, reads = apply_one(d.get("id") or p.stem, d.get("data") or {}, yaml)
        print("\n".join(msgs))
        if ok:
            applied.append({"id": d.get("id") or p.stem, "version": d.get("version")})
            to_read += reads
    (src / "applied.json").write_text(json.dumps({"applied": applied, "to_read": to_read}, indent=1), encoding="utf-8")
    print(f"{len(applied)} edit document(s) applied; {len(to_read)} attachment(s) to read")

if __name__ == "__main__":
    main()
