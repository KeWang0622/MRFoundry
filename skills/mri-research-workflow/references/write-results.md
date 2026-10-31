# Results section, abstract and claim ledger

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`. Common rules: the workflow SKILL.md.

1. Build `claims.json` first, one claim per reported entry: estimate, CI, SD or IQR, p as given (adjusted or
   interaction p where stated), n, unit, interpretation, locations. Convert units in code and round once.
2. Report the primary endpoint and EVERY prespecified secondary endpoint, significant or not, with estimate,
   95 % CI, p and n. Between-group comparisons carry the inference; within-group changes are descriptive.
3. A CI that includes 0 gets a no-difference phrase ("no difference was detected", or the task's list) IN THE
   SAME SENTENCE as its estimate, and interpretation `no_effect_detected`. Never "trend", "tended",
   "approached", "borderline" or "numerically".
4. Subgroup and post hoc estimates: "exploratory" (or "post hoc") in every sentence, clause and table row that
   reports one (a ';' starts a new clause); give the interaction p; no "larger/greater/stronger/especially".
5. Every number in the text comes from the inputs or a stated unit conversion: no new relative changes,
   percentages of baseline, ratios or power. Differences of percentages are percentage points (pp).
6. Run, fix every FAIL, run again:

       WC --words abstract.md:<limit> --texts abstract.md results.md --bib refs.bib --claims claims.json \
          --loc abstract=abstract.md --loc results=results.md --trace <results json> [--scale <unit factor>] \
          [--forbid-in "<topic words>::@task.json:<banned-word list>"] [--require-in "<subgroup words>::exploratory,post hoc"]

