---
name: mri-research-workflow
description: >-
  Read before designing, analysing or reporting an MRI study with subjects,
  groups or repeated scans: development and held-out splits, biomarker
  comparisons, repeatability (wCV, ICC), cutoffs and classification, confidence
  intervals, analysis plans, reports and papers for MRM, JMRI, TMI, MICCAI or
  CVPR. Prevents test-data leakage, the wrong statistical unit and numbers that do
  not match saved outputs. Ships tested study statistics and the finish check
  (missing or split deliverables, entrypoints that fail on a clean rerun) that
  every MRFoundry skill runs. Measurements belong to the specialist skills.
metadata:
  author: Ke Wang
  version: "0.11.0"
---

# MRFoundry: MRI Research Workflow (study design, statistics, deliverables, papers)

## Finish check (every task with files to deliver)

    python .agents/skills/mri-research-workflow/scripts/finish_check.py \
        --require <every deliverable name the task lists> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder> \
        [--expect <files the entrypoint must write>] [--json report.json:key1,key2/sub] [--range FILE:LOW:HIGH]

It fails when a deliverable is missing or misnamed, when the entrypoint sits in one folder and its outputs in
another (put all of them in the folder the task names, else the workspace root), when no environment record
exists, when the entrypoint fails in a fresh folder holding only the script and the inputs, and when a map
median falls outside the expected range for its units. Fix each FAIL and run it again. Produce every
deliverable first, then refine. `scripts/check_deliverables.py spec.json` checks nested JSON keys and array
shapes against a spec.

## Study statistics (`scripts/study_stats.py`, tested)

| Need | Function |
|---|---|
| Group separation | `auc` (Mann-Whitney), `paired_difference` (t-based CI, Cohen's dz), `subject_bootstrap` |
| Repeatability | `repeatability` (within-subject SD with chi-square CI, wCV, repeatability coefficient), `within_subject_cv` |
| Agreement | `icc` (one-way, two-way random and mixed; single and average measures; k sessions), `icc_3_1`, `bland_altman` |
| Cutoffs and classification | `threshold_on_dev`, `balanced_accuracy` |

Rules: the statistical unit is the subject (or lesion, or ROI-session if the plan says so), never the voxel;
declare the unit and ICC form for every endpoint; fix every model setting, threshold and cutoff on
development subjects and apply it unchanged to held-out subjects; the study's analysis plan overrides these
defaults; recompute every reported number from the saved outputs.

## From idea to paper

1. **Frame**: related work ([literature access](../mri-research/references/literature-access.md)), the gap, one
   claim, the target venue ([publishing](../mri-research/references/publishing.md)).
2. **Design**: datasets and licences, baselines, endpoints, ablations, reference standards, failure tests and
   what would falsify the claim ([evaluation guide](../mri-research/references/evaluation-and-attribution.md));
   keep tuning and test data separate; record seeds, configurations and logs.
3. **Run** with the specialist skills (reconstruction, deep learning, diffusion, sequences, hardware).
4. **Analyze** the planned endpoints with uncertainty, subgroups and failure cases; limit conclusions to the
   evidence collected.
5. **Write** from verified evidence ([paper-writing guide](references/paper-writing.md),
   [paper plan](assets/paper-plan.md), [reviewer response](assets/reviewer-response.md)); keep planned and actual
   results distinct; submission requires user authorization.

Citations: [reading list](references/reading-list.md). Project notes (only with `.mrfoundry/INDEX.md`):
[project memory](../mri-research/references/project-memory.md). Setup problems:
[tool setup guide](../mri-research/references/tool-setup.md).
