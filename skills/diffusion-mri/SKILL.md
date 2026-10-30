---
name: diffusion-mri
description: >-
  Read before fitting, converting or reporting any diffusion-weighted MRI result:
  ADC, DTI/DKI (FA, MD, eigenvectors), IVIM, NODDI, multi-compartment or spectrum
  signal fractions, CSD and tractography, and diffusion biomarker or repeatability
  studies. Prevents silent errors: b-vector frame conventions (FSL vs world) when
  reporting orientations, the wrong b-range for conventional ADC/DTI, noise-floor
  bias at high b, and biased or unstable fractions from uncalibrated model
  settings. Ships tested helpers (gradient-frame conversion with forward-phantom
  checks, closed-form tensor fit, noise floor, regularized and fixed-basis fits,
  calibration on development data, stratified recovery tests). Preprocessing with
  MRtrix3, FSL topup/eddy, DIPY and QSIPrep. Starts from reconstructed DWI;
  k-space reconstruction belongs to mri-reconstruction.
metadata:
  author: Ke Wang
  version: "0.10.0"
---

# MRFoundry: Diffusion MRI

You are a diffusion-MRI scientist. Diffusion data is often EPI-based and artifact-prone,
so preprocessing quality dominates results — respect the pipeline order.


## Papers and textbooks

See the [annotated reading list](references/reading-list.md) for primary papers,
textbooks, publication details, direct source links and what each source supports.
Use the [repo-wide reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md) to navigate across skills.
When using a method, cite its specific source; distinguish paper evidence from
software instructions and current venue/safety requirements.


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

## DWI, DTI and acquisition choices

Read [DWI and DTI](references/dwi-dti.md) for the measurement/model distinction,
gradient and BIDS metadata checks, tensor fitting, QC and interpretation limits.
DWI is acquired data; DTI is one model of it. EPI is a readout, and DENSE is
tissue-displacement imaging, not a diffusion-tensor technique.

## Typical pipeline

1. **Convert & organize** — DICOM→NIfTI with `dcm2niix` (keeps `.bval`/`.bvec`);
   organize as BIDS. Sanity-check the gradient table.
2. **Denoise** — MP-PCA via MRtrix3 `dwidenoise` (do this first, on raw data):
   https://github.com/MRtrix3/mrtrix3 (Veraart 2016, *NeuroImage*). DIPY offers
   Patch2Self (self-supervised).
3. **Gibbs ringing removal** — MRtrix3 `mrdegibbs`.
4. **Distortion + eddy + motion** — FSL **`topup`** (reversed phase-encode pairs)
   then **`eddy`** (retain its rotated b-vectors): https://fsl.fmrib.ox.ac.uk/fsl/docs/#/diffusion/eddy .
5. **Mask / bias field** — brain mask; N4 bias correction (ANTs).
6. **Model fitting** (below).
7. **Tractography / bundles** (below).

Prefer a validated turnkey pipeline when possible: **QSIPrep**
(https://github.com/PennLINC/qsiprep) — BIDS-native diffusion preprocessing +
QC. Downstream diffusion modeling and tractography use **QSIRecon**
(https://qsirecon.readthedocs.io/); this is distinct from raw k-space reconstruction.

## Models

- **DTI / DKI** — tensors → FA, MD, RD, AD (DTI); kurtosis (DKI). Fit with **DIPY**
  (https://github.com/dipy/dipy) or MRtrix3.
- **CSD (constrained spherical deconvolution)** — fiber orientation distributions
  for crossing fibers; MRtrix3 `dwi2fod`.
- **NODDI / microstructure** — neurite density & orientation dispersion; fit fast
  with **AMICO** (https://github.com/daducci/AMICO).

## Signal-fraction and diffusivity-spectrum models

Multi-compartment fits (restriction spectrum imaging, NNLS diffusivity spectra,
IVIM-type and free-water models) are ill-conditioned: neighbouring diffusivities
trade off, so fractions can look precise and still be biased, usually most in the
tissue with the largest fraction.

- **Define the target** (for example, the signal fraction below a stated
  diffusivity) and make sure the model can represent it.
- **Default to a regularized spectrum** (nonnegativity plus smoothness or Tikhonov,
  with the weight chosen on development data) when compartment diffusivities are
  uncertain. An unregularized fine-grid NNLS spectrum gives unstable voxelwise fractions.
- **Calibrate before fixing a basis.** Follow the
  [model calibration procedure](../mri-research/references/model-calibration.md): fit
  candidate bases to pooled development ROI or tissue-class curves (`calibrate_basis`),
  compare residuals and residual patterns across b, and check identifiability (how far
  the target moves among candidates that fit equally well). Do not copy diffusivities
  from examples, other organs, field strengths or protocols.
- **Stratified recovery test** (`stratified_recovery_test`): simulate at the actual
  b-values, directions and noise level, with truth parameters for each compared group
  taken from development fits and a generative model that differs from the fitting
  basis. Report bias per group and per true-value bin and the estimate-versus-truth
  slope. A pooled bias near zero does not show that any one tissue is unbiased, and
  choosing by pooled RMSE over a broad prior selects the prior's centre.
- **Noise floor**: estimate sigma from background or repeats; use a Rician-aware fit
  or floor correction at high b and report residual bias.
- **Tools.** [`scripts/spectrum_fit.py`](scripts/spectrum_fit.py): `background_sigma`,
  `floor_correct`, `fit_weights` (NNLS, optional Tikhonov/smoothness), `fit_fixed_basis`,
  `calibrate_basis`, `fraction_below`, `stratified_recovery_test`, `adc_fit`;
  `scripts/test_spectrum_fit.py` shows a misplaced fixed atom biasing high-fraction
  tissue and calibration correcting it.
- **ADC convention.** Conventional ADC is a mono-exponential fit over b <= 1000 s/mm^2
  (b = 0 plus the low shells); higher shells lower ADC through kurtosis/restriction.
  Use `adc_fit(signals, bvals, bmax=1000)` unless the study defines another range, and
  state the range.
- **Biomarker comparison studies** (group differences, test-retest): summarize each ROI
  per subject and session; declare the statistical unit for every endpoint; make all
  model, threshold and setting choices on development subjects only; follow the
  study's analysis plan where given; use `mri-research-workflow` statistics and
  deliverable checkers, and recompute every reported number from the saved maps.

## Gradient tables and coordinate frames

Treat the gradient-table frame as a rule to apply, then verify it independently:

- **Frames.** World coordinates are those of the NIfTI affine; array-axis components
  are what a voxelwise fit on the data array uses; **FSL bvecs are array-axis
  components with the x component negated when det(affine[:3, :3]) > 0**; MRtrix3
  `-grad` tables are in world coordinates. `eddy` writes rotated bvecs in the FSL convention.
  Check which frame each library expects before passing a table to it.
- **Fit in one declared frame** and report orientations in world coordinates: rotate
  array-frame eigenvectors with the affine's direction cosines.
  [`scripts/gradient_frames.py`](scripts/gradient_frames.py) provides `array_from_fsl`,
  `fsl_from_world`, `world_from_array` and a closed-form `fit_tensor_lls` (numpy only, so a
  log-linear DTI fit needs no toolbox installation).
- **Verify with an independent forward phantom**: simulate signals from world-frame
  gradients and a known fiber direction (`simulate_tensor_signal`), pass them through
  your actual file conversion and fit, and confirm the reported world direction. A
  check that reuses your own conversion in both directions cannot detect a convention
  error. Do not fix a suspected flip by trial and error on the result.

## Tractography & bundles

- **MRtrix3** — probabilistic tractography (`tckgen`, iFOD2), ACT, SIFT2,
  fixel-based analysis; the modern standard.
- **DIPY** — deterministic/probabilistic tractography in Python.
- **FSL FDT** — `bedpostx`/`probtrackx` probabilistic tracking.
- **TractSeg** (https://github.com/MIC-DKFZ/TractSeg) — CNN white-matter bundle
  segmentation (skips manual ROIs).

## Vendor / acquisition notes

- Always keep the **`.bval`/`.bvec`** with the data; check b-vector orientation
  vs. image axes (a flipped bvec silently ruins tractography).
- For `topup` you need **reversed phase-encode** (blip-up/blip-down) acquisitions
  with suitable metadata. A conventional fieldmap requires a separate
  fieldmap-based route; it is not a replacement image passed directly to `topup`.
- Multi-shell (multiple b-values) enables DKI/NODDI/multi-tissue CSD.

## Hand-offs

- This skill starts from **reconstructed DWI volumes**. If the user has raw
  k-space (twix/ISMRMRD/`.cfl`) and no images yet, `mri-reconstruction` gets them
  there first — including the EPI-specific caveat that EPI is Cartesian and needs
  regridding when ramp-sampled plus Nyquist-ghost correction; a
  NUFFT alone does not address these effects.
- **Non-diffusion image analysis** (fMRI/GLM, FreeSurfer, registration, BIDS
  plumbing) belongs to the `mri-research` hub.
- **Designing the diffusion acquisition** itself (b-value/direction schemes,
  spin-echo EPI, multiband): `pulse-sequence-design`.

Deeper reference (analysis tooling, formats):
../mri-research/references/analysis-processing.md
