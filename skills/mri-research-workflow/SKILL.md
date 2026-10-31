---
name: mri-research-workflow
description: >-
  Read before designing, analysing, writing up or reviewing an MRI study:
  results sections with a claim ledger, referee reports, gaps and proposals
  from a supplied corpus, sample size and repeatability (ICC with CI) from
  pilot data, group comparisons, cutoffs and held-out splits. Use it, not the
  method skills, for manuscripts. Prevents overclaiming, numbers that do not
  match the data, non-verbatim quotes, wrong statistical units and over-limit
  texts. Ships a writing checker, study statistics and the finish check every
  MRFoundry skill runs.
metadata:
  author: Ke Wang
  version: "0.12.0"
---

# MRFoundry: MRI Research Workflow (studies, statistics, write-ups, reviews, deliverables)

## Route

| Task | Read | Check before finishing |
|---|---|---|
| Results section, abstract, claim ledger | [write-results](references/write-results.md) | `scripts/write_check.py --claims ...` |
| Methods/statistics review of a manuscript | [write-review](references/write-review.md) | `scripts/write_check.py --quotes ...` |
| Research gap and proposal from a supplied corpus | [write-proposal](references/write-proposal.md) | `scripts/write_check.py --ids ... --schema ...` |
| Repeatability and sample size from pilot data | [plan-sample-size](references/plan-sample-size.md) | `scripts/write_check.py --schema ... --numbers-in ...` |
| Group statistics, repeatability, cutoffs | `scripts/study_stats.py` (table below) | finish check |
| Study or method-comparison design: baselines, endpoints, ablations, failure tests | [evaluation guide](../mri-research/references/evaluation-and-attribution.md) | |
| Paper planning, venues, reviewer responses | [paper-writing guide](references/paper-writing.md) | |
| Literature summary or related work | [literature access](../mri-research/references/literature-access.md): state topic and date window, verify primary records, merge versions, label abstract-only items, keep reported claims apart from your assessment | |
| Deliverables with code | | finish check (below) |

`python .agents/skills/mri-research-workflow/scripts/write_check.py --help` lists every flag; each FAIL line
says what to fix. Fix the files, never the checker, and run it again.

## Rules for every write-up, review and plan

1. **Definitions are literal.** Apply each definition the task gives to every record or entry IN CODE (one row
   per record with the fields the definition uses and the decision). Add no criteria and drop none.
2. **Schemas are exact**: key names, vocabulary spellings, one value versus a list, integers. An endpoint
   `unit` is the measurement unit (ms, 1/s, mm²/s, %), never the unit of analysis.
3. **Numbers come from files**: compute in code, keep one ledger, write prose from it with the same rounding;
   no new statistics unless asked. Units and precision as the task states.
4. **Claims match the evidence**: a CI including 0 is reported as no difference detected; exploratory results
   are labelled as such in every clause; no causal or clinical claim beyond the design.
5. **Citations are closed**: only supplied keys or record IDs; a record supports a statement only if it states
   that fact itself.
6. **Limits**: word limits count every token; stay below 90 %. Quotes are one contiguous verbatim passage.

## Study statistics (`scripts/study_stats.py`, tested; `--api` lists signatures)

| Need | Function |
|---|---|
| Two groups | `two_sample_t` (pooled or Welch t, CI, p, pooled SD, Hedges g), `auc`, `subject_bootstrap` |
| Paired | `paired_difference` (t CI, Cohen's dz), `bland_altman` |
| Repeatability | `repeatability` (wSD with chi-square CI, wCV, RC), `icc`, `icc_ci` (F-based CI, all six forms) |
| Sample size | `n_per_group`, `n_paired` (normal or exact t), `sd_of_differences`, `inflate_for_loss`, `combined_fraction`, `n_total_unbalanced` |
| Cutoffs | `threshold_on_dev`, `balanced_accuracy` |

The statistical unit is the subject (or the unit the plan names), never the voxel; fix every setting, threshold
and cutoff on development subjects and apply it unchanged to held-out subjects; the study's analysis plan
overrides these defaults.

## Finish check (every task with files to deliver)

    python .agents/skills/mri-research-workflow/scripts/finish_check.py \
        --require <every deliverable name the task lists> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder> \
        [--expect <files the entrypoint must write>] [--json report.json:key1,key2/sub] [--range FILE:LOW:HIGH]

It fails on missing or misnamed deliverables, an entrypoint stored apart from its outputs, no environment
record when code is delivered, an entrypoint that fails in a fresh folder, and map medians outside the
expected range. Without code, use `--require` only. `--help` lists the flags of either checker: run them, do not
read their sources. A standalone single-file entrypoint takes tested helpers with
`python .agents/skills/mri-research-workflow/scripts/inline_helpers.py <module.py> <functions> --into <entrypoint.py>`.

Citations: [reading list](references/reading-list.md).
Project notes (only with `.mrfoundry/INDEX.md`): [project memory](../mri-research/references/project-memory.md).

