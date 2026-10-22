Link library feedback to initiative `$ARGUMENTS`.

1. Read the initiative's `initiative.yaml`, `requirements.yaml`, and `feedback.yaml` (hypotheses, existing evidence, saved searches).
2. Re-run the saved searches and search for the initiative's topics; show me candidate entries not yet linked.
3. For each entry I approve, add it to `feedback.yaml` → `evidence` with the hypotheses and requirement IDs it bears on,
   and add its ID to the matching requirements' `evidence` in `requirements.yaml`.
4. Update hypothesis verdicts and themes only if the evidence clearly supports it; otherwise leave them open and say why.
5. Run `python scripts/feedback.py check` and `python scripts/status.py`.
