Start a new initiative: $ARGUMENTS

1. Create `initiatives/<yyyy-qn-short-slug>/` by copying `initiatives/_template/`. Use today's quarter.
2. Fill in `initiative.yaml`: name, slug, one-line problem, owner, priority (ask if unclear), collaborators.
3. Read `contracts/concept.md`. Ask me the questions needed to draft the concept, a few at a time.
4. Seed `requirements.yaml` and the `hypotheses` in `feedback.yaml` from what we discuss.
5. Draft the concept in the form recorded in the manifest (default: Claude Doc) and record its link and status `draft`.
6. Add the initiative to the Feedback Board's `initiatives` collection (doc id = slug, `{name}`) so contributors can pick it.
7. Run `python scripts/status.py` and show me the roadmap row.
