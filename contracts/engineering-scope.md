# Contract: Engineering Scope (phase 4, Working with engineering)

**Purpose:** Agree what will be built, in what order, and how it will be verified.
**Consumers:** Engineering, QA, Support, PM.
**Default form:** `data` (`scope.yaml`) synced to `asana`. Engineering works from tasks; the YAML keeps traceability.

## Inputs
Project spec, UX spec, `requirements.yaml`. (Not new customer interviews. Escalate back to Spec if requirements change.)

## Must contain
- Scope items, each referencing requirement IDs, with estimate and Asana task link
- Explicit in/out of scope list for this release; every P0 requirement in scope
- Dependencies and risks
- QA approach: test plan owner, what gets automated vs. manual, acceptance criteria coverage
- Support readiness: what support needs before launch

## Next phase takes
The final list of shipped requirements, which defines what GTM can promise.

## Approved when
Engineering lead and PM agree on scope, every P0 is covered, and the QA approach is filled in.
