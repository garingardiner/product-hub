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
| `tags` | 2–5 topic tags (see below) |
| `source` | `interview`, `sales-call`, `support-ticket`, `survey`, `usage-data`, `other` |
| `customer`, `segment`, `date` | Who and when. Segment is a tag-style value (`enterprise`, `mid-market`). |
| `contact` | Optional name and role of the person who said it (e.g. "Dana Lee, AM lead") |
| `initiative` | Optional initiative slug this entry was collected for, picked from the board's initiative list |
| `updatedAt` | Set by the board when an entry is edited after saving |
| `requirements` | Optional requirement IDs it supports (`R-001`) |

## Tagging conventions
- Lowercase and hyphenated: `bulk-export`, `audit-reporting`, `sso`.
- Tags describe **what the feedback is about** (product area, workflow, capability), not its type, segment, or customer.
  Those have their own fields and filters.
- Reuse before creating. The board shows Claude the existing tags and asks it to reuse them; humans should do the same.
- Prefer the noun people search for: `permissions`, not `cant-share-with-team`.
- Keep the set healthy: monthly, run `python scripts/feedback.py tags` and merge near-duplicates on the board
  (e.g. `export` vs `exports` vs `data-export`).

## Quality bar
- A quote that doesn't appear in the source notes is a bug. The board flags it; fix it before saving.
- Don't log internal opinions as customer feedback. If it's a hunch, it belongs in a concept doc as a hypothesis.
