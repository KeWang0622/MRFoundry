# Research gap and study proposal from a supplied corpus

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`. Common rules: the workflow SKILL.md.

1. Load the corpus into one table in code: record ID, population, technique, reference standard, design, the
   sizes of the groups COMPARED in the main analysis, the analysis type of the main finding, its p-value,
   technical success, and the IDs a record explicitly relies on.
2. Apply each definition to every row and print the deciding fields. Under a "significant main finding and
   small groups" definition: a correlation or regression finding uses the total-n threshold even when subgroup
   counts are listed; a one-group paired study uses that group's n; a non-significant main finding is not
   underpowered. Dependents name the record ID explicitly.
3. Contradictions: same technique, population and reference; find the protocol factor that separates the
   significant from the null records (tabulate every candidate factor on both sides).
4. Gap: enumerate technique x population x reference combinations and test each gap rule in code; list as
   support only records that establish each rule.
5. Sample size: inputs only from records the rules allow; `study_stats.n_per_group` or `n_paired`,
   `combined_fraction`, `n_total_unbalanced` or `n_enrol`; round up once, at the end.
6. Run, fix every FAIL, run again:

       WC --texts proposal.md proposal.json --ids <corpus json> --schema task.json:<schema key>=proposal.json \
          --words proposal.md:<limit> --numbers-in proposal.md=proposal.json:<paths of the sample sizes>

