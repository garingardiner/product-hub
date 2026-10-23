Move initiative `$ARGUMENTS` to its next phase (or to the phase named in the arguments).

1. Read its `initiative.yaml` and the gate checklist for its current phase in `CLAUDE.md`. Run `python scripts/status.py`.
2. If the checklist has open items, list exactly what's still open and offer to help close each one, then ask whether to
   move anyway. Gates don't block: move only once the user says to, and they may pick any phase.
3. Set `phase`, add a dated entry to `decisions` that names any open checklist items at the time of the move, and run the
   script again.
4. Read the new phase's contracts and propose the first artifact to create, including which form you recommend and why,
   and which inputs from earlier phases you'll pull in.
