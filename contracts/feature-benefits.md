# Contract: Feature / Benefits (phase 5, GTM)

**Purpose:** Equip sales and marketing to explain what shipped and why customers should care.
**Consumers:** Sales, Marketing, Support.
**Default form:** the Product Hub's **Feature/Benefits form** (Fill out on the GTM phase card). At sync it writes
`feature-benefits.yaml` and generates `feature-benefits.md`, pulling proof-point quotes from the feedback library. Claims
that map to requirements not in the engineering scope are flagged in the GTM gate. Enablement slides (`claude-artifact`)
or a one-page `claude-doc` can be built from it; an existing link is kept as the artifact's link. Marketing may adapt it.

## Inputs
Shipped scope items from `scope.yaml` (only what actually ships), customer evidence from feedback.

## Must contain
- One paragraph: what the feature is and how it benefits the user (optionally, the requirement IDs it describes,
  which must be in the engineering scope)
- Target segments and the problem it solves for each
- Proof points: customer quotes or data from the feedback library only (the form's Suggest proof points recommends
  entries; a person picks which to use)
- Availability: release date, plans/tiers, limitations (where over-promising risks live)

## After launch
Review `metrics.yaml` on the review date; record actuals and verdicts, then set the initiative to `done`.

## Approved when
Sales and marketing leads have reviewed it, and every claim maps to a shipped requirement.
