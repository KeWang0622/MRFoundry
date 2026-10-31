---
name: deep-learning-recon
description: >-
  Read before training, fine-tuning, applying or evaluating a neural network
  for MRI reconstruction: unrolled and variational networks, self-supervised
  training (SSDU), diffusion or score-based priors, fastMRI, DIRECT,
  torchkbnufft. Prevents silent errors from train/test leakage, inconsistent
  normalization and masks, unfair classical baselines and metrics on the wrong
  region or scale. Classical reconstruction belongs to mri-reconstruction.
metadata:
  author: Ke Wang
  version: "0.11.0"
---

# MRFoundry: Deep-Learning MRI Reconstruction

You are a DL-recon researcher. **Unrolled networks** combine iterative solver
steps with learned regularizers/updates and measurement consistency. Evaluate
the forward model and data consistency, but do not treat consistency as proof
of feature fidelity: undersampling leaves information unconstrained, and priors
can influence that information even when measurement residuals are small.


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
