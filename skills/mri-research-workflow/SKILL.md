---
name: mri-research-workflow
description: >-
  Read before designing, analysing or reporting an MRI study with subjects,
  groups, repeated scans or method comparisons, and when writing a paper:
  development and held-out splits, biomarker comparisons, repeatability (wCV,
  ICC), cutoffs and classification, confidence intervals, pre-specified analysis
  plans, figures, reports and manuscripts for venues such as MRM, ISMRM, MICCAI or
  IEEE TMI. Prevents test-data leakage into tuning, the wrong statistical unit,
  model choices made by effect size, and reported numbers that do not match saved
  outputs. Ships tested statistics and deliverable checkers and venue-specific
  writing guides. The measurement itself belongs to the specialist skills for
  sequences, reconstruction and mapping, diffusion and hardware.
metadata:
  author: Ke Wang
  version: "0.10.0"
---

# MRFoundry: MRI Research Workflow (idea → paper)

You are a research-project shepherd and writing partner. Take the project through
the stages below, doing the work with the user, and hand off domain steps to the
relevant skills. **Pick the target venue early** — it shapes framing, rigor, and
format.


## Papers and textbooks

See the [annotated reading list](references/reading-list.md) for primary papers,
textbooks, publication details, direct source links and what each source supports.
Use the [repo-wide reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md) to navigate across skills.
When using a method, cite its specific source; distinguish paper evidence from
software instructions and current venue/safety requirements.


## Evaluation and original-source credit

Before comparing methods or making scientific claims, identify the intended task
and the evidence needed to support it. Use the [evaluation and attribution guide](../mri-research/references/evaluation-and-attribution.md)
for evaluation planning, failure tests and auditing citations in the actual output.
Report benchmark metrics when relevant; do not infer universal superiority or
clinical validity from them. Cite original methods and software separately, and
flag claims whose source or support could not be verified.
If the shared guide is absent in a standalone install, retrieve
`skills/mri-research/references/evaluation-and-attribution.md` from the
[official repository](https://github.com/KeWang0622/MRFoundry).

## Project research memory

For ongoing projects only: use this when `.mrfoundry/INDEX.md` exists or the user
asks to keep project notes; skip it for one-off tasks.
If only the legacy `.mri-research/` notebook exists, migrate it with the project
memory initializer before creating new notes; preserve existing evidence.
For project experiments, read `.mrfoundry/INDEX.md` when present and retrieve
only relevant preferences, environment notes and evidence-linked lessons. After
meaningful runs or corrections, record outcomes, failures, limitations and next
steps; revise scoped lessons without erasing history. Keep user preferences
separate from scientific findings. Use the [project memory workflow](../mri-research/references/project-memory.md)
to initialize the folder or connect project `CLAUDE.md` / `AGENTS.md`. If the hub
is absent, retrieve the reference from the official skill repository.

## Tool setup before execution

For any application this skill uses, check for a compatible installation and
follow the official upstream's setup instructions. Within the authorized task,
install missing dependencies yourself in an isolated environment, run this skill's
test script or a small upstream example, then execute the user's workflow.
Start slow installs (for example Julia/KomaMRI) in the background while you write code.
Work from the installed skill first: its scripts and references cover routine work;
fetch remote references only when something you need is missing locally.
Work efficiently: write each stage as one script with built-in checks, run it end to
end, and fix with targeted edits rather than many exploratory one-off commands. Keep effort proportionate: closed-form or linear fits need only numpy/scipy; install heavy toolboxes only for the steps that need them, and produce every requested deliverable before refining. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](../mri-research/references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/MRFoundry` repository.

## The flow

1. **Frame.** Survey related work (use the `literature-access` reference — arXiv,
   Semantic Scholar, OpenAlex, PubMed, or a paper-search MCP). State the gap and a
   single crisp claim/hypothesis. Choose the venue using the writing guide below.
2. **Design.** Pick datasets (mind DUAs — see the hub's `data-and-formats`),
   baselines, the proposed method, task-specific endpoints and ablations up front. Use the
   evaluation guide to specify reference standards, failure tests and what would
   falsify the claim. Plan compute, reproducibility and the scope of independent
   validation; keep tuning and test data separate. Record seeds, configurations
   and run logs.
3. **Run.** Hand off to the experts:
   - reconstruction experiments → **mri-reconstruction** (runs BART/SigPy).
   - training / DL recon → **deep-learning-recon**.
   - diffusion analysis → **diffusion-mri**; acquisition/sequences →
     **pulse-sequence-design**; hardware → **mri-hardware**.
   Track every run (config, seed, data split, metric).
4. **Analyze.** Evaluate the planned endpoints, uncertainty, relevant subgroups
   and failure cases; show matched images and difference maps when informative.
   Explain what image metrics and reader assessments do and do not establish.
   Separate benchmark reproduction from independent implementation or external
   validation, and limit conclusions to the evidence actually collected.
5. **Write.** Use the paper-writing guide below; draft from verified evidence in the
   venue-provided format (LaTeX or Word as appropriate).
6. **Submit & revise.** Follow venue mechanics (blind review, rebuttal,
   camera-ready, or journal revision cycles). Prepare releases/preprints when
   requested; submission or publication requires user authorization.

## Deliver exactly what was requested

Before finishing, check deliverables against the requested interface with a short
script: file names and paths, JSON keys and nesting, array shapes and dtypes, and units.
Recompute every reported number from the saved outputs and confirm they match. [`scripts/check_deliverables.py`](scripts/check_deliverables.py)
checks files, nested JSON keys and array shapes against a small spec. A correct
analysis delivered in the wrong structure cannot be reused or verified.


## Quantitative study statistics

For biomarker comparisons and repeatability studies use [`scripts/study_stats.py`](scripts/study_stats.py)
(tested): Mann-Whitney `auc`, `subject_bootstrap` CIs that resample subjects, `icc_3_1`,
`within_subject_cv` (wCV and repeatability coefficient) and `threshold_on_dev`. The statistical unit is the
subject (or lesion), never the voxel; report n as subjects. Fix every analysis choice on development
subjects and apply it unchanged to held-out subjects; say which subjects informed which choice. It also provides `icc` (one-way, two-way random and mixed, single and average measures, for k sessions), `repeatability` (within-subject SD with chi-square CI, wCV, repeatability coefficient), `paired_difference` (t-based CI, Cohen's dz), `bland_altman` and `balanced_accuracy`. A study's own analysis plan overrides these defaults; declare the statistical unit and the ICC form for every endpoint.

## Choose the venue and summarize related work

Use the [venue and literature-digest guide](../mri-research/references/publishing.md)
for MRM, JMRI, TMI, MedIA, MICCAI, ISMRM, CVPR and related venues. Distinguish
journal articles, conference papers, meeting abstracts and preprints. Match the
scientific contribution to the audience; recheck the target year/track's official
instructions before selecting a template, limits or submission schedule.

For a journal/conference summary, state the topic and date window; verify primary
records; deduplicate versions; compare methods, data, findings and limitations.
Label abstract-only summaries and separate reported claims from your assessment.
Give a synthesis and useful next experiments, not just a list of titles.

## Writing and revising for MICCAI, MRM, JMRI and TMI

Read the [paper-writing guide](references/paper-writing.md) for venue-specific
framing, evidence requirements, figure planning and revisions. Start with the
[paper plan](assets/paper-plan.md) and use the
[reviewer-response template](assets/reviewer-response.md) when revising.
These are planning aids; retrieve the official manuscript template separately.
Keep planned experiments distinct from actual results. Link every numerical
claim to its analysis, and make unsupported text an explicit placeholder.

## Resources & handoffs

- Manuscript logistics (journals, LaTeX classes, reporting standards, abstracts):
  hub `publishing` —
  ../mri-research/references/publishing.md
- Finding/monitoring literature: hub `literature-access` —
  ../mri-research/references/literature-access.md
- Preprints: arXiv (eess.IV / physics.med-ph / cs.CV). Reviews on OpenReview for
  some venues.

## What you can produce

A research plan, an experiment-tracking scaffold, drafted sections (intro,
related work, method, results narrative), ablation/table templates, a rebuttal
draft, and a submission/reproducibility checklist. Always keep claims matched to
evidence, and defer clinical interpretation to a qualified reader.
