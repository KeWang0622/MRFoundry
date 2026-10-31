# Evidence audit and study proposal from a supplied corpus

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`. Common rules: the workflow SKILL.md.

1. Load the corpus into one table in code: record ID, population, method, reference standard, design, the size of
   each group the main analysis compares, the type of that analysis, its p-value, technical success, and the
   record IDs a record names as its basis.
2. Apply every definition in code, in dependency order (a definition that uses another one comes after it), and
   print the fields each decision used. Read each clause literally against the record's main analysis: count only
   the groups that analysis compares (group sizes listed for description do not count), use the analysis type the
   record states, and leave a record out when its main finding fails any clause. A record depends on another only
   if it names that record's ID.
3. Disagreements: within one method, population and reference standard, tabulate every protocol and population
   factor for the records with and without a significant result, and find the factor that separates them.
4. Gap: enumerate the method x population x reference combinations and test each gap rule in code; cite as
   support only records that establish the rule they are cited for.
5. Controls: include each confounder or protocol factor that the corpus shows to change the chosen measure in the
   chosen population, citing the records that demonstrate the effect (a record that only applied a control does
   not support it). Add the physical dependencies of the measure: relaxation times depend on field strength and
   mapping sequence, diffusion metrics on the b-values fitted, perfusion on labelling and delay.
6. Sample size: take inputs only from records the rules allow; `study_stats.n_per_group` or `n_paired`,
   `combined_fraction`, `n_total_unbalanced` or `inflate_for_loss`; round up once, at the end.
7. Run, fix every FAIL, run again:

       WC --texts <proposal md> <proposal json> --ids <corpus json> --schema <task json>:<schema key>=<proposal json> \
          --words <proposal md>:<limit> --numbers-in <proposal md>=<proposal json>:<paths of the sample sizes>

