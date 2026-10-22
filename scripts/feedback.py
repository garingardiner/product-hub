#!/usr/bin/env python3
"""Search the feedback library snapshot (feedback/library.json).

  python scripts/feedback.py search [words...] [--tag T]... [--type T] [--segment S] [--source S] [--initiative I] [--json]
  python scripts/feedback.py tags              # all tags with counts
  python scripts/feedback.py show F-261022-AB12
  python scripts/feedback.py check             # every cited ID in initiatives exists in the library
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "feedback" / "library.json"

def load():
    if not LIB.exists():
        sys.exit("feedback/library.json not found. Export it from the Feedback Board first.")
    return json.loads(LIB.read_text(encoding="utf-8")).get("entries", [])

def fmt(e):
    who = e.get('customer', '') + (f" / {e['contact']}" if e.get('contact') else "")
    lines = [f"{e['id']}  [{e.get('type','')}] {who} ({e.get('segment','')}, {e.get('source','')}, {e.get('date','')})"]
    if e.get("quote"):
        lines.append(f'  “{e["quote"]}”')
    if e.get("summary"):
        lines.append(f"  {e['summary']}")
    lines.append(f"  tags: {', '.join(e.get('tags', []))}" + (f"  initiative: {e['initiative']}" if e.get("initiative") else ""))
    return "\n".join(lines)

def search(a):
    out = []
    for e in load():
        if a.type and e.get("type") != a.type: continue
        if a.segment and e.get("segment") != a.segment: continue
        if a.source and e.get("source") != a.source: continue
        if a.initiative and e.get("initiative") != a.initiative: continue
        if any(t not in e.get("tags", []) for t in a.tag or []): continue
        hay = " ".join(str(e.get(k, "")) for k in ("id", "quote", "summary", "customer", "contact", "segment", "initiative")).lower() + " " + " ".join(e.get("tags", []))
        if any(w.lower() not in hay for w in a.words): continue
        out.append(e)
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print("\n\n".join(fmt(e) for e in out) or "No matches.")
        print(f"\n{len(out)} match(es)", file=sys.stderr)

def check():
    ids = {e["id"] for e in load()}
    missing = []
    for f in (ROOT / "initiatives").glob("*/*.yaml"):
        if f.parent.name.startswith("_"): continue
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        cited = [x["id"] for x in data.get("evidence", []) if isinstance(x, dict) and "id" in x]
        cited += [i for r in data.get("requirements", []) for i in r.get("evidence", [])]
        missing += [(f.relative_to(ROOT), i) for i in cited if i not in ids]
    for path, i in missing:
        print(f"MISSING {i} cited in {path}")
    print("All cited feedback IDs found." if not missing else f"{len(missing)} cited ID(s) not in library.json (re-export?)")
    sys.exit(1 if missing else 0)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("words", nargs="*")
    for opt in ("type", "segment", "source", "initiative"): s.add_argument(f"--{opt}")
    s.add_argument("--tag", action="append"); s.add_argument("--json", action="store_true")
    sub.add_parser("tags")
    sh = sub.add_parser("show"); sh.add_argument("id")
    sub.add_parser("check")
    a = p.parse_args()
    if a.cmd == "search": search(a)
    elif a.cmd == "tags":
        for t, n in Counter(t for e in load() for t in e.get("tags", [])).most_common(): print(f"{n:4}  {t}")
    elif a.cmd == "show":
        e = next((e for e in load() if e["id"] == a.id), None)
        print(fmt(e) if e else f"{a.id} not found")
    elif a.cmd == "check": check()

if __name__ == "__main__":
    main()
