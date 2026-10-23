# Contract: Feedback entry (shared library)

One piece of customer feedback: one point from one customer. A single interview usually produces several entries.
Collected on the Feedback Board; snapshotted to `feedback/library.json`.

## Fields
| Field | Notes |
|---|---|
| `id` | `F-YYMMDD-XXXX`, assigned by the board. Cite this everywhere. |
| `quote` | The customer's exact words, shortest span that makes the point. Empty if there are none. Never paraphrased. |
| `summary` | One plain sentence in our words. |
| `type` | `pain-point`, `feature-request`, `bug`, `workaround`, `question`, `churn-risk`, `praise` |
| `sentiment` | `negative`, `neutral`, `positive` |
| `tags` | 1–3 tags from the board's approved tag list (see below) |
| `suggested_tags` | New tags waiting for the board owner to approve, merge or reject. Not used for search until approved |
| `source` | `interview`, `sales-call`, `support-ticket`, `survey`, `usage-data`, `other` |
| `customer`, `segment`, `date` | Who and when. Segment is picked on the board: `aerospace`, `automotive`, `power` (add more in the board's `SEGMENTS` list). |
| `contact` | Optional name and role of the person who said it (e.g. "Dana Lee, AM lead") |
| `link` | Optional https link to the interview: recording, notes or transcript. Editable or removable later on the board |
| `initiative` | Optional initiative slug this entry was collected for, picked from the board's initiative list |
| `updatedAt` | Set by the board when an entry is edited after saving |
| `requirements` | Optional requirement IDs it supports (`R-001`) |

## Tagging conventions
- **Controlled list.** The board's `tags` collection is the approved list (`tags/<tag>`: `{status, description}`),
  owned by the board owner. Claude only applies tags from it, at most 3 per entry.
- Anything new (from Claude or a person) is saved as a **suggested** tag. The owner reviews suggestions in the board's
  Tags panel: Approve (adds it to the list and to those entries), Merge into an existing tag, or Reject.
  The same panel merges or retires approved tags and rewrites every entry that has them.
- Tags name a broad **product area** (e.g. `geometry-modeling`, `cfd`, `automation`), lowercase and hyphenated.
  Never a customer, segment, type, initiative, product or block name (no `loft-block`): those have their own fields.
- Prefer the noun people search for: `export`, not `cant-export-stl`.
- Keep the list short (about 20–30). Check monthly with `python scripts/feedback.py tags`.

## Quality bar
- A quote that doesn't appear in the source notes is a bug. The board flags it; fix it before saving.
- Don't log internal opinions as customer feedback. If it's a hunch, it belongs in a concept doc as a hypothesis.
