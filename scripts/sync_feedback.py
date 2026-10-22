#!/usr/bin/env python3
"""Rebuild feedback/library.json from Feedback Board documents saved by Claude.

Usage: python scripts/sync_feedback.py <dir>
<dir> holds the board's feedback documents as saved by ArtifactData `list` with `out_dir`
(<dir>/feedback/<ID>.json, each {"id", "data", ...}). Overwrites feedback/library.json.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "feedback" / "library.json"
FIELDS = ("quote", "summary", "type", "sentiment", "tags", "source", "customer", "contact", "segment",
          "date", "initiative", "requirements", "createdAt", "updatedAt")

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    docs = sorted((src / "feedback").glob("*.json")) if (src / "feedback").is_dir() else sorted(src.glob("*.json"))
    entries = []
    for p in docs:
        d = json.loads(p.read_text(encoding="utf-8"))
        data = d.get("data", d)
        # submittedBy is a board user id; the board's own export leaves it out too
        e = {"id": d.get("id") or p.stem, **{k: data[k] for k in FIELDS if k in data}}
        entries.append(e)
    entries.sort(key=lambda e: (e.get("date") or "", e.get("createdAt") or ""), reverse=True)
    out = {"exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "source": "Feedback Board (synced by Claude)", "count": len(entries), "entries": entries}
    LIB.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"feedback/library.json: {len(entries)} entries")

if __name__ == "__main__":
    main()
