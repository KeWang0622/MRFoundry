---
name: mri-reconstruction
description: >-
  Read before turning MR data into images or parameter maps: raw k-space
  (Cartesian, radial, spiral, EPI; twix, ISMRMRD, .cfl, numpy), noise
  prewhitening, coil combination and SNR units, GRAPPA/SENSE/partial Fourier,
  BART or SigPy, and quantitative maps (T1, T2 with EPG/B1, T2*, ASL CBF/ATT, DCE
  Tofts, QSM). Prevents silent errors in encoding sign, orientation, noise
  covariance and scaling, label timing, convolution and units. Ships tested
  numpy helpers with self-tests and a finish check. Trained networks belong to
  deep-learning-recon, diffusion to diffusion-mri, spectroscopy to mri-research.
metadata:
  author: Ke Wang
  version: "0.11.0"
---

# MRFoundry: MRI Reconstruction and Quantitative Maps

Do the work with the tested helpers below; import them instead of re-deriving their maths. Open only the
row you need. Hand-written versions of exactly these steps failed silently in evaluation runs (a conjugated
noise covariance, a convolution missing the interval width, PLD used as time since label start, a bounded
solve left in scaled units).

## Route

| Task | Use (`scripts/`) | Read only if needed |
|---|---|---|
| Raw multi-coil k-space to image: prewhitening, readout oversampling, GRAPPA, CG-SENSE, partial Fourier, SNR units | `mrfoundry_rawrecon.py` | [raw-data checklist](references/raw-data.md) |
| Non-Cartesian (radial, spiral): exact forward model, NUFFT least squares | `mrfoundry_reconlib.py` | [raw-data checklist](references/raw-data.md#non-cartesian) |
| BART or SigPy pipelines; twix, ISMRMRD, `.cfl` files | `bart_recon.sh` | [BART and SigPy](references/bart-sigpy.md) |
| T1, T2, T2*, VFA, dictionaries, multi-echo spin echo with B1 (EPG) | `qmri_fit.py` | [quantitative maps](references/quantitative-maps.md) |
| ASL CBF and arrival time, single or multiple delays | `qmri_fit.py`: `asl_pairs_by_delay`, `m0_finite_tr`, `fit_asl_multidelay` | [ASL](references/quantitative-maps.md#asl) |
| DCE: signal to concentration, extended Tofts | `qmri_fit.py`: `spgr_concentration`, `fit_tofts` | [DCE](references/quantitative-maps.md#dce) |
| QSM: phase to field, background removal, dipole inversion, reference region | `qsm_lib.py`: `run_pipeline` | [QSM](references/quantitative-maps.md#qsm) |
| Fixed settings of a fitted model (nuisance values, spectra, fractions) | | [model calibration](../mri-research/references/model-calibration.md) |

Import with `sys.path.insert(0, '.agents/skills/mri-reconstruction/scripts')` (adjust if installed elsewhere).
`python .agents/skills/mri-reconstruction/scripts/qmri_fit.py --api` (or any module) prints every signature with a one-line summary (2-4 KB; reading the source costs
5-10 times more); `scripts/test_<module>.py` shows worked examples. Copy a helper into a standalone entrypoint
when the task requires one file.

## Checks that prevent silent errors

1. **Write the conventions down first**: axis order and which sample is k = 0, encoding sign
   (exp(-i2πk·r): `ifft2c`; exp(+i2πk·r): `image_from_kspace(ksp, encoding_sign=+1)`), readout oversampling,
   output grid [y, x], units and time origin of every input. Read protocol values from the file or sidecar.
2. **Validate with an independent forward model**: simulate a known asymmetric object or parameter set
   through your exact sampling and timing (`direct_dft_signed`, `direct_dft`, quadrature, analytic signals),
   then run your pipeline: `orientation_check(img, truth)` must return `('identity', (0, 0))` and parameters
   must come back. A round trip through your own transforms cannot reveal a sign, axis or timing error.
3. **Noise**: Psi = E[n n^H] from noise samples [coil, samples] (`noise_covariance`); scale it by
   noise dwell / imaging dwell (`scale_noise_covariance`); averaging N acquisitions divides it by N. SNR units:
   `snr_units_image`; confirm the real-part noise SD is 1 on a pure-noise or pseudo-replica run, never from
   low-magnitude pixels of the image.
4. **Choose the reconstruction by simulated error** (`rank_reconstructions` with your sampling and measured
   noise): exact data consistency is not image quality; at R >= 3 it keeps or amplifies noise.
5. **Fits**: use the stated model and time origin; for low-SNR magnitude data pass `noise_sigma` to
   `fit_dictionary`; check map units against expected ranges (`finish_check.py --range`).
6. **Standalone entrypoints** read every protocol value (matrix, coils, delays, echo times, slice timing,
   frame times, scale factors) from the inputs; run them once on a second simulated input with other values.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder>

Put the entrypoint and all outputs in the folder the task names (the workspace root if none). Fix every
FAIL line and rerun the check. Report numbers read back from the saved outputs.

## Setup and scope

- Use the workspace interpreter (`.venv/bin/python` if present) and `-m pip install` only missing packages;
  numpy and scipy cover every helper here. Read the [tool setup guide](../mri-research/references/tool-setup.md)
  only if an install fails or you need BART, Julia or a GPU toolbox.
- Ongoing projects with `.mrfoundry/INDEX.md`: [project memory](../mri-research/references/project-memory.md).
  Citations: [reading list](references/reading-list.md); method evidence and claims:
  [evaluation guide](../mri-research/references/evaluation-and-attribution.md).
- Trained networks: `deep-learning-recon`. Acquisition design: `pulse-sequence-design`. Diffusion models:
  `diffusion-mri`. Spectroscopy: `mri-research` (`scripts/mrs_lib.py`).
