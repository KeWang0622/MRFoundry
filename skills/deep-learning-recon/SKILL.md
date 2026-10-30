---
name: deep-learning-recon
description: >-
  Read before training, fine-tuning, applying or evaluating a neural network for
  MRI reconstruction: unrolled and variational networks (VarNet, MoDL), self-
  supervised training without fully sampled data (SSDU), diffusion or score-based
  priors, physics-guided data consistency, fastMRI and mridata datasets, and
  frameworks such as DIRECT, fastMRI and torchkbnufft. Prevents silent errors from
  train, validation and test leakage, inconsistent k-space normalization and
  sampling masks between training and testing, unfair classical baselines, and
  metrics computed on the wrong region or scale. Classical training-free
  reconstruction (ESPIRiT, SENSE, GRAPPA, compressed sensing, NUFFT) belongs to
  mri-reconstruction.
metadata:
  author: Ke Wang
  version: "0.10.0"
---

# MRFoundry: Deep-Learning MRI Reconstruction

You are a DL-recon researcher. **Unrolled networks** combine iterative solver
steps with learned regularizers/updates and measurement consistency. Evaluate
the forward model and data consistency, but do not treat consistency as proof
of feature fidelity: undersampling leaves information unconstrained, and priors
can influence that information even when measurement residuals are small.


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
end, and fix with targeted edits rather than many exploratory one-off commands. Keep effort proportionate: closed-form or linear fits need only numpy/scipy; install heavy toolboxes only for the steps that need them, and produce every requested deliverable before refining. Before finishing, confirm every requested deliverable exists under its exact name and location, and rerun each standalone entrypoint from a fresh copy in a temporary directory with the project's interpreter on the provided input; record that command in the environment record. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](../mri-research/references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/MRFoundry` repository.

## Method families (with citations)

- **Variational Network (VN)** — Hammernik et al., *MRM* 2018;79(6):3055–3071.
  Code: https://github.com/VLOGroup/mri-variationalnetwork
- **MoDL** — CNN prior + CG data consistency, weight-shared. Aggarwal et al.,
  *IEEE TMI* 2019. Code: https://github.com/hkaggarwal/modl
- **End-to-End VarNet** — learns coil sensitivities too; strong fastMRI baseline
  (Sriram et al., MICCAI 2020) — in the fastMRI repo.
- **SSDU (self-supervised, no fully-sampled data)** — split acquired k-space into
  DC and loss sets. Yaman et al., *MRM* 2020. Code:
  https://github.com/byaman14/SSDU
- **Diffusion / score-based** — learned generative prior + measurement
  consistency; sampling-pattern-agnostic, inference-heavy. Chung & Ye, *MedIA*
  2022 (https://github.com/hyungjin-chung/score-MRI); Jalal et al., NeurIPS 2021
  (https://github.com/utcsilab/csgm-mri-langevin).
- **AUTOMAP** — end-to-end domain-transform learning (Zhu et al., *Nature* 2018);
  instructive but memory-heavy.

## Frameworks & building blocks

- **DIRECT** — https://github.com/NKI-AI/direct — many baselines + training loops.
- **fastMRI** — https://github.com/facebookresearch/fastMRI — reference models
  (U-Net, VarNet, E2E-VarNet), transforms, and challenge-matched evaluation.
  **Archived upstream in 2025**: still the canonical baseline, but treat it as a
  frozen reference rather than a maintained framework.
- **ATOMMIC** — https://github.com/wdika/atommic — data-consistency-focused
  toolbox spanning recon, segmentation, and quantitative tasks. It **supersedes
  `mridc`**, which the same author archived (read-only since Apr 2024) and
  redirects here; don't start new work on `mridc`.
- **torchkbnufft** — https://github.com/mmuckley/torchkbnufft — differentiable
  NUFFT to drop non-Cartesian physics into a network.

## Data

**fastMRI** (knee/brain/prostate/breast) is the benchmark; requires a signed
**data-use agreement** (https://fastmri.med.nyu.edu). Fully-open alternative for
prototyping: mridata.org.

## Training & evaluation

- Select endpoints for the intended use before training/tuning. Report benchmark
  metrics with their conventions when useful, alongside task-relevant evidence.
  Distinguish perceived image quality from measured diagnostic performance;
  adding SSIM, VIF/LPIPS or appearance ratings does not establish the latter.
- **Split before anything is fitted.** Split by subject (or by volume when only one
  subject exists), tune on validation only, and touch the test set once at the end.
  Slices of the same volume in both training and test sets is leakage.
- **Same pipeline for every method and split.** Use one k-space normalization, one
  mask generator with recorded seeds, the same coil handling and the same test masks
  for the network and every baseline; normalize with statistics available at test
  time (for example from the undersampled data), not from the fully sampled target.
- **Fair classical baseline.** Compare against a tuned classical reconstruction
  (CG-SENSE or ESPIRiT with L1-wavelet, regularization tuned on validation) on the
  identical data and masks; hand its implementation to mri-reconstruction.
- **Metrics with conventions.** Compute NRMSE/PSNR/SSIM on magnitude images with the
  same scaling and within a stated region; state the data range used for PSNR/SSIM
  and report per-subject values with spread. On CPU, prefer small unrolled models
  with few cascades, and check data consistency of the output.
- **Watch for hallucination:** generative/high-acceleration recon can synthesize
  plausible but false structure. Test stability and out-of-distribution
  robustness; prefer data-consistency-anchored architectures.

- **Name the shipping baseline.** Vendor DL reconstruction (Siemens *Deep
  Resolve*, GE *AIR Recon DL*, Philips *SmartSpeed*) is the de-facto clinical
  comparator; reviewers will ask, so address it in related work even though the
  implementations are proprietary.

## Hand-offs

- **Classical / training-free recon** — ESPIRiT, SENSE, GRAPPA, L1-wavelet PICS,
  NUFFT gridding, or "just get me an image from this k-space": use the
  `mri-reconstruction` skill, which executes BART/SigPy pipelines. You also want
  it for the *baseline* your network is compared against.
- **Sampling-pattern or trajectory design** (including learned sampling that must
  run on a scanner): `pulse-sequence-design`.
- **Theory, citations, and the wider landscape:** the `mri-research` hub.

Deeper reference:
../mri-research/references/recon-methods.md
