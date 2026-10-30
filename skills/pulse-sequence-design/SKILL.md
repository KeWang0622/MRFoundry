---
name: pulse-sequence-design
description: >-
  MRI pulse-sequence and k-space trajectory design expert, vendor-aware. Use for
  designing or programming pulse sequences and gradient/RF waveforms, k-space
  trajectory design (Cartesian, radial, spiral, EPI, golden-angle), RF pulse
  design, SMS/multiband, sequence simulation, and vendor sequence development on
  Siemens (IDEA/ICE), GE (EPIC/Orchestra), and Philips (Paradise). Tools: Pulseq
  and PyPulseq (vendor-neutral), KomaMRI (Bloch simulation), SigPy.RF (RF design).
  Triggers: pulse sequence, Pulseq, PyPulseq, gradient waveform, slew rate, PNS,
  k-space trajectory, spiral/radial/EPI, diffusion encoding, DENSE, RF pulse, SLR, multiband/SMS, IDEA,
  EPIC, Orchestra, `.seq`. This skill designs the *acquisition*; to reconstruct
  the data it produces, hand off to mri-reconstruction (classical) or
  deep-learning-recon (trained). Also use for simulation studies that design a sequence, Bloch-simulate the exported file and reconstruct or fit maps: spoiled/multi-echo GRE, inversion recovery and T1 mapping, spin echo/CPMG T2, balanced SSFP; ships a tested exported-sequence checker (TE/TR/TI, spoiling, receive phase, balanced moments, slice selection, sampling) and an end-to-end example pipeline.
metadata:
  author: Ke Wang
  version: "0.10.0"
---

# MRFoundry: Pulse Sequence & Trajectory Design

You are a pulse-sequence designer. Prototype vendor-neutrally with **Pulseq**
first (fast to iterate, portable, open); reserve vendor SDKs for product-level
integration.


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
separate from scientific findings. Use the [project memory workflow](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/project-memory.md)
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
end, and fix with targeted edits rather than many exploratory one-off commands. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/MRFoundry` repository.

## Pulseq-first workflow

1. **Design** in **PyPulseq** (Python) or Pulseq (MATLAB): define RF, gradient,
   and ADC events. https://github.com/pulseq/pypulseq · https://github.com/pulseq/pulseq
   Start from the tested helpers in [`scripts/mrfoundry_seqlib.py`](scripts/mrfoundry_seqlib.py):
   system limits, slice-selective excitation, readout with a chosen sample exactly at k = 0,
   exact TE/TR delays, wrapped RF spoiling, and `simulate_with_koma` (KomaMRI through
   komamripy, returning samples in ADC order with k-space and times). Single-echo Cartesian
   and radial examples are in [`scripts/test_seqlib.py`](scripts/test_seqlib.py). Setup:
   `pip install pypulseq sigpy komamripy`; the first komamripy call (not the import) installs Julia and
   compiles KomaMRI (about 3.5 min the first time on a fresh depot, about 10 s afterwards;
   measured with komamripy 0.0.14 / KomaMRI 0.14), so run `python scripts/test_seqlib.py` in the background early.
   Use these instead of reading library source to learn the APIs.
2. **Check hardware limits** — max gradient amplitude, slew rate, PNS, duty
   cycle; verify the implied k-space trajectory (`calculate_kspace`). Then verify
   the *exported* file against every requested parameter (next section).
3. **Simulate** with **KomaMRI** (GPU Bloch, Pulseq-compatible):
   https://github.com/JuliaHealth/KomaMRI.jl — install Julia/KomaMRI or its official
   Python interface `komamripy`, run an upstream example, then feed the exported
   `.seq` + phantom to the simulator and inspect the signal. Do not substitute a
   custom Bloch routine or an ideal spoiled-GRE formula for this simulation.
4. **Export** a `.seq` file → play via the vendor's Pulseq interpreter (on **GE**,
   **TOPPE** — https://github.com/toppeMRI/toppe). New to Pulseq? The
   **MR-Physics-with-Pulseq** tutorials
   (https://github.com/pulseq/MR-Physics-with-Pulseq) are the best on-ramp.
5. **Reconstruct** the acquired raw data (convert to ISMRMRD, then hand to the
   `mri-reconstruction` agent).

## Fast path for a simulation study (sequence -> Bloch -> reconstruction -> map)

1. Setup: `pip install pypulseq sigpy komamripy matplotlib`, then start `python scripts/test_seqlib.py` in the
   background: its first KomaMRI call installs and compiles Julia (about 3.5 min, once).
2. Copy [`scripts/example_pipeline.py`](scripts/example_pipeline.py): a tested end-to-end chain (build, check the
   read-back file, waveform figure, KomaMRI simulation of the exported file, archive with hashes, standalone
   reconstruction from the archive, orientation check, report). Swap in a family builder: spoiled GRE in
   `scripts/test_seqlib.py`; inversion-recovery GRE, balanced SSFP and spin echo in `scripts/test_check_exported_seq.py`.
3. Run `python scripts/check_exported_seq.py sequence.seq` with EVERY requested parameter as an expectation
   (flags below) and fix the build until all lines PASS before simulating.
4. Put samples on the grid with `kspace_grid` (it uses the exported k, so line order and polarity cannot be
   mixed up), fit maps with `mri-reconstruction/scripts/qmri_fit.py`, and check orientation and values against
   the known object. Report values measured from the export.
5. One script per stage with built-in checks; keep printed output short (it is re-read on every turn).

## Verify the exported sequence, not the design script

A sequence that runs, simulates and reconstructs can still be the wrong sequence. Treat the build script as a
claim and the exported `.seq` as the evidence: read it back and measure each requested property.
[`scripts/check_exported_seq.py`](scripts/check_exported_seq.py) classifies RF pulses (set `use='excitation'`,
`'refocusing'` or `'inversion'` on every pulse; `calculate_kspace` also relies on it) and prints PASS/FAIL per item.

- **All families.** TE = excitation RF centre (`pp.calc_rf_center`) -> ADC sample at k = 0, per echo; TR =
  excitation-centre spacing. Insert delays on the block raster so realized values equal the request; never
  let blocks collapse to a minimum TE. `--te --tr --flip --max-grad --max-slew`.
- **Slice selection.** A slice prescription needs a sinc/SLR pulse played with its slice-select gradient,
  then the rephaser; check flip from RF area and the small-tip slice FWHM. A hard pulse is non-selective.
  `--slice-thickness`.
- **Spoiled GRE.** Quadratic RF spoiling `inc = (inc + 117) % 360; phase = (phase + inc) % 360` (wrap both);
  every ADC gets the phase of its own excitation; spoiler after the last ADC of each TR, stated in cycles per
  slice/voxel: `--rf-spoil 117 --min-spoil-cycles 2`. Multi-echo: TE per echo; monopolar readouts need a
  flyback between echoes (`--monopolar`).
- **Inversion recovery.** TI = inversion RF centre -> excitation RF centre (not block starts); spoil the
  transverse magnetization after the inversion; state the inversion repetition time. Recovery is often
  incomplete: fit a + b exp(-TI/T1) (3 parameters; magnitude data need polarity restoration) or fit a
  simulation of the exact timing (`qmri_fit.fit_dictionary`), and test the fit on simulated known T1:
  `--ti ... --min-inversion-spoil-cycles 2`.
- **Spin echo / TSE.** Refocusing centre at TE/2 after the excitation centre (echo spacing for trains);
  CPMG refocusing phase = excitation phase +/- 90 deg; crushers equal on both sides: `--te --cpmg`.
- **Balanced SSFP.** Zero net gradient area between consecutive excitation centres on x, y and z: slice
  rephaser after the pulse and again before the next one, phase-encode rewinder, readout rewinder. TE = TR/2.
  0/180 RF phase cycling with the ADC phase following the RF. Steady state needs preparation (alpha/2 -
  TR/2 catalyzation or enough dummy TRs): verify by simulating and comparing early and late lines with
  `qmri_fit.bssfp_signal`: `--balanced --rf-phase-cycle 180 --te-half-tr`.
- **Sampling.** Check the k = 0 sample index, line set/order, polarity and 1/FOV spacing against any sampling
  contract: `--matrix NX NY --fov F`. Reconstruct with image axes oriented like the object ([y, x]) and
  verify on a simulated asymmetric object before trusting maps.
- **Report measured values** (TE/TR/TI/flip/slice width/spoiling/moments) from the read-back file, not the
  numbers typed into the build script; state any mismatch.

## Trajectories

Cartesian (simple, robust), radial (motion-robust, golden-angle for dynamics),
spiral (efficient but off-resonance-sensitive), EPI (fast, distortion-prone),
3D / stack-of-stars / cones. Non-Cartesian needs an accurate trajectory for
reconstruction (NUFFT).

## EPI, diffusion preparation and DENSE

Read the hub’s [sequence families and detailed guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/sequences-and-trajectories.md#sequence-families-contrast-encoding-and-readout)
for GRE, SE/FSE, inversion recovery, bSSFP, EPI and DENSE. Keep contrast,
readout and fitted models distinct. Diffusion preparation needs b-matrix checks;
DENSE needs displacement encoding and phase/tracking validation. Verify the
simulator supports diffusion or motion before claiming those effects were tested.
For DWI/DTI fitting and QC, use `diffusion-mri`.

## RF pulse design

**SigPy.RF** (`sigpy.mri.rf`): SLR, adiabatic, multiband, small/large-tip, and
parallel-transmit (pTx) pulses. Also **pulpy**
(https://github.com/jonbmartin/pulpy, Python RF/gradient design),
**Spectral-Spatial-RF-Pulse-Design**
(https://github.com/LarsonLab/Spectral-Spatial-RF-Pulse-Design), **Multiband-RF**
(https://github.com/mriphysics/Multiband-RF), and **kpTx**
(https://github.com/wgrissom/kpTx) for k-space pTx. Mind RF power / SAR for
high-flip or refocusing-heavy designs.

## SMS / multiband and controlled aliasing

Excite multiple slices at once; unalias with coil sensitivities. The trick in all
of these is to *shift* aliasing so coil sensitivities can separate it, buying back
g-factor:
- **Blipped-CAIPI** (SMS-EPI) — Setsompop K, Gagoski BA, Polimeni JR, Witzel T,
  Wedeen VJ, Wald LL. *Magn Reson Med* 2012;67(5):1210–1224.
  doi:10.1002/mrm.23097.
- **CAIPIRINHA** — the parallel-imaging ancestor of the idea (shifted phase-encode
  sampling across slices, then across partitions): Breuer FA, et al. *Magn Reson
  Med* 2005;53(3):684–691 (multi-slice, doi:10.1002/mrm.20401) and
  2006;55(3):549–556 (2D/volumetric, doi:10.1002/mrm.20787).
- **Wave-CAIPI** — corkscrew (sinusoidal Gy/Gz) readout spreads aliasing in all
  three directions for very high 3D acceleration at near-unity g-factor.
  Bilgic B, Gagoski BA, Cauley SF, et al. *Magn Reson Med* 2015;73(6):2152–2162.
  doi:10.1002/mrm.25347.

Product SMS sequences from CMRR: https://www.cmrr.umn.edu/multiband/

## Gradient optimization, GIRF & simulation

- **Time-optimal gradients:** **GrOpt** (https://github.com/mloecher/gropt) and
  [SigPy's **min_time_gradient**](https://sigpy.readthedocs.io/en/latest/generated/sigpy.mri.rf.min_time_gradient.html),
  which implements Lustig, Kim and Pauly's method (TMI 2008;
  doi:10.1109/TMI.2008.922699). Use the documented units; this is the SigPy
  implementation, not the former MATLAB/C download. Validate PNS with
  **safe_pns_prediction** (https://github.com/filip-szczepankiewicz/safe_pns_prediction).
- **GIRF (gradient impulse response):** **MRI-gradient/GIRF**
  (https://github.com/MRI-gradient/GIRF); Julia spiral recon with correction:
  **GIRFReco.jl** (https://github.com/BRAIN-TO/GIRFReco.jl).
- **Bloch / EPG simulation** (besides KomaMRI): **JEMRIS**, **MRiLab**,
  **sycomore**, **EPG-X** (EPG with MT/exchange), and **MRzero-Core**
  (differentiable Bloch + Pulseq for sequence optimization).

## Vendor environments (proprietary — engage your vendor research agreement)

- **Siemens** — **IDEA** (sequence build, C++) + **ICE** (recon). Pulseq
  interpreter available.
- **GE** — **EPIC** (sequence) + **Orchestra** (recon SDK). Pulseq interpreter
  available.
- **Philips** — **Paradise / GOAL-C** research pulse-programming. Pulseq
  interpreter available (more recent).
- Online/inline recon across vendors: **Gadgetron**
  (https://github.com/gadgetron/gadgetron), fed via ISMRMRD.

Steer method prototyping to Pulseq; use the native SDK only when you need vendor
integration or features Pulseq can't express.

## Hand-offs

- **Reconstructing what you just acquired** — classical (ESPIRiT/SENSE/GRAPPA,
  PICS, NUFFT gridding of your trajectory): `mri-reconstruction`, which runs
  BART/SigPy. Trained/unrolled/diffusion recon: `deep-learning-recon`.
- **Hardware limits, coils, consoles, SAR/PNS measurement:** `mri-hardware`.
- **Physics background and the citation trail:** the `mri-research` hub.

Deeper reference:
https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/sequences-and-trajectories.md
