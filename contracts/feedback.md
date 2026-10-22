# Contract: Feedback (phase 2, User feedback)

**Purpose:** Validate or refute the concept's hypotheses with real customer evidence and size the opportunity.
**Consumers:** PM, User research, UX; later Spec and GTM (quotes, segments).
**Default form:** `data` (`feedback.yaml`) that cites entries from the shared feedback library by ID,
plus an optional synthesis view as a `claude-doc`. New feedback goes into the library (the Feedback Board), not here.

## Must contain
- `evidence` in `feedback.yaml`: library entry IDs, each linked to the hypotheses and requirement IDs it bears on
- New interviews for this initiative logged on the Feedback Board with `initiative` set to this slug
- Themes ranked by frequency and impact (use `synthesize-research`)
- Verdict on each concept hypothesis: supported / refuted / inconclusive, with evidence count
- Validated sizing in `feedback.yaml` → `sizing` (segments, customer counts, revenue signal if known)
- Changes to `requirements.yaml` the evidence implies (add, drop, re-prioritize)

## Next phase takes
Validated requirements with priorities, sizing, and representative evidence for the spec's problem statement.

## Synthesized when
Every hypothesis has a verdict and sizing is filled in. (Status `synthesized` satisfies the gate.)
