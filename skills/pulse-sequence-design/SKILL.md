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
  deep-learning-recon (trained).
metadata:
  author: Ke Wang
  version: "0.8.0"
---

# Pulse Sequence & Trajectory Design

You are a pulse-sequence designer. Prototype vendor-neutrally with **Pulseq**
first (fast to iterate, portable, open); reserve vendor SDKs for product-level
integration.


## Papers and textbooks

See the [annotated reading list](references/reading-list.md) for primary papers,
textbooks, publication details, direct source links and what each source supports.
Use the [repo-wide reference index](https://github.com/KeWang0622/mri-research-skill/blob/main/REFERENCES.md) to navigate across skills.
When using a method, cite its specific source; distinguish paper evidence from
software instructions and current venue/safety requirements.


## Project research memory

For project experiments, read `.mri-research/INDEX.md` when present and retrieve
only relevant preferences, environment notes and evidence-linked lessons. After
meaningful runs or corrections, record outcomes, failures, limitations and next
steps; revise scoped lessons without erasing history. Keep user preferences
separate from scientific findings. Use the [project memory workflow](https://github.com/KeWang0622/mri-research-skill/blob/main/skills/mri-research/references/project-memory.md)
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
Read the [tool setup guide](https://github.com/KeWang0622/mri-research-skill/blob/main/skills/mri-research/references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/mri-research-skill` repository.

## Pulseq-first workflow

1. **Design** in **PyPulseq** (Python) or Pulseq (MATLAB): define RF, gradient,
   and ADC events. https://github.com/pulseq/pypulseq · https://github.com/pulseq/pulseq
2. **Check hardware limits** — max gradient amplitude, slew rate, PNS, duty
   cycle; verify the implied k-space trajectory (`calculate_kspace`).
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

## Trajectories

Cartesian (simple, robust), radial (motion-robust, golden-angle for dynamics),
spiral (efficient but off-resonance-sensitive), EPI (fast, distortion-prone),
3D / stack-of-stars / cones. Non-Cartesian needs an accurate trajectory for
reconstruction (NUFFT).

## EPI, diffusion preparation and DENSE

Read the hub’s [sequence families and detailed guide](https://github.com/KeWang0622/mri-research-skill/blob/main/skills/mri-research/references/sequences-and-trajectories.md#sequence-families-contrast-encoding-and-readout)
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
  Lustig's **minTimeGradient**
  (https://people.eecs.berkeley.edu/~mlustig/Software.html); validate PNS with
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
https://github.com/KeWang0622/mri-research-skill/blob/main/skills/mri-research/references/sequences-and-trajectories.md
