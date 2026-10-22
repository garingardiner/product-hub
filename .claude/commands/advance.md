Try to move initiative `$ARGUMENTS` to its next phase.

1. Read its `initiative.yaml` and the gate for its current phase in `CLAUDE.md`. Run `python scripts/status.py`.
2. If the gate fails, list exactly what's missing and offer to help close each gap. Do not change the phase.
3. If it passes, set `phase` to the next phase, add a dated entry to `decisions`, and run the script again.
4. Read the next phase's contracts and propose the first artifact to create, including which form you recommend and why,
   and which inputs from earlier phases you'll pull in.
