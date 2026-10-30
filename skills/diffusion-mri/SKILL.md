---
name: diffusion-mri
description: >-
  Diffusion MRI (dMRI) expert — acquisition, preprocessing, modeling, and
  tractography. Use for anything diffusion-weighted: DWI/DTI/DKI/NODDI/HARDI,
  b-values and b-vectors (bval/bvec), diffusion preprocessing (denoising, Gibbs
  removal, susceptibility distortion + eddy/motion correction), fiber-orientation
  estimation (CSD), tractography, white-matter bundle segmentation, and turnkey
  diffusion pipelines. Tools: MRtrix3, DIPY, FSL (eddy/topup/FDT), AMICO (NODDI),
  TractSeg, QSIPrep. Also use for apparent diffusion coefficient (ADC) studies and multi-compartment or
  spectrum signal-fraction models such as restriction spectrum imaging (RSI), NNLS
  diffusion spectra and IVIM-type fits. Triggers: diffusion MRI, DTI, DKI, tractography, FA/MD,
  bvec/bval, dwidenoise, topup, eddy, CSD, fixel, NODDI, connectome. Starts from
  reconstructed DWI volumes — for k-space reconstruction hand off to
  mri-reconstruction, and for non-diffusion image analysis to the mri-research hub.
metadata:
  author: Ke Wang
  version: "0.9.0"
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

If only the legacy `.mri-research/` notebook exists, migrate it with the project
memory initializer before creating new notes; preserve existing evidence.
For project experiments, read `.mrfoundry/INDEX.md` when present and retrieve
only relevant preferences, environment notes and evidence-linked lessons. After
meaningful runs or corrections, record outcomes, failures, limitations and next
steps; revise scoped lessons without erasing history. Keep user preferences
separate from scientific findings. Use the [project memory workflow](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/project-memory.md)
to initialize the folder or connect project `CLAUDE.md` / `AGENTS.md`. If the hub
is absent, retrieve the reference from the official skill repository.

## Tool setup before execution

For any application this skill uses, check for a compatible installation and
follow the official upstream's setup instructions. Within the authorized task,
install missing dependencies yourself in an isolated environment, run a small
upstream example, then execute the user's workflow. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/tool-setup.md) when installing,
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
IVIM-type and free-water models) are ill-conditioned: neighbouring diffusivities trade
off, so fractions can be precise-looking and wrong.

- **Define the target** (for example, signal fraction below a stated diffusivity) and
  make sure the model can represent it; avoid basis diffusivities near the cutoff.
- **Keep the model well posed.** Use a few well-separated fixed compartments justified
  by the literature, or a regularized spectrum (nonnegativity plus smoothness/Tikhonov).
  An unregularized fine-grid NNLS spectrum gives unstable voxelwise fractions.
- **Run a recovery test before analysing real data.** Simulate signals at the actual
  b-values, directions and noise level (Rician magnitude) from plausible tissue models
  that are *not* the fitting basis (for example, continuous diffusivity distributions),
  fit them, and report bias, spread and correlation of the target quantity. Choose the
  basis and regularization with this test and development data; never by the size of
  the effect you hope to show or by test-set results.
- **Handle the noise floor** at high b (estimate sigma from background or repeats; use a
  Rician-aware fit or floor correction) and report residual bias with the results.

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
https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/analysis-processing.md
