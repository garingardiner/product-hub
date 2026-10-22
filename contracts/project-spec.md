# Contract: Project Specification (phase 3, Spec)

**Purpose:** Define what we're building and why, precisely enough for engineering to scope it.
**Consumers:** Engineering, UX, Support, Sales.
**Default form:** `claude-doc` following the `write-spec` PRD structure. Requirements live in `requirements.yaml`;
the doc references them by ID instead of restating them in a second place.

## Must contain
- Problem statement grounded in feedback evidence
- Goals and non-goals (with rationale)
- User stories by persona
- Requirements by ID with priority (P0/P1/P2) and acceptance criteria, all in `requirements.yaml`
- Link to success metrics (`metrics.yaml`) and UX spec
- Open questions, each tagged with an owner and blocking/non-blocking
- Support considerations: docs, known edge cases, expected ticket types

## Next phase takes
The P0/P1 requirement set and acceptance criteria, which become engineering scope items.

## Approved when
Engineering and UX have reviewed it, no blocking open questions remain, and support has signed off on support considerations.
