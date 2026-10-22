# Contract: Initiative manifest (`initiative.yaml`)

Every initiative folder has one. `scripts/status.py` validates it.

```yaml
name: string                 # human-readable name
slug: string                 # matches folder name
problem: string              # one line
phase: discovery | feedback | spec | engineering | gtm | done | parked
priority: P0 | P1 | P2
owner: string                # PM
team: Build | Analyze | Orchestrate
size: Small | Medium | Large   # rough project size
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
attachments:                 # links and files added per phase (usually from the Product Hub page)
  - id: A-YYMMDD-XXXX
    phase: discovery | feedback | spec | engineering | gtm
    title: string
    kind: link | file
    link: string             # kind link (Google Drive, Figma, any https URL)
    asset: string            # kind file: the hub's uploaded-file id; filename: original name
    file: string             # kind file: where the original was saved, e.g. files/notes.pdf
    repo_link: string        # kind file: GitHub link to that original, set at sync
    use_as: string           # optional artifact key it fills (sets that artifact's link or path)
    read: bool               # true once Claude has read it
    source: string           # extracted text, e.g. sources/A-261022-AB12.md
    summary: string          # one line on what it says
```
