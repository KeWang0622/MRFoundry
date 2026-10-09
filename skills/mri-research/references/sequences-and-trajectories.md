# Pulse sequence programming & k-space trajectory design

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this when the user wants to design/program a pulse sequence, define or
analyze a k-space trajectory, or simulate an acquisition. Sequence design and
trajectory design are two sides of the same coin: the gradient waveforms in the
sequence *are* what traces k-space.

## Trajectory families (and when each is used)

- **Cartesian** — line-by-line raster; simplest recon (FFT), robust to
  off-resonance; the clinical default. Undersample phase-encode lines for
  parallel imaging / CS.
- **Radial (spokes)** — samples through k-space center every readout; motion-
  robust, benign undersampling artifacts (streaks), great for dynamic imaging.
  **Golden-angle** radial gives near-uniform coverage for any temporal window.
- **Spiral** — very efficient k-space coverage per readout (fast); sensitive to
  off-resonance/blurring and gradient imperfections; needs NUFFT + often
  off-resonance correction.
- **EPI** — single/multi-shot zig-zag; the workhorse for fMRI and diffusion;
  fast but prone to geometric distortion, N/2 ghosting, and dropout.
- **3D variants / stack-of-stars / cones / rosettes / PROPELLER** — chosen for
  coverage, motion robustness, or SNR efficiency.

Non-Cartesian trajectories require gridding/NUFFT for reconstruction (see the
NUFFT tools in [`tools.md`](tools.md)) and an accurate description of the sampled
coordinates (the "trajectory"), which recon needs as input.

## Vendor-neutral sequence programming: Pulseq

**Pulseq** is the open, vendor-agnostic pulse-sequence standard. You describe a
sequence once as a `.seq` file; a vendor-specific interpreter plays it on the
scanner. This decouples research sequences from proprietary environments.

- Standard & MATLAB: https://github.com/pulseq/pulseq ·
  Tutorials: https://pulseq.github.io/
- **PyPulseq** (Python): https://github.com/pulseq/pypulseq ·
  docs: https://pypulseq.readthedocs.io . Paper: Ravi, Geethanath, Vaughan,
  "PyPulseq," *JOSS* 4(42):1725, 2019.
- Interpreters exist for **Siemens, GE, Bruker, and (more recently) Philips**;
  a `.seq` file is portable across scanner software versions once the
  interpreter is installed.
- **Ecosystem:** **TOPPE** (https://github.com/toppeMRI/toppe) runs Pulseq/TOPPE
  sequences on **GE** scanners; **pulseq-CEST**
  (https://github.com/kherz/pulseq-cest) adds CEST saturation blocks +
  Bloch–McConnell simulation (with a preset library, `pulseq-cest-library`);
  **MR-Physics-with-Pulseq** (https://github.com/pulseq/MR-Physics-with-Pulseq)
  is an excellent tutorial collection for learning sequence design.

## Vendor-native sequence environments (when Pulseq isn't enough)

Research needing tight vendor integration or product features still uses the
native SDKs (proprietary; require vendor research agreements — point the user
to their vendor collaboration, don't try to reproduce SDK internals):

- **Siemens — IDEA** (sequence build) + **ICE** (recon), C++.
- **GE — EPIC** (sequence) + **Orchestra** (recon SDK), C/C++.
- **Philips — Paradise / GOAL-C** research pulse-programming environment.
- **Bruker — ParaVision** method programming (preclinical).

If a user is prototyping a *method*, steer them to Pulseq first (portable,
open, fast to iterate); reserve vendor SDKs for when they need product-level
integration or features Pulseq can't express.

## RF pulse design

Sequence programming also means designing the RF pulses themselves (excitation,
refocusing, inversion, saturation; slice/slab-selective, spectral-spatial,
adiabatic, multiband, and parallel-transmit/pTx pulses).

- **SigPy.RF** (`sigpy.mri.rf`) — a Python RF-pulse-design toolbox within SigPy:
  SLR pulses, adiabatic pulses, multiband, small-tip and large-tip designs, and
  pTx. Docs via https://sigpy.readthedocs.io/ ; SigPy repo in [`tools.md`](tools.md).
- **pulpy** — https://github.com/jonbmartin/pulpy — Python RF/gradient pulse
  design (SLR, adiabatic, multiband, pTx) from the Grissom lab.
- **Spectral-Spatial-RF-Pulse-Design** —
  https://github.com/LarsonLab/Spectral-Spatial-RF-Pulse-Design — spectral-spatial
  (SPSP) pulse design (MATLAB).
- **Multiband-RF** (https://github.com/mriphysics/Multiband-RF) and **kpTx**
  (https://github.com/wgrissom/kpTx) — multiband/SMS and k-space-domain
  parallel-transmit (pTx) pulse design.
- **PyPulseq** defines the RF and gradient *events* that make up the sequence,
  so RF design and sequence assembly live in the same Python workflow.
- Be mindful of **RF power / SAR** limits (a safety constraint), especially for
  refocusing-heavy or high-flip designs.

## Simulation (test a sequence without scanner time)

- **KomaMRI.jl** — https://github.com/JuliaHealth/KomaMRI.jl — GPU-accelerated,
  Pulseq-compatible Bloch simulator; purpose-built for pulse-sequence
  development. Feed it a `.seq` and a phantom, get simulated signal/images.
- **JEMRIS** (https://github.com/JEMRIS/jemris) and **MRiLab**
  (https://github.com/leoliuf/MRiLab) — established open Bloch simulators
  (long-standing C++/GUI, and GPU-accelerated, respectively).
- **sycomore** (https://github.com/lamyj/sycomore) and **EPG-X**
  (https://github.com/mriphysics/EPG-X) — Bloch + extended-phase-graph (EPG)
  signal modeling; EPG-X adds magnetization transfer / chemical exchange.
- **MRzero-Core** (https://github.com/MRsources/MRzero-Core) — differentiable
  Bloch simulation + Pulseq, for sequence optimization and learning.
- BART includes analytical phantoms for quick recon testing.

## Designing/analyzing trajectories in code

- **BART** `traj` generates common trajectories (radial, spiral, custom) and
  `nufft` reconstructs them: https://mrirecon.github.io/bart/
- **SigPy** builds NUFFT linops from arbitrary coordinate arrays; good for
  prototyping novel trajectories in Python.
- **PyPulseq** computes the k-space trajectory implied by your gradient
  waveforms (`calculate_kspace`), so you can verify coverage and slew/gradient
  limits before playing the sequence.
- Always check **hardware constraints**: max gradient amplitude, max slew rate,
  PNS (peripheral nerve stimulation) limits, and duty cycle. A trajectory that
  violates these can't be played (or is unsafe). KomaMRI/PyPulseq help validate.
- **Gradient & trajectory optimization:** **GrOpt**
  (https://github.com/mloecher/gropt) for time-optimal gradient-waveform design,
  and Lustig's **minTimeGradient / tOptGrad**
  on the [author's software page](https://people.eecs.berkeley.edu/~mlustig/Software.html)
  for time-optimal gradients along an arbitrary k-space path. Use its
  **Time Optimal Gradient Design** section for the package and demo; verify the
  current download before installing. Validate against PNS with
  **safe_pns_prediction**
  (https://github.com/filip-szczepankiewicz/safe_pns_prediction).
- **GIRF (gradient impulse response function):** measure/apply with
  **MRI-gradient/GIRF** (https://github.com/MRI-gradient/GIRF); **GIRFReco.jl**
  (https://github.com/BRAIN-TO/GIRFReco.jl) is a Julia spiral-recon pipeline with
  GIRF trajectory correction — important for accurate spiral/non-Cartesian
  trajectories.

## Acceleration & correction (acquisition side)

Modern scans lean on these acquisition-side methods; recon-side acceleration
(parallel imaging, compressed sensing, deep learning) lives in
[`recon-methods.md`](recon-methods.md).

- **Simultaneous Multi-Slice (SMS) / multiband** — excite and read several
  slices at once for large speedups, then unalias them using coil
  sensitivities. Foundational: Moeller S, et al. *Magn Reson Med*
  2010;63(5):1144–1153 (doi:10.1002/mrm.22361); blipped-CAIPI to cut the
  g-factor penalty: Setsompop K, et al. *Magn Reson Med* 2012;67(5):1210–1224
  (doi:10.1002/mrm.23097). Widely-used product sequences from CMRR (Minnesota):
  https://www.cmrr.umn.edu/multiband/
- **B0 field mapping & distortion correction** — EPI/spiral suffer geometric
  distortion from B0 inhomogeneity. Correct with **FSL `topup`** (reversed
  phase-encode pairs, https://fsl.fmrib.ox.ac.uk/fsl/docs/#/diffusion/topup) or
  **FUGUE** (fieldmap-based unwarping,
  https://fsl.fmrib.ox.ac.uk/fsl/docs/#/registration/fugue).
- **B1 mapping** — transmit-field (B1+) mapping (double-angle, Bloch–Siegert,
  AFI) matters for quantitative and high-field work; feeds qMRI
  ([`quantitative-and-spectroscopy.md`](quantitative-and-spectroscopy.md)).
- **Off-resonance correction** for long-readout spiral/EPI — conjugate-phase /
  multi-frequency interpolation. Representative reference: Man L-C, Pauly JM,
  Macovski A. *Magn Reson Med* 1997;37(5):785–792 (doi:10.1002/mrm.1910370523).
- **Prospective motion correction** — track motion during the scan (navigators,
  optical tracking, FID/PACE) and update the acquisition geometry in real time.
  Retrospective correction and QC tools are in [`analysis-processing.md`](analysis-processing.md).

## Typical workflows

- *"Prototype a new golden-angle radial sequence and test it"* → design in
  PyPulseq → validate trajectory + slew limits → simulate in KomaMRI → export
  `.seq` → (with vendor interpreter) run → convert raw to ISMRMRD
  ([`data-and-formats.md`](data-and-formats.md)) → reconstruct with BART/SigPy NUFFT + PICS.
- *"Analyze the trajectory in this dataset"* → read the ISMRMRD header /
  trajectory arrays; if absent, reconstruct the nominal trajectory from the
  gradient description or sequence parameters.

## Sequence families: contrast, encoding and readout

These labels describe different parts of an acquisition and can be combined.
DWI is diffusion weighting; DTI is a fitted model; EPI is a readout; DENSE encodes
tissue displacement. Choose the contrast/measurement first, then its readout.

| Family | Typical purpose | What to check |
|---|---|---|
| Spoiled GRE | T1-weighted/dynamic imaging; flexible Cartesian, radial or spiral sampling | RF/gradient spoiling, steady state, TE/TR and off-resonance |
| SE / FSE (TSE) | Spin-echo contrast and efficient T2-weighted imaging | Refocusing train, effective TE, stimulated echoes, blurring and RF load |
| Inversion recovery | T1 weighting or suppression, including FLAIR/STIR | Inversion efficiency, TI, tissue relaxation and readout effects |
| bSSFP | High signal efficiency, often cine imaging | Balanced gradients, transient state, off-resonance banding and phase cycling |
| GE-EPI / SE-EPI | Fast BOLD or diffusion readout | Echo spacing, distortion, odd/even echo phase and signal loss |
| Diffusion-prepared SE-EPI | Direction- and b-dependent water diffusion contrast | Full gradient encoding, TE, motion and diffusion metadata |
| DENSE | Phase-based tissue displacement and derived strain, often cardiac | Encoding directions/frequency, phase reference, unwrapping and tracking |
| Phase-contrast MRI | Velocity encoding, including flow imaging | VENC, phase offsets, aliasing and velocity directions |

Start from established [Pulseq tutorials](https://pulseq.github.io/tutorials.html)
or the tool's upstream examples rather than inventing a sequence implementation.

### EPI and diffusion-weighted EPI

Alternating readout gradients and phase-encoding blips traverse many k-space lines
within an echo train. Short acquisition windows help speed, but low bandwidth in
the phase-encoding direction makes off-resonance distortion important. SE-EPI and
GE-EPI have different contrast; neither makes distortion disappear.

Use the upstream [diffusion EPI example](https://pulseq.github.io/writeEpiDiffusionRS.html)
as a starting point, with scanner-specific limits revalidated. Check actual ADC
sample coordinates, readout polarity, echo spacing, TE, partial Fourier and any
SMS/in-plane acceleration. Ramp sampling needs regridding when present;
odd/even phase mismatch needs ghost correction. EPI normally targets a Cartesian
grid; it is not automatically a radial/spiral NUFFT problem. Multi-shot diffusion
also needs a strategy for shot-to-shot phase variation.

Diffusion preparation sets the b-value/b-matrix, not the EPI readout alone. For
ideal rectangular pulsed-gradient spin echo, `b = (γ G δ)² (Δ − δ/3)` with γ in
rad/s/T gives b in s/m²; divide by 10⁶ for s/mm². Real waveforms need the full
encoding history, including refocusing sign changes and imaging-gradient cross
terms. Preserve directions and b-values with exported images; connect to the
[diffusion guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/diffusion-mri/references/dwi-dti.md).

### DENSE: displacement encoding with stimulated echoes

DENSE stores a position-dependent phase and decodes after tissue motion, making
phase sensitive to displacement. With encoding frequency `kₑ` in cycles/mm,
the displacement contribution is `Δφ = 2π kₑ · u` under the chosen sign convention.
Reference/background phase must be accounted for. This is distinct from DWI
attenuation and phase-contrast velocity encoding.

A useful analysis needs encoding directions, frequency/units, reference data,
cardiac timing, magnitude and phase images. Inspect magnitude SNR and phase wraps,
then unwrap and track tissue before deriving strain. Through-plane motion and
segmentation/tracking errors can bias 2D results; do not equate raw phase with a
strain map. Higher encoding frequency increases displacement sensitivity but
also phase wrapping for a given displacement.

Use [DENSEanalysis](https://denseanalysis.com/) and its
[upstream repository](https://github.com/denseanalysis/denseanalysis) for established
analysis. Its published setup is legacy MATLAB: check the chosen release's MATLAB,
toolbox and MEX compatibility and run an upstream example; do not promise a modern
Python equivalent or build an improvised strain solver when setup fails.
Foundational reading: [Aletras et al., DENSE](https://pmc.ncbi.nlm.nih.gov/articles/PMC2887318/)
and the phase-unwrapping/tracking paper cited by DENSEanalysis.

### Match simulation to the phenomenon

A static-spin Bloch test can verify timing/contrast but cannot by itself validate
diffusion attenuation or DENSE tissue motion. Verify that the established
simulator supports the required diffusion or prescribed-motion model, with an
upstream example and known reference case. If unsupported, explicitly limit the
result to the tested physics and select a supported implementation. A sequence
file passing timing checks is not evidence that the intended biomarker is valid.
