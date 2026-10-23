# Contract: Project Specification (phase 3, Spec)

**Purpose:** Define what we're building and why, precisely enough for engineering to scope it.
**Consumers:** Engineering, UX, Support, Sales.
**Default form:** the Product Hub's **Project spec form** (Fill out on the Spec phase card). At sync its sections go to
`spec.yaml`, its requirements to `requirements.yaml`, and `project-spec.md` is generated from both by `scripts/spec_doc.py`
(form `repo-md`). A `claude-doc` following the `write-spec` PRD structure is still fine; either way requirements live in
`requirements.yaml` and the doc references them by ID instead of restating them.

## Must contain
Follows the Product Specification Template (Streamlined) V3:
1. Overview & key information: feature name, target launch, product owner, status (from the manifest)
2. Sales & marketing brief: what it is (one sentence), 2–3 key benefits, target user, two-sentence sales pitch
3. Problem & goals: problem statement grounded in feedback evidence, and success metrics
4. Requirements & user stories: each requirement is a story (As a… / I want to… / So that…) with a stable ID,
   priority (P0 must have, P1 should have, P2 could have) and acceptance criteria, all in `requirements.yaml`
   (`user`, `title`, `benefit`)
5. Out of scope for this release
6. Design & tech notes: UI / design link (or the UX spec), technical dependencies and constraints
- Plus open questions, each with an owner and blocking/non-blocking (blocking ones hold the Spec gate)

## Next phase takes
The P0/P1 requirement set and acceptance criteria, which become engineering scope items.

## Approved when
Engineering and UX have reviewed it, no blocking open questions remain, and support has signed off on support considerations.
