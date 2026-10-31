# Repeatability and sample size from pilot data

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`; statistics: `scripts/study_stats.py`.

1. Apply the QC rule first and list the exclusions. Form the endpoint exactly as defined (for example an average over regions
   or repeats within one session); the unit of analysis is then the participant, not the region or repeat.
2. Repeatability on participants with both sessions: `repeatability` (within-subject SD and its chi-square
   CI; RC = 2.77 wSD = 1.96 √2 wSD) and `icc_ci(data, form)` in the form the task names (ICC(2,1) absolute
   agreement; ICC(3,1) consistency).
3. Choose the design that answers the question most efficiently: each participant under both conditions and no
   carryover -> paired or crossover design, whose SD is √2 x wSD (`sd_of_differences`, `n_paired`);
   separate groups -> parallel groups, using the between-participant SD from the group pilot (`two_sample_t`
   gives the pooled SD; `n_per_group`). Then `inflate_for_loss(n, loss_fraction)`.
4. Run, fix every FAIL, run again:

       WC --schema <task json>:<schema key>=<design json> --numbers-in <plan md>=<design json>:<paths of n> --words <plan md>:<limit>

