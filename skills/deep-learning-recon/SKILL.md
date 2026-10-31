---
name: deep-learning-recon
description: >-
  Read before training, fine-tuning, applying or evaluating a neural network
  for MRI reconstruction: unrolled and variational networks, self-supervised
  training (SSDU), diffusion or score-based priors, fastMRI, DIRECT,
  torchkbnufft. Prevents silent errors from train/test leakage, inconsistent
  normalization and masks, unfair classical baselines and metrics on the wrong
  region or scale. Classical reconstruction belongs to mri-reconstruction;
  reviewing or writing a manuscript belongs to mri-research-workflow.
metadata:
  author: Ke Wang
  version: "0.12.0"
---

# MRFoundry: Deep-Learning MRI Reconstruction

You are a DL-recon researcher. **Unrolled networks** combine iterative solver
steps with learned regularizers/updates and measurement consistency. Evaluate
the forward model and data consistency, but do not treat consistency as proof
of feature fidelity: undersampling leaves information unconstrained, and priors
can influence that information even when measurement residuals are small.


Method families (VN, MoDL, E2E-VarNet, SSDU, score-based), frameworks (DIRECT, fastMRI, ATOMMIC, torchkbnufft)
and datasets with citations and licences: [methods, frameworks and data](references/methods-and-frameworks.md).

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
- **Quantitative endpoints** (R2*, T2, field, PDFF, ROI means): tune lambda, checkpoints and the method choice
  by the endpoint error on validation subjects (`rank_reconstructions(..., metric=endpoint_error)`), not by image
  NRMSE; use the structure shared across echoes or contrasts (all echoes as channels, joint or low-rank
  reconstruction); compute reported values from the exact saved reconstructions. A classical candidate whose
  tuning picks zero regularization is zero filling: widen the grid or use a stronger prior (TV, wavelets).
- **Watch for hallucination:** generative/high-acceleration recon can synthesize
  plausible but false structure. Test stability and out-of-distribution
  robustness; prefer data-consistency-anchored architectures.

- **Name the shipping baseline.** Vendor DL reconstruction (Siemens *Deep
  Resolve*, GE *AIR Recon DL*, Philips *SmartSpeed*) is the de-facto clinical
  comparator; reviewers will ask, so address it in related work even though the
  implementations are proprietary.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder>

## Setup, scope and hand-offs

- Use the workspace interpreter (`.venv/bin/python` if present); on CPU prefer small unrolled models with few
  cascades. Read the [tool setup guide](../mri-research/references/tool-setup.md) only if an install fails.
- Citations: [reading list](references/reading-list.md); evidence and claims:
  [evaluation guide](../mri-research/references/evaluation-and-attribution.md); theory:
  [recon methods](../mri-research/references/recon-methods.md). Project notes (only with `.mrfoundry/INDEX.md`):
  [project memory](../mri-research/references/project-memory.md).
- Classical reconstruction and the classical baseline (ESPIRiT, SENSE, GRAPPA, PICS, NUFFT), including
  `mri-reconstruction/scripts/mrfoundry_rawrecon.py` (`sense_cg`, `coil_maps_from_acs`, `rank_reconstructions`):
  `mri-reconstruction`. Sampling or trajectory design: `pulse-sequence-design`.
