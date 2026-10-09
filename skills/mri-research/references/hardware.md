# MRI hardware & the open-hardware community

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this when the user asks about MRI hardware — magnets, gradients, RF coils,
consoles/spectrometers — or about building/using low-field and open-source
systems. This is an orientation + pointers file; hardware work is deeply
physical and safety-critical, so route the user to the primary projects and
their communities.

## The hardware chain (what the pieces do)

- **Main magnet (B0)** — provides the static field (e.g., 0.05 T portable up to
  1.5/3/7 T clinical and research). Field strength drives SNR and many design
  tradeoffs. Low-field (< 0.1 T) is a fast-growing, accessible research area.
- **Gradient system** — coils + amplifiers that produce linear field variations
  for spatial encoding. Key specs: max amplitude (mT/m), slew rate (T/m/s),
  duty cycle; limited by hardware and by **PNS** (peripheral nerve stimulation)
  safety limits.
- **RF system** — transmit coil(s) for excitation and receive coil arrays for
  signal; RF power amplifier, T/R switch, preamps. Multi-channel receive arrays
  are what make parallel imaging possible ([`recon-methods.md`](recon-methods.md)).
- **Console / spectrometer** — generates RF/gradient waveforms with precise
  timing and digitizes the received signal (ADCs/DACs). This is where
  open-source consoles focus.
- **Shim system** — corrects B0 inhomogeneity (passive/active/dynamic shims).

## Open-source hardware community

- **Open Source Imaging Initiative (OSI²)** — https://www.opensourceimaging.org
  — the hub for open-source MRI hardware (consoles, coils, magnets, low-field
  systems), with a projects directory and community. Note: OSI² design files and
  code live on **GitLab** (https://gitlab.com/osii), including the complete open
  low-field scanner **OSI² ONE** (https://gitlab.com/osii/mri-scanners/osii-one).
  Overview: Winter L, et al. "Open-source magnetic resonance imaging: Improving
  access, science, and education through global collaboration." *NMR in
  Biomedicine* 2024;37:e5052.
- **MaRCoS** — MAgnetic Resonance COntrol System: open control for (mostly
  low-field) MRI; cycle-accurate sequences and arbitrary waveforms. Canonical
  repos: **marcos_client** (https://github.com/vnegnev/marcos_client),
  **marcos_server** (https://github.com/vnegnev/marcos_server), **marcos_extras**
  (https://github.com/vnegnev/marcos_extras); streaming successor **marga**
  (https://github.com/vnegnev/marga). System paper: Negnevitsky V, Vives-Gilabert
  Y, Algarín JM, et al. "MaRCoS, an open-source electronic control system for
  low-field MRI." *J Magn Reson* 2023;350:107424.
  doi:10.1016/j.jmr.2023.107424. For multi-site benchmarking of MaRCoS-driven
  scanners, see Guallart-Naval T, et al. *NMR in Biomedicine* 2023;36(1):e4825.
  doi:10.1002/nbm.4825.
- **OCRA** — low-cost (~$500) real-time console on the STEMLab/Red Pitaya (Zynq
  SoC, 125 Msps ADC/DAC). Pulseq interpreter: **ocra-pulseq**
  (https://github.com/LincolnCB/ocra-pulseq). Project page:
  https://www.opensourceimaging.org/project/ocra-open-source-console-for-real-time-acquisition/
- **Gradient power amplifier:** **GPA-FHDO** — open 4-channel GPA for low-field
  MRI: https://github.com/menkueclab/GPA-FHDO .
- **MRI4ALL** — community-built open scanner (Zeugmatron Z1): console software
  (https://github.com/mri4all/console) and magnet/gradient/shim design repos at
  https://github.com/mri4all .

Low-field + open hardware is the most active place for hands-on, buildable MRI
research; the OSI² projects directory is the best living index.

## Coil, gradient & shim design

- **Gradient / shim coil design:** **CoilGen** — BEM stream-function coil-layout
  generator (Amrein et al., *MRM* 2022): https://github.com/Philipp-MR/CoilGen ,
  with a Python port **pyCoilGen** (https://github.com/kev-m/pyCoilGen).
- **RF coil EM simulation & SAR:** **openEMS** (FDTD;
  https://github.com/thliebig/openEMS · https://www.openems.de); **MARIE** —
  integral-equation full-wave solver for MRI RF coils + body
  (https://github.com/thanospol/MARIE) and its Python port **mariepy** (SAR /
  virtual-observation-point modeling, https://github.com/pulserver/mariepy);
  **CoSimPy** — EM/circuit co-simulation incl. SAR
  (https://github.com/umbertozanovello/CoSimPy). Commercial: HFSS, CST, Sim4Life.
- **RF matching / networks:** **scikit-rf**
  (https://github.com/scikit-rf/scikit-rf) — S-parameters and impedance matching;
  general-purpose but standard for coil tuning.
- **B0 shimming:** **Shimming Toolbox** — static, dynamic, and real-time shimming
  in Python: https://github.com/shimming-toolbox/shimming-toolbox .
- **Safety:** SAR (RF heating) and PNS (gradient) limits are regulatory and
  safety-critical — see the MRI safety section below; never improvise around
  limits.

## MRI safety (research orientation — not clinical guidance)

MRI is generally safe but has real, physics-driven hazards. This is background
orientation for researchers; it is **not** a substitute for your site's MR
safety program, screening, or a qualified MR safety officer / medical physicist.
For anything involving a real magnet or human/animal subjects, follow local
policy, IRB/ethics approval, and vendor specifications.

Main hazard classes:
- **Static field (B0):** the always-on magnet turns ferromagnetic objects into
  projectiles and can disrupt implants — strict ferromagnetic screening and zone
  control are essential.
- **Gradients:** rapidly switched fields cause peripheral nerve stimulation
  (PNS) and loud acoustic noise (hearing protection).
- **RF (B1):** deposits power as heat — **SAR** limits guard against tissue
  heating/burns (mind conductive loops and leads).
- **Cryogens / quench:** superconducting magnets can quench and vent cryogens;
  quench pathways and oxygen monitoring matter.
- **Implants & devices:** must be checked for MR-conditional/safe labeling at the
  relevant field strength before scanning.
- **Contrast agents:** gadolinium-based agents carry their own considerations
  (e.g., NSF in severe renal impairment, gadolinium retention) — a clinical
  decision, out of scope here.

Authoritative references:
- **ACR Manual on MR Safety** —
  https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/radiology-safety/mr-safety
- **MRIsafety.com** (Shellock R&D / IMRSER), incl. implant/device lookup —
  https://www.mrisafety.com/
- **ISMRM** safety resources — https://www.ismrm.org/

## How to help on hardware questions

Hardware is where "point, don't reproduce" matters most: the user should engage
the primary projects and their maintainers. Summarize the landscape, name the
right project (OSI²/MaRCoS/OCRA for consoles; openEMS for EM sim), flag the
safety constraints, and hand off to the project's own docs and community.
