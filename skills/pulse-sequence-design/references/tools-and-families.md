# Tools and sequence families

**Summary.** Pulseq/PyPulseq for vendor-neutral prototypes; KomaMRI (komamripy) or MRzeroCore to simulate the
exported file; SigPy.RF or pulpy for RF pulses; GrOpt or SigPy for time-optimal gradients; vendor SDKs only
for product integration. Check every family rule on the exported file (SKILL.md table).

## Pulseq workflow

1. Design in PyPulseq (https://github.com/pulseq/pypulseq) or Pulseq (https://github.com/pulseq/pulseq).
2. Check hardware limits (gradient amplitude, slew, PNS, duty cycle) and the implied trajectory
   (`calculate_kspace`), then the exported file against every requested parameter.
3. Simulate the exported file: KomaMRI (https://github.com/JuliaHealth/KomaMRI.jl, Python interface
   komamripy) or MRzeroCore (https://github.com/MRsources/MRzero-Core).
4. Play the file through the vendor's Pulseq interpreter (GE: TOPPE, https://github.com/toppeMRI/toppe).
   Tutorials: MR-Physics-with-Pulseq (https://github.com/pulseq/MR-Physics-with-Pulseq).
5. Reconstruct (ISMRMRD, then `mri-reconstruction`).

## Trajectories

Cartesian (robust), radial (motion-robust; golden angle for dynamics; sensitive to gradient delays), spiral
(efficient, off-resonance sensitive), EPI (fast, distortion-prone), 3D stack-of-stars, cones. Non-Cartesian
reconstruction needs the actual trajectory (measured, GIRF-corrected or delay-corrected).

## EPI, diffusion preparation and DENSE

Single-shot EPI: `add_epi_readout` in `scripts/mrfoundry_seqlib.py` (alternating readout lobes, ADC on the
flat top, blips during ramp-down, constant line period, TE to the kx = ky = 0 sample). Off-resonance df shifts an EPI image along the phase-encode direction by df x ES x N_pe pixels (ES = echo
spacing, N_pe = lines per shot; equivalently df divided by the phase-encode bandwidth per pixel 1/(N_pe ES)).
The sign depends on the ky traversal direction and the off-resonance sign convention: confirm it by simulating
one off-resonant object through the exported sequence. Diffusion preparation needs b-matrix checks; DENSE needs displacement
encoding and phase validation; verify the simulator supports diffusion or motion before claiming those
effects were tested. Family guide: [sequences and trajectories](../../mri-research/references/sequences-and-trajectories.md).

## RF pulse design

SigPy.RF (`sigpy.mri.rf`: SLR, adiabatic, multiband, small/large tip, pTx), pulpy
(https://github.com/jonbmartin/pulpy), Spectral-Spatial-RF-Pulse-Design
(https://github.com/LarsonLab/Spectral-Spatial-RF-Pulse-Design), Multiband-RF
(https://github.com/mriphysics/Multiband-RF), kpTx (https://github.com/wgrissom/kpTx). Mind RF power and SAR.

## SMS / multiband and controlled aliasing

Blipped-CAIPI (Setsompop et al., MRM 2012;67:1210, doi:10.1002/mrm.23097), CAIPIRINHA (Breuer et al., MRM
2005;53:684, doi:10.1002/mrm.20401; MRM 2006;55:549, doi:10.1002/mrm.20787), Wave-CAIPI (Bilgic et al., MRM
2015;73:2152, doi:10.1002/mrm.25347). Product sequences: https://www.cmrr.umn.edu/multiband/. Multiband
pulses sum single-band pulses with frequency offsets (and phase schedules to limit peak power); slice-shift
blips create the CAIPI shift.

## Gradient optimization, GIRF and other simulators

GrOpt (https://github.com/mloecher/gropt); SigPy `min_time_gradient` (Lustig, Kim and Pauly, TMI 2008,
doi:10.1109/TMI.2008.922699); PNS prediction safe_pns_prediction
(https://github.com/filip-szczepankiewicz/safe_pns_prediction); GIRF (https://github.com/MRI-gradient/GIRF),
GIRFReco.jl (https://github.com/BRAIN-TO/GIRFReco.jl). Other simulators: JEMRIS, MRiLab, sycomore, EPG-X.

## Vendor environments

Siemens IDEA + ICE, GE EPIC + Orchestra, Philips Paradise/GOAL-C (all with Pulseq interpreters); Gadgetron
(https://github.com/gadgetron/gadgetron) for online reconstruction via ISMRMRD. Use native SDKs only when
Pulseq cannot express a feature or for product integration.
