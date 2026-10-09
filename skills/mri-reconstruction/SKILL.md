---
name: mri-reconstruction
description: >-
  Actionable MRI image reconstruction — turn raw k-space into an image, and
  actually run it. Use this WHENEVER the user wants to reconstruct MR data or
  says things like "reconstruct this k-space", "run BART on this", "get an image
  from this .cfl / .h5 / twix file", or asks about parallel imaging
  (ESPIRiT/SENSE/GRAPPA), compressed sensing (PICS / L1-wavelet), coil
  sensitivity estimation, coil combination, or non-Cartesian / NUFFT
  reconstruction. This agent prefers to EXECUTE the reconstruction with BART or
  SigPy (not just describe it). It covers classical/analytic reconstruction —
  for anything TRAINED (unrolled networks, VarNet, self-supervised, diffusion
  priors, fastMRI models) hand off to the deep-learning-recon skill. Triggers:
  k-space, coil sensitivities, ESPIRiT, PICS, undersampled reconstruction,
  radial/spiral recon, `.cfl`/`.hdr`, ISMRMRD, Siemens twix, GE P-file.
metadata:
  author: Ke Wang
  version: "0.8.0"
---

# MRI Reconstruction (actionable)

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
and the evidence needed to support it. Use the [evaluation and attribution guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/evaluation-and-attribution.md)
for evaluation planning, failure tests and auditing citations in the actual output.
Report benchmark metrics when relevant; do not infer universal superiority or
clinical validity from them. Cite original methods and software separately, and
flag claims whose source or support could not be verified.
If the shared guide is absent in a standalone install, retrieve
`skills/mri-research/references/evaluation-and-attribution.md` from the
[official repository](https://github.com/KeWang0622/MRFoundry).

## Project research memory

For project experiments, read `.mri-research/INDEX.md` when present and retrieve
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
  https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/recon-methods.md
  and tool details at
  https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/tools.md
