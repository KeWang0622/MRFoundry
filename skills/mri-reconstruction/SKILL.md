---
name: mri-reconstruction
description: >-
  Read before turning MR data into images or parameter maps: Cartesian and non-
  Cartesian (radial, spiral, NUFFT) reconstruction, coil sensitivities and
  combination, noise prewhitening, SENSE/GRAPPA/ESPIRiT, partial Fourier,
  compressed sensing with BART or SigPy, g-factor and SNR, and relaxometry or
  parameter fitting (T1, T2, T2*, VFA, dictionaries) on simulated or scanner data.
  Prevents silent errors in k-space centring and FFT scaling, readout
  oversampling, ACS and sampling patterns, image orientation, noise-floor bias and
  signal-model mismatch. Ships tested helpers for raw-data reconstruction and
  quantitative fitting. Inputs include .cfl, ISMRMRD/.h5, twix, P-files and numpy
  arrays. Trained networks belong to deep-learning-recon; acquisition design to
  pulse-sequence-design.
metadata:
  author: Ke Wang
  version: "0.10.0"
---

# MRFoundry: MRI Reconstruction (actionable)

You are a reconstruction engineer: given k-space, produce an image — and run the
pipeline, don't just talk about it. Default to **BART** (battle-tested, CLI,
scriptable); use **SigPy** when the user is in Python. Confirm the data before
running, then execute and inspect.


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
end, and fix with targeted edits rather than many exploratory one-off commands. Keep effort proportionate: closed-form or linear fits need only numpy/scipy; install heavy toolboxes only for the steps that need them, and produce every requested deliverable before refining. Before finishing, confirm every requested deliverable exists under its exact name, with code and outputs together in the location the task specifies (the workspace root if none is specified), and rerun each standalone entrypoint from a fresh copy in a temporary directory with the project's interpreter on the provided input; record that command in the environment record. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](../mri-research/references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/MRFoundry` repository.

## Workflow

**0. Identify the k-space format** (ask or inspect). BART works in its own
`.cfl`/`.hdr`, so other formats need a conversion step:
- **BART `.cfl` + `.hdr`** — native; dims must be `[X Y Z COILS ...]` (coils on
  dim 3). Ready to use.
- **Siemens twix `.dat`** — `bart twixread -A meas.dat ksp` writes a `.cfl`
  (`-A` auto-guesses the dimensions; without it you must supply them explicitly
  via `-x/-y/-z/-c/-s/-n`, and a flagless call will not work). Then confirm with
  `bart show -m ksp`. Alternative: read in Python with `twixtools`/`pymapVBVD`
  and write a `.cfl`.
- **NumPy array** — write a `.cfl` with BART's Python helper:
  `PYTHONPATH=$TOOLBOX_PATH/python python -c "import cfl; cfl.writecfl(name, arr)"`
  (`cfl.py` ships in BART's `python/` directory — it is not on PyPI, and the
  unrelated `bartpy` package on PyPI is a decision-tree library, not this).
  Make sure coils land on dim 3.
- **ISMRMRD `.h5`** — BART *has* an `ismrmrd` tool, but it is a build-time
  option: the Makefile defaults to `ISMRMRD=0`, so a stock build has no
  `bart ismrmrd` command. Check with `bart ismrmrd -h`; if it's missing, either
  rebuild BART with `ISMRMRD=1` (needs the ISMRMRD C++ library) or read the file
  with the Python `ismrmrd` package and `cfl.writecfl`. Vendor raw → ISMRMRD
  first via `siemens_to_ismrmrd` / `ge_to_ismrmrd` / `philips_to_ismrmrd`.

**1. Estimate coil sensitivities (ESPIRiT):**
```
bart ecalib -m1 -r 24 kspace sens
```
`-m1` matters: `ecalib` computes **two** ESPIRiT map sets by default, and `pics`
then returns a soft-SENSE result with a size-2 MAPS dimension instead of a single
image — a silent wrong answer. `-r` caps the auto-extracted calibration region
(24³ is already the default; lower it if your ACS is smaller).

**2. Reconstruct:**
```
# Fully sampled: inverse FFT + coil combine
bart fft -iu 7 kspace img_coils && bart rss 8 img_coils img

# Undersampled — parallel imaging + compressed sensing (the workhorse):
bart pics -l1 -r 0.01 kspace sens img     # l1-wavelet regularized
```
- **Non-Cartesian** (radial/spiral/cones/rosette): you also need the trajectory.
  Use `bart pics -t traj kspace sens img`. For calibration, grid with the
  **inverse** NUFFT (`bart nufft -i`), not the adjoint (`-a`) — the adjoint
  leaves the sampling density in the data and biases the ESPIRiT maps. Get the
  trajectory from the sequence/ISMRMRD, or `bart traj` for nominal.
- **EPI is Cartesian.** Its zig-zag traversal still samples a Cartesian grid, so
  do *not* reach for a trajectory/NUFFT. EPI needs ramp-sampling regridding and
  Nyquist-ghost / phase correction first, then the Cartesian path above;
  geometric distortion is corrected downstream (topup/FUGUE).

**3. Inspect:** check image dimensions, scaling, orientation, measurement
residuals and coil-combination errors. Investigate aliasing and over-smoothing
with calibration/model checks and a documented regularization sweep; raising
`-r` is not a universal fix. For method comparisons, use the evaluation guide
above and assess task-relevant feature preservation as well as image metrics.

## Runnable helper

`scripts/bart_recon.sh <kspace_cfl> <output_cfl> [l1_reg] [traj_cfl]` runs an
ESPIRiT → PI+CS pipeline on a BART `.cfl` k-space file. It **assumes Cartesian
data with coils on dim 3 and a fully-sampled ACS** (calibration region); pass a
**trajectory `.cfl`** as the 4th argument for genuinely non-Cartesian sampling
(radial/spiral/cones/rosette — not EPI, which is Cartesian). It warns about these
assumptions but can't fully verify them — check the header and adapt the
regularization / calibration size to the data.

## Tested conventions (Python)

[`scripts/mrfoundry_reconlib.py`](scripts/mrfoundry_reconlib.py) fixes conventions that break
reconstructions silently: `cartesian_image` (centred inverse FFT; sample n//2 is k = 0; image
[y, x]), `direct_dft` (forward model for checks) and `nufft_least_squares` (SigPy coordinates
ordered (ky, kx) times FOV; output rescaled to the direct-sum model).
`python scripts/test_reconlib.py` verifies them against a direct DFT.


## Acquired-data conventions and checks

Most silent failures with acquired or vendor-style k-space are conventions, not
algorithms. Before reconstructing, establish and record:

- **Layout**: axis order (coil, ky, kx), which axis is the readout, and where k = 0
  sits. Asymmetric echoes and partial Fourier move the peak: locate the k-space
  maximum instead of assuming n//2.
- **Readout oversampling** (often 2x): crop the central field of view after the
  readout transform (`remove_readout_oversampling`) before comparing with a
  nominal matrix.
- **Noise**: estimate the covariance from the noise scan and prewhiten noise,
  calibration and imaging data with the same matrix before ESPIRiT, GRAPPA or SENSE.
- **Sampling**: acceleration, which lines were acquired (offset), ACS lines
  (integrated or separate), partial-Fourier coverage. Keep acquired samples
  unchanged; fill missing lines with GRAPPA/SENSE and asymmetric coverage with
  POCS or homodyne rather than reporting zero-filled blur as final.
- **FFT and scaling**: centred orthonormal transforms (`fft2c`/`ifft2c`, as in SigPy)
  differ from numpy's unnormalized `ifft2` by a constant. State the intensity scale,
  use the same coil combination as the reference (RSS vs sensitivity-weighted),
  and say whether an error metric fits a scale (`nrmse`).
- **Encoding sign**: the standard model is s(k) = Σ m(r) exp(−i2πk·r), reconstructed by a
  centred inverse FFT; some vendors and simulators use exp(+i2πk·r), which needs the forward
  transform (`image_from_kspace(ksp, encoding_sign=+1)`). The wrong choice mirrors the image in
  both axes and shifts it by one pixel for even matrices. Take the sign from the documentation.
- **Orientation**: confirm row/column order and flips against an asymmetric feature,
  a provided reference or header geometry; fft-for-ifft or a missing shift mirrors
  or rolls the image.
- **Standalone entrypoints**: read acceleration, ACS, oversampling, partial-Fourier
  and noise information from the file or header, never from constants tuned to one
  dataset, and rerun the script on a second (or simulated) dataset.
- **Validate first, with an independent forward model**: simulate k-space from a known,
  asymmetric image and smooth coil maps using the signal equation exactly as documented
  (sign, centring, scaling; `direct_dft_signed` is an explicit sum, not an FFT), apply your
  sampling and conventions, and confirm the pipeline recovers it. A round trip through your
  own FFT helpers cannot detect a sign, shift or axis-order error. Report the SNR cost of
  acceleration with a g-factor or pseudo-replicas.

[`scripts/mrfoundry_rawrecon.py`](scripts/mrfoundry_rawrecon.py) (numpy only; `python scripts/test_rawrecon.py`):
`fft2c`/`ifft2c`, `image_from_kspace` and `direct_dft_signed` (encoding sign), `rss`, `noise_covariance`, `prewhiten`, `remove_readout_oversampling`,
`grappa_2d` (Tikhonov-regularized 2-line kernel from ACS), `pocs_partial_fourier`,
`sense_cg` (Cartesian CG-SENSE), `pseudo_replica` (noise maps, g-factor) and `nrmse`.
Prefer BART or SigPy for production reconstructions; the helpers make conventions
explicit and serve as checks or small fallbacks.

## Quantitative maps from reconstructed images

[`scripts/qmri_fit.py`](scripts/qmri_fit.py) (tested, vectorized, no initial guesses): `fit_monoexp`
(T2/T2*), `fit_inversion_recovery` (3-parameter, complex or magnitude with polarity restoration),
`fit_vfa`, `fit_dictionary` (match to simulated signals when no closed form fits the exact timing) and
closed-form checks `ernst_signal`, `ir_signal`, `bssfp_signal` (Bloch fixed point). Test every fit on
simulated data with known parameters from your own exported sequence before reporting maps; check map
orientation ([y, x], no flips) against the known object. Also: `epg_cpmg` and `epg_t2_dictionary` (multi-echo spin echo with imperfect refocusing, where
stimulated echoes bias mono-exponential T2; fit T2 with B1 by dictionary), `asl_cbf_pcasl` and
`asl_cbf_pasl` (consensus single-compartment model: ΔM = control − label, equilibrium M0, result in
ml/100 g/min) and `tofts_concentration` / `fit_tofts_linear` (extended Tofts with the plasma input
Cp = Cblood / (1 − Hct); time units set the rate units). For fits with fixed nuisance settings, follow the
[model calibration procedure](../mri-research/references/model-calibration.md).

## SigPy (Python) alternative

```python
import sigpy as sp, sigpy.mri as mr
maps = mr.app.EspiritCalib(ksp).run()                     # coil maps
img  = mr.app.L1WaveletRecon(ksp, maps, lamda=0.01).run() # PI + CS
# non-Cartesian: build a NUFFT from coords, use mr.app.SenseRecon
```

## Guardrails

- Confirm the acceleration factor and sampling (Cartesian vs non-Cartesian)
  before choosing a method — the wrong forward model gives garbage.
- If BART isn't installed: https://codeberg.org/mrirecon/bart (source, active)
  with docs at https://mrirecon.codeberg.page/ — install and validate it when needed. If blocked, explain the
  limitation before switching to SigPy. Note the `github.com/mrirecon/bart` mirror is archived as of 2026.
- **Report the SNR cost, not just the image.** Acceleration R costs SNR by
  `g·√R`; quote a g-factor (or a pseudo-replica SNR estimate for GRAPPA/ESPIRiT/
  nonlinear recon) rather than implying R is free.
- **Stay in lane:** anything trained — unrolled networks, VarNet/MoDL, SSDU,
  diffusion priors, fastMRI baselines — belongs to the `deep-learning-recon`
  skill. Designing the *acquisition* or the trajectory belongs to
  `pulse-sequence-design`; this skill consumes a trajectory, it doesn't design one.
- For method theory and citations, see the hub:
  ../mri-research/references/recon-methods.md
  and tool details at
  ../mri-research/references/tools.md
