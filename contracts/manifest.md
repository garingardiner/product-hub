# Contract: Initiative manifest (`initiative.yaml`)

Every initiative folder has one. `scripts/status.py` validates it.

```yaml
name: string                 # human-readable name
slug: string                 # matches folder name
problem: string              # one line
phase: discovery | feedback | spec | engineering | gtm | done | parked
priority: P0 | P1 | P2
owner: string                # PM
collaborators: { role: [names] }
target_release: string       # optional, e.g. 2027-Q1
blockers: [string]
decisions:                   # short decision log
  - { date: YYYY-MM-DD, decision: string, by: string }
artifacts:
  <artifact_key>:            # concept, feedback, project_spec, ux_spec, success_metrics, engineering_scope, feature_benefits
    form: repo-md | data | claude-doc | claude-artifact | figma | asana | drive | other
    path: string             # for repo-md / data
    link: string             # for everything else
    status: not-started | draft | in-review | approved | synthesized | superseded
    owner: string
```
