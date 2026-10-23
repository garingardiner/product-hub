# Contract: UX Specification (phase 3, Spec)

**Purpose:** Show how the experience works, covering every P0 requirement.
**Consumers:** Engineering, PM, Support.
**Default form:** the designs live in `figma` (or a `claude-artifact` design); the Product Hub's **UX spec form**
(Fill out on the Spec phase card) records the sections below. At sync it writes `ux-spec.yaml` and generates
`ux-spec.md` (form `repo-md`, with the Figma link kept as the artifact's link). P0 requirements the design doesn't
cover, and blocking design questions, show in the Spec gate.

## Must contain
Follows the UX Specification Template (Streamlined):
1. Overview & key information: feature/flow name, target release, product designer, product manager, design status
   (draft / in review / design ready / handoff), Figma file link
2. Sales & marketing UX snapshot: one-sentence experience summary, friction removed, customer value, demo talking point
3. User journey & flow: target persona, entry point, primary user goal, success state / exit, and the requirement IDs the
   design covers (every P0; note the IDs on the Figma frames too)
4. UI component states & behaviors: screen/component, state (default, hover, loading, empty, error, success, disabled),
   behavior / visual spec
5. Content & microcopy: action labels, error and validation messages, confirmation messages
6. Accessibility & responsive: keyboard navigation, screen reader / ARIA labels, breakpoints
7. Out of scope / deferred interactions
- Plus open design questions with owners (blocking ones hold the Spec gate)

## Next phase takes
Screens and states that engineering estimates against; QA uses them for test cases.

## Approved when
PM and engineering agree it covers all P0 requirements and is buildable.
