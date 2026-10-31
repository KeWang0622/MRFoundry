# Results section, abstract and claim ledger

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`. Common rules: the workflow SKILL.md.

1. Build the claim ledger first, in the schema the task gives: one record per reported result holding every number
   the text will show (estimate, interval, spread, p-value exactly as supplied, n), its unit and its
   interpretation. Convert units in code and round once.
2. Report the primary endpoint and every prespecified secondary endpoint, significant or not; give the point
   estimate, its 95 % CI, the p-value and n for each. Draw inference from the comparison between groups; a change
   inside one group is description only.
3. When a 95 % CI includes 0, the sentence that gives the estimate also states that the comparison found no
   difference (in the task's wording when it lists phrases), and the ledger's interpretation agrees. Do not soften
   a null result with hedging words.
4. Label every subgroup or unplanned estimate as exploratory (or post hoc) in each clause and table row that gives
   it (a ';' starts a new clause), give the interaction test, and do not describe the effect as differing between
   subgroups.
5. Every number in the text comes from the inputs or a stated unit conversion; do not derive statistics that the
   inputs do not report. A difference between two percentages is in percentage points (pp); a relative change is
   labelled relative.
6. Run, fix every FAIL, run again:

       WC --words <summary file>:<limit> --texts <summary file> <results file> --bib <bib file> --claims <ledger> \
          --loc <name>=<summary file> --loc <name>=<results file> --trace <source json> [--scale <unit factor>] \
          [--null-phrases @<task json>:<phrase list>] [--forbid-in "<topic words>::@<task json>:<word list>"] \
          [--require-in "<subgroup words>::exploratory,post hoc"]

