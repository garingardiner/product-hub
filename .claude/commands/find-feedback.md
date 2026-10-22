Find customer feedback relevant to: $ARGUMENTS

1. Run `python scripts/feedback.py tags` to see the tag vocabulary, then pick the tags, types, and segments that fit the request.
2. Run a few `python scripts/feedback.py search ... --json` queries (by tag first, then by words) and merge the results.
3. Report: how many entries match, the main themes with entry IDs and a representative exact quote for each,
   which segments and customers they come from, and where evidence is thin or comes from only one customer.
4. List the searches you ran so they can be saved in an initiative's `feedback.yaml` → `searches`.
5. If `feedback/library.json` looks stale (check `exported_at`), say so and suggest re-exporting from the Feedback Board.
Never quote anything that isn't in the library.
