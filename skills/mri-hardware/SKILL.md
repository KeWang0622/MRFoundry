---
name: mri-hardware
description: >-
  MRI hardware and safety expert — magnets, gradients, RF coils, consoles /
  spectrometers, low-field and open-source systems, and MR safety. Use for
  hardware design or selection, low-field MRI, open-source consoles (MaRCoS,
  OCRA), RF/gradient coil design and EM simulation, shimming, and MR safety
  (SAR, PNS, implants, quench, contrast agents). Triggers: MRI hardware, gradient
  coil, RF coil, low-field MRI, MaRCoS, OCRA, spectrometer/console, shimming,
  SAR, PNS, quench, MR safety, B0/B1. Orientation only — not clinical advice.
  For waveform/sequence programming hand off to pulse-sequence-design, and for
  turning acquired k-space into images to mri-reconstruction.
metadata:
  author: Ke Wang
  version: "0.8.0"
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
https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/hardware.md
