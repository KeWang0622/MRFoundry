---
name: mri-reconstruction
description: >-
  Read before turning MR data into images or parameter maps: raw k-space
  (Cartesian, radial, spiral, EPI; twix, ISMRMRD, numpy), GRAPPA/SENSE, coil
  combination, off-resonance correction, BART or SigPy, and T1, T2/EPG, T2*,
  water-fat (PDFF), ASL, DCE or QSM maps. Prevents silent errors in encoding
  sign, acceleration pattern, orientation, noise covariance and floor, water-
  fat swaps, timing origin and units. Ships tested numpy helpers and a finish
  check. Trained networks: deep-learning-recon; diffusion: diffusion-mri.
metadata:
  author: Ke Wang
  version: "0.14.0"
---

# MRFoundry: MRI Reconstruction and Quantitative Maps

Do the work with the tested helpers below instead of re-deriving their maths; open only the row you need.
Hand-written versions of these steps failed silently in evaluation runs.

## Route

| Task | Use (`scripts/`) | Read only if needed |
|---|---|---|
| Undersampled multi-coil Cartesian: R, offset and ACS from the mask, GRAPPA, CG-SENSE, prewhitening, coil combination, SNR units | `mrfoundry_rawrecon.py`: `sampling_pattern`, `grappa_from_mask`, `sense_combine`, `prewhiten` | [raw-data checklist](references/raw-data.md) |
| Non-Cartesian (radial, spiral): exact forward model, NUFFT least squares; off-resonance with a field map | `mrfoundry_reconlib.py`: `offres_least_squares`, `smooth_field` | [raw-data checklist](references/raw-data.md#non-cartesian) |
| Water-fat separation, PDFF, R2* (multi-echo GRE, multi-peak fat) | `fatwater_lib.py`: `fat_offsets_hz`, `fit_fat_water`, `fat_fraction` | [quantitative maps](references/quantitative-maps.md#water-fat) |
| BART or SigPy pipelines; twix, ISMRMRD, `.cfl` files | `bart_recon.sh` | [BART and SigPy](references/bart-sigpy.md) |
| T1, T2, T2*, VFA, dictionaries, multi-echo spin echo with B1 (EPG) | `qmri_fit.py` | [quantitative maps](references/quantitative-maps.md) |
| ASL CBF and arrival time, single or multiple delays | `qmri_fit.py`: `asl_pairs_by_delay`, `slice_delays`, `asl_effective_efficiency` (background suppression), `m0_finite_tr`, `asl_cbf_pcasl`, `fit_asl_multidelay` | [ASL](references/quantitative-maps.md#asl) |
| DCE: signal to concentration, extended Tofts | `qmri_fit.py`: `spgr_concentration`, `fit_tofts` | [DCE](references/quantitative-maps.md#dce) |
| QSM: phase to field, background removal, dipole inversion, reference region | `qsm_lib.py`: `run_pipeline` (`phase_misfit_fraction` < 0.01; `--selftest` with your acquisition must PASS) | [QSM](references/quantitative-maps.md#qsm) |
| Fixed settings of a fitted model (nuisance values, spectra, fractions) | | [model calibration](../mri-research/references/model-calibration.md) |
| One-file standalone entrypoint | `python .agents/skills/mri-research-workflow/scripts/inline_helpers.py <module.py> <functions> --into <entrypoint.py>` copies the tested helpers | |

Import with `sys.path.insert(0, '.agents/skills/mri-reconstruction/scripts')`. `python <module>.py --api` prints the
signatures (do not read the sources); `scripts/test_<module>.py` has worked examples. Never retype a helper into a
standalone entrypoint: copy it with `inline_helpers.py` (a retyped GRAPPA took the wrong acceleration factor from
the mask and still gave plausible maps).

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
   noise; `metric=` the endpoint error when the deliverable is a parameter map): exact data consistency is not
   image quality; at R >= 3 it keeps or amplifies noise.
5. **Fits**: use the stated model and time origin. Multi-echo magnitude at low SNR: combine coils with the SAME
   phase-preserving weights for every echo (`sense_combine`), then pass `noise_sigma` (and `n_channels` for RSS)
   to `fit_monoexp` or `fit_dictionary`; an RSS log-linear fit overestimates T2 by several percent. Water-fat:
   `fit_fat_water` chooses among field-map candidates with a smooth field (voxelwise minima swap water and fat
   in isolated high-fat regions), then `fat_fraction(water_real, fat_real, flip, TR, T1w, T1f, b1)`. Check map
   units against expected ranges (`finish_check.py --range`).
6. **Standalone entrypoints** read every protocol value (matrix, coils, acceleration, delays, echo times,
   field strength, slice timing, frame times, scale factors) from the inputs; run them on a second simulated
   input with OTHER values (another acceleration, field strength or echo train) before finishing.

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
