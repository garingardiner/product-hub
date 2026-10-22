# Product Hub

Shared workspace for Product Management and adjacent teams to move initiatives through
**Discovery → Feedback → Spec → Engineering → GTM**, with Claude doing the drafting, synthesis, and tracking.

## How it's organized

- `CLAUDE.md` holds the workflow rules, phase gates, and conventions Claude follows. Start here.
- `contracts/` defines what each artifact must contain, independent of format.
- `initiatives/` has one folder per initiative, each with a manifest (`initiative.yaml`) plus structured data
  (requirements, feedback, metrics, scope). Docs, designs, and decks can live elsewhere; the manifest links to them.
- `feedback/library.json` is a snapshot of the shared Feedback Board (https://claude.ai/artifact/MVCedVjgWJ9WyywSWuRstp),
  searchable with `scripts/feedback.py`.
- `ROADMAP.md` is generated. Don't edit it by hand.
- `scripts/status.py` validates manifests, checks phase gates, and regenerates the roadmap.
- `.claude/commands/` has slash commands for Claude Code: `/new-initiative`, `/advance`, `/find-feedback`, `/link-feedback`, `/status`.

## Getting started

1. Push this folder to a new GitHub repo and open it with Claude Code.
2. `pip install pyyaml`, then run `python scripts/status.py`.
3. Run `/new-initiative <name and one-line problem>` for a real initiative you're working on.
4. Work through it, and edit `contracts/` and `CLAUDE.md` whenever something feels wrong. That's the point of the pilot.
5. Delete `initiatives/2026-q4-example-bulk-export` once you have a real one.
