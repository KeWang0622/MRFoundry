---
name: diffusion-mri
description: >-
  Read before fitting, converting or reporting any diffusion-weighted MRI
  result: ADC, DTI/DKI (FA, MD, kurtosis, eigenvectors), IVIM, NODDI,
  multi-compartment or spectrum signal fractions, CSD and tractography, and
  diffusion biomarker or repeatability studies. Prevents silent errors:
  b-vector frames (FSL, vendor, world) when reporting orientations, b-values
  from vector norms, the b-range for conventional ADC/DTI, noise-floor bias, units,
  and biased or unstable fractions from uncalibrated model settings. Ships tested
  numpy helpers (frame conversion with forward-phantom checks, closed-form tensor
  fit, noise floor, regularized and fixed-basis fits, calibration, stratified
  recovery tests). Starts from reconstructed DWI.
metadata:
  author: Ke Wang
  version: "0.11.0"
---

# MRFoundry: Diffusion MRI

Use the tested numpy helpers; a closed-form log-linear DTI fit needs no toolbox installation. Open only the
row you need; `python .agents/skills/diffusion-mri/scripts/spectrum_fit.py --api` (or `gradient_frames.py`) lists signatures (do not cat the source).

## Route

| Task | Use (`scripts/`) | Read only if needed |
|---|---|---|
| Gradient tables, frames, DTI/DKI orientation, b-values | `gradient_frames.py`: `array_from_fsl`, `fsl_from_world`, `world_from_array`, `world_from_lps`, `bvals_bvecs_from_vectors`, `fit_tensor_lls`, `simulate_tensor_signal` | [DWI and DTI](references/dwi-dti.md) |
| ADC, signal fractions, diffusivity spectra, IVIM-type fits | `spectrum_fit.py`: `background_sigma`, `floor_correct`, `adc_fit`, `fit_weights`, `fit_fixed_basis`, `calibrate_basis`, `fraction_below`, `stratified_recovery_test` | [model calibration](../mri-research/references/model-calibration.md) |
| Preprocessing (denoise, Gibbs, topup/eddy), CSD, NODDI, tractography, QSIPrep | MRtrix3, FSL, DIPY, AMICO | [preprocessing and models](references/preprocessing-and-models.md) |
| Group comparisons, repeatability, cutoffs | `mri-research-workflow/scripts/study_stats.py` | `mri-research-workflow` |

## Checks that prevent silent errors

1. **Frames as a rule, then an independent test.** FSL bvecs are array-axis components with x negated when
   det(affine[:3, :3]) > 0; MRtrix3 `-grad` tables are world coordinates; vendor vector files state their own
   frame (for example patient LPS) and b-value encoding (b may scale with the squared vector norm). Fit in one
   declared frame and report orientations in world coordinates. Verify with `simulate_tensor_signal`: build
   signals from a known world fibre direction, pass them through YOUR conversion and fit, and confirm the
   reported direction. A check that reuses your conversion in both directions cannot detect a frame error.
2. **Conventional ADC/DTI use b <= 1000 s/mm²** (`adc_fit(signals, bvals, bmax=1000)`) unless the study says
   otherwise; DKI fits all shells including the higher ones.
3. **Units**: MD and ADC in mm²/s (brain tissue about 0.6e-3 to 1.0e-3, free water about 3e-3 at body
   temperature) or µm²/ms (x1000); b in s/mm². Check map medians with `finish_check.py --range` in the units
   the task asks for.
4. **Fractions and spectra are ill-conditioned**: default to a regularized spectrum with the weight chosen on
   development data; calibrate any fixed basis on pooled development curves (`calibrate_basis`) and check
   identifiability; never copy diffusivities from examples, other organs or protocols.
5. **Stratified recovery tests** (`stratified_recovery_test`): truth for each compared group from development
   fits, a generative model that differs from the fitting basis, the real b-values and noise. Choose settings
   by the worst group or bin RMSE, then confirm the worst bias and voxelwise stability (`retest_tol=` reports
   the fraction of voxels whose estimate changes between two noise realizations). A pooled bias near zero
   proves nothing about any one tissue.
6. **Noise floor** at high b: estimate sigma from background (`background_sigma`) and correct
   (`floor_correct`) or fit a Rician-aware model.
7. **Studies**: summarize per subject and session, declare the statistical unit for each endpoint, make every
   choice on development subjects only, and recompute every reported number from the saved maps.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder> \
        --range <md map>:<low>:<high>      # e.g. 0.0001:0.004 for MD in mm²/s

## Setup and scope

- Use the workspace interpreter (`.venv/bin/python` if present); numpy and scipy cover the helpers. Install
  DIPY, MRtrix3 or FSL only for steps that need them; see the [tool setup guide](../mri-research/references/tool-setup.md)
  if an install fails.
- Citations: [reading list](references/reading-list.md). Project notes (only with `.mrfoundry/INDEX.md`):
  [project memory](../mri-research/references/project-memory.md).
- Raw k-space: `mri-reconstruction`. Acquisition design: `pulse-sequence-design`. Non-diffusion image
  analysis: `mri-research`.
