# Contract: Project Specification (phase 3, Spec)

**Purpose:** Define what we're building and why, precisely enough for engineering to scope it.
**Consumers:** Engineering, UX, Support, Sales.
**Default form:** the Product Hub's **Project spec form** (Fill out on the Spec phase card). At sync its sections go to
`spec.yaml`, its requirements to `requirements.yaml`, and `project-spec.md` is generated from both by `scripts/spec_doc.py`
(form `repo-md`). A `claude-doc` following the `write-spec` PRD structure is still fine; either way requirements live in
`requirements.yaml` and the doc references them by ID instead of restating them.

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
