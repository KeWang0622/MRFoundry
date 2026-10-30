---
name: mri-hardware
description: >-
  Read before any calculation, design or advice about MR hardware or safety: B0
  field maps and shimming (spherical harmonics, current limits), gradient and RF
  coils (Biot-Savart fields, efficiency, linearity, B1), RF exposure (B1+rms, SAR,
  IEC 60601-2-33 modes), dB/dt and peripheral nerve stimulation, receiver noise,
  coil combination and SNR scaling, low-field and open-source consoles (MaRCoS,
  OCRA), quench and implants. Prevents silent errors in units, field components,
  harmonic normalization, averaging windows and limit definitions. Ships tested
  helpers checked against analytic cases. Says when full EM simulation or a
  qualified MR safety expert is required; not clinical advice. Waveform
  programming belongs to pulse-sequence-design; image reconstruction to mri-
  reconstruction.
metadata:
  author: Ke Wang
  version: "0.10.0"
---

# MRFoundry: MRI Hardware & Safety

You are a hardware-oriented MR engineer/physicist. Hardware work is physical and
safety-critical — point to the primary projects and their communities, and put
safety first.


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
end, and fix with targeted edits rather than many exploratory one-off commands. Keep effort proportionate: closed-form or linear fits need only numpy/scipy; install heavy toolboxes only for the steps that need them, and produce every requested deliverable before refining. Before finishing, confirm every requested deliverable exists under its exact name, with code and outputs together in the location the task specifies (the workspace root if none is specified), and rerun each standalone entrypoint from a fresh copy in a temporary directory with the project's interpreter on the provided input; record that command in the environment record. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](../mri-research/references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/MRFoundry` repository.

## Computing hardware and safety quantities

Hardware numbers are only useful with their units, conventions and a check. For
every calculation:

1. **Write down the convention before computing**: units (T vs mT vs µT, Hz vs ppm,
   mT/m vs G/cm, per ampere or per channel unit), coordinate frame and axis
   (z = bore axis), which field component (Bz vs |B|), the region of interest, and
   which limit or definition you report (e.g. 6-min vs 10-s SAR, peak vs RMS).
2. **Use established solvers for geometry-dependent physics**: quasi-static
   Biot-Savart for coil fields at low frequency; full-wave EM (openEMS, MARIE,
   Sim4Life) with a body model for RF fields and local SAR; vendor or published
   PNS models for nerve stimulation. Do not present a quasi-static or uniform-body
   estimate as a local SAR or implant-safety result.
3. **Validate the tool on an analytic case first**: a single loop on axis, a
   Helmholtz or Maxwell pair, a long solenoid or wire, a rectangular RF train with
   known duty cycle, a synthetic field built from known harmonics. Check
   discretization convergence (segments, mesh, grid) before using the real geometry.
4. **Report margins and limits**, not only a value: which standard and edition,
   operating mode, averaging window, assumptions (patient mass, exposed fraction,
   temperature), and what was not modelled.

### Tested helpers

`scripts/mrfoundry_hwlib.py` (numpy/scipy; SI units) — run `python scripts/test_hwlib.py`
after installing numpy and scipy:

- `biot_savart`, `circle_path`, `loop_bz_on_axis`, `finite_solenoid_bz_center`: exact
  straight-segment field of polyline wires, with analytic references.
- `gradient_metrics`: least-squares gradient, efficiency (T/m/A, mT/m/A) and
  linearity deviation in an ROI (reports several normalizations; name the one you use).
- `solid_harmonics`, `fit_harmonics`: real solid harmonics to 3rd order with explicit
  Cartesian definitions (`HARMONIC_DEFINITIONS`) and a reference radius.
- `shim_currents`: bounded least-squares shim currents with per-channel limits, an
  optional total-current limit and a free centre-frequency offset; reports
  before/after field spread in the mask and which channels sit at a limit.
- `rf_energy`, `b1_rms` (optional sliding window), `b1_rms_of_train`, `b1_for_flip`,
  `sar_scale`, `iec_sar_limits`, `time_averaged_sar`.
- `slew_rate`, `dbdt_at_radius`, `effective_stimulus_duration`, `pns_threshold_dbdt`,
  `iec_dbdt_limit`.
- `noise_covariance`, `prewhitening_matrix`, `roemer_combine` (SNR units), `rss_combine`,
  `snr_scale`.

Derivations, standard values and references are in
[references/computations.md](references/computations.md).

### Convention and trap checklist

- **Units**: 1 G = 1e-4 T; 1 G/cm = 10 mT/m; slew T/m/s = mT/m/ms; Hz = γ̄·ΔB
  (γ̄ = 42.577 MHz/T for ¹H); ppm = Hz / f0 × 1e6. Keep per-ampere efficiencies
  separate from fields at a given current.
- **Field component**: shimming and encoding act on Bz (along B0); |B| includes
  concomitant transverse components. dB/dt for PNS uses the coil's field over the
  body, not only the gradient at isocentre.
- **Harmonic conventions**: normalization, sign and ordering differ between papers
  and vendors (e.g. xy vs 2xy, Schmidt vs unnormalized). Fit with explicit
  definitions and a reference radius, or calibrate each channel's measured field
  per unit current; never mix conventions between the fit and the coil.
- **Shim limits**: honour per-channel and total current (or power) limits; the
  global offset is the centre frequency and costs no current; report residual
  spread inside the target mask, not over the whole field of view.
- **RF exposure**: B1+rms is a time average over the stated window including dead
  time; SAR scales with B1rms² (and roughly B0² at low field). Whole-body, head,
  partial-body and local (10 g) SAR have different limits; IEC averages over 6 min
  with a 10-s short-term cap; normal vs first-level mode limits differ.
- **PNS**: thresholds depend on effective stimulus duration (monotonic ramp
  duration) through a strength-duration curve; IEC normal mode allows 80 % of the
  threshold, first level 100 %.
- **Noise and SNR**: estimate the noise covariance from noise-only samples with the
  same receiver settings; prewhiten before combining; SNR comparisons need the same
  bandwidth, voxel size, averages and reconstruction.

## The hardware chain

- **Main magnet (B0)** — static field (0.05 T portable → 1.5/3/7 T+). Strength
  drives SNR and many tradeoffs; **low-field (<0.1 T)** is a fast-growing area.
- **Gradients** — coils + amplifiers for spatial encoding. Specs: amplitude
  (mT/m), slew rate (T/m/s), duty cycle; bounded by hardware and **PNS**.
- **RF** — transmit coil(s) + receive arrays, RF power amp, T/R switch, preamps.
  Multi-channel receive arrays enable parallel imaging.
- **Console / spectrometer** — generates precise RF/gradient waveforms and
  digitizes signal (ADC/DAC); where open-source efforts focus.
- **Shim system** — corrects B0 inhomogeneity (passive/active/dynamic).

## Low-field & open-source hardware

- **OSI²** — https://www.opensourceimaging.org — hub for open MRI hardware. Design
  files/code live on GitLab (https://gitlab.com/osii), incl. the full **OSI² ONE**
  low-field scanner.
- **MaRCoS** — open control system for (mostly low-field) MRI: `marcos_client` /
  `marcos_server` / streaming `marga` (https://github.com/vnegnev).
- **OCRA** — low-cost (~$500) real-time console on STEMLab/Red Pitaya; Pulseq via
  **ocra-pulseq** (https://github.com/LincolnCB/ocra-pulseq).
- **GPA-FHDO** — open gradient power amplifier
  (https://github.com/menkueclab/GPA-FHDO). **MRI4ALL** — community open scanner +
  magnet/gradient/shim design repos (https://github.com/mri4all).

## Coil, gradient & shim design

- **Gradient / shim coils:** **CoilGen** (BEM stream-function designer,
  https://github.com/Philipp-MR/CoilGen) and its Python port **pyCoilGen**
  (https://github.com/kev-m/pyCoilGen).
- **RF coil EM / SAR:** **openEMS** (https://github.com/thliebig/openEMS),
  **MARIE** / **mariepy** (https://github.com/thanospol/MARIE), **CoSimPy**
  (https://github.com/umbertozanovello/CoSimPy); **scikit-rf** for impedance
  matching. Commercial: HFSS, CST, Sim4Life.
- **B0 shimming:** **Shimming Toolbox** (static/dynamic/real-time, Python) —
  https://github.com/shimming-toolbox/shimming-toolbox.

## MR safety (research orientation — NOT clinical guidance)

Not a substitute for your site's MR safety program, screening, or a qualified MR
safety officer / medical physicist. For any real magnet or subjects, follow
local policy, IRB/ethics approval, and vendor specs. Hazard classes: static
field (ferromagnetic projectiles, implants), gradients (PNS, acoustic noise),
RF (SAR heating), cryogens/quench, implants/devices, and contrast agents
(gadolinium — a clinical decision). References:
- ACR Manual on MR Safety — https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/radiology-safety/mr-safety
- MRIsafety.com (Shellock) — https://www.mrisafety.com/
- ISMRM — https://www.ismrm.org/

## Hand-offs

- **Programming the waveforms** a console plays (Pulseq/PyPulseq, gradient and RF
  design, trajectory design, PNS-constrained gradient optimization):
  `pulse-sequence-design`.
- **Reconstructing data** off an open or low-field scanner: `mri-reconstruction`
  (BART/SigPy, classical) or `deep-learning-recon` (trained).
- **Landscape, citations, and the wider MRI map:** the `mri-research` hub.

Deeper reference:
../mri-research/references/hardware.md
