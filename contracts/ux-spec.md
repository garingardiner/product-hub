# Contract: UX Specification (phase 3, Spec)

**Purpose:** Show how the experience works, covering every P0 requirement.
**Consumers:** Engineering, PM, Support.
**Default form:** the designs live in `figma` (or a `claude-artifact` design); the Product Hub's **UX spec form**
(Fill out on the Spec phase card) records the design links, flows mapped to requirement IDs, states, accessibility and
open questions. At sync it writes `ux-spec.yaml` and generates `ux-spec.md` (form `repo-md`, with the Figma link kept as
the artifact's link). P0 requirements no flow covers, and blocking design questions, show in the Spec gate.

## Must contain
- Flows and screens covering each P0 requirement (note requirement IDs on frames)
- Empty, error, and edge states
- Accessibility considerations
- Open design questions with owners

## Next phase takes
Screens and states that engineering estimates against; QA uses them for test cases.

## Approved when
PM and engineering agree it covers all P0 requirements and is buildable.
