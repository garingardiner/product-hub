#!/usr/bin/env python3
"""Record that Claude has read an initiative attachment ("sync hub", after reading links and files).

Usage: python scripts/record_source.py <slug> <attachment-id> --summary "One line" [--file <repo-relative path>]
Expects the extracted text already saved at initiatives/<slug>/sources/<attachment-id>.md.
Marks the attachment read, stores the summary and source path, and keeps the original upload's path if given.
An uploaded file marked "use as" an artifact makes that artifact point at the extracted text (repo-md).
"""
import argparse
from io import StringIO
from ruamel.yaml import YAML
import status

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("id")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--file", default="", help="where the original upload was saved, relative to the initiative folder")
    a = ap.parse_args()
    folder = status.ROOT / "initiatives" / a.slug
    src = f"sources/{a.id}.md"
    if not (folder / src).exists():
        raise SystemExit(f"{folder / src} not found; save the extracted text there first")
    yaml = YAML(); yaml.preserve_quotes = True; yaml.width = 4096
    path = folder / "initiative.yaml"
    doc = yaml.load(path.read_text(encoding="utf-8"))
    att = next((x for x in doc.get("attachments") or [] if x.get("id") == a.id), None)
    if att is None:
        raise SystemExit(f"{a.slug}: no attachment {a.id}")
    att["read"], att["source"], att["summary"] = True, src, a.summary.strip()
    if a.file:
        att["file"] = a.file
    use_as = att.get("use_as")
    if att.get("kind") == "file" and use_as in (doc.get("artifacts") or {}):
        art = doc["artifacts"][use_as]
        art["form"], art["path"] = "repo-md", src
        art.pop("link", None)
        if art.get("status") == "not-started":
            art["status"] = "draft"
        print(f"{a.slug}: {use_as} now points at {src}")
    s = StringIO(); yaml.dump(doc, s)
    path.write_text(s.getvalue(), encoding="utf-8", newline="\n")
    print(f"{a.slug}: {a.id} recorded as read")

if __name__ == "__main__":
    main()
