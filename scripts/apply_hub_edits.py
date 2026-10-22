#!/usr/bin/env python3
"""Apply edits made on the Product Hub page to initiative manifests ("sync hub").

Usage: python scripts/apply_hub_edits.py <dir>    (requires: pip install pyyaml ruamel.yaml)
<dir> holds the hub's `edits` documents as saved by ArtifactData `list` with `out_dir`
(<dir>/edits/<slug>.json, each {"id", "version", "data": {patch, artifacts, decisions_add}}).
Edits are validated, written to initiatives/<slug>/initiative.yaml with comments kept, and phase moves
only forward one step when the gate passes (or backward). Writes <dir>/applied.json: the documents that
were applied, with the version to delete them at.
"""
import json, sys
from datetime import date
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import status

ROOT = status.ROOT
FIELDS = {"name", "problem", "priority", "owner", "team", "target_release"}
PRIORITIES = {"P0", "P1", "P2"}

def flow(d):
    m = CommentedMap(d)
    m.fa.set_flow_style()
    return m

def apply_one(slug, data, yaml):
    msgs, path = [], ROOT / "initiatives" / slug / "initiative.yaml"
    if not path.exists():
        return False, [f"{slug}: no such initiative, skipped"]
    doc = yaml.load(path.read_text(encoding="utf-8"))
    patch = data.get("patch") or {}
    for k, v in patch.items():
        if k in FIELDS:
            v = str(v).strip()
            if k == "priority" and v not in PRIORITIES:
                msgs.append(f"{slug}: priority '{v}' not allowed, kept {doc.get('priority')}")
                continue
            if k == "name" and not v:
                msgs.append(f"{slug}: empty name ignored")
                continue
            doc[k] = v
        elif k == "blockers":
            doc["blockers"] = [str(b).strip() for b in v if str(b).strip()]
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
    path.write_text(_dump(yaml, doc), encoding="utf-8", newline="\n")

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
                path.write_text(_dump(yaml, doc), encoding="utf-8", newline="\n")
                msgs.append(f"{slug}: {note}")
    msgs.insert(0, f"{slug}: applied")
    return True, msgs

def _dump(yaml, doc):
    from io import StringIO
    s = StringIO()
    yaml.dump(doc, s)
    return s.getvalue()

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    applied = []
    for p in sorted((src / "edits").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        ok, msgs = apply_one(d.get("id") or p.stem, d.get("data") or {}, yaml)
        print("\n".join(msgs))
        if ok:
            applied.append({"id": d.get("id") or p.stem, "version": d.get("version")})
    (src / "applied.json").write_text(json.dumps(applied, indent=1), encoding="utf-8")
    print(f"{len(applied)} edit document(s) applied")

if __name__ == "__main__":
    main()
