# Hardware landscape, open hardware and safety references

**Summary.** Orientation for the MR hardware chain, open-source and low-field systems, coil/shim design tools
and safety resources. For calculations use `scripts/mrfoundry_hwlib.py` and [computations](computations.md).

## The hardware chain

- **Main magnet (B0)**: 0.05 T portable to 1.5/3/7 T and above; strength drives SNR and many trade-offs;
  low field (< 0.1 T) is a fast-growing area.
- **Gradients**: coils and amplifiers for spatial encoding; amplitude (mT/m), slew rate (T/m/s), duty cycle;
  bounded by hardware and peripheral nerve stimulation.
- **RF**: transmit coil(s), receive arrays, power amplifier, T/R switch, preamplifiers.
- **Console / spectrometer**: generates RF and gradient waveforms and digitizes signal.
- **Shim system**: passive, active and dynamic correction of B0 inhomogeneity.

## Low-field and open-source hardware

OSI² (https://www.opensourceimaging.org; design files https://gitlab.com/osii, including OSI² ONE), MaRCoS
(https://github.com/vnegnev), OCRA with ocra-pulseq (https://github.com/LincolnCB/ocra-pulseq), GPA-FHDO
(https://github.com/menkueclab/GPA-FHDO), MRI4ALL (https://github.com/mri4all).

## Coil, gradient and shim design

CoilGen (https://github.com/Philipp-MR/CoilGen) and pyCoilGen (https://github.com/kev-m/pyCoilGen); RF
coil EM and SAR: openEMS (https://github.com/thliebig/openEMS), MARIE (https://github.com/thanospol/MARIE),
CoSimPy (https://github.com/umbertozanovello/CoSimPy), scikit-rf for matching; commercial HFSS, CST,
Sim4Life. B0 shimming: Shimming Toolbox (https://github.com/shimming-toolbox/shimming-toolbox).

## MR safety (research orientation, not clinical guidance)

Not a substitute for a site MR safety programme, screening or a qualified MR safety officer. Hazards: static
field (projectiles, implants), gradients (PNS, acoustic noise), RF (SAR heating), cryogens and quench,
implants and devices, contrast agents. References: ACR Manual on MR Safety
(https://www.acr.org/Clinical-Resources/Clinical-Tools-and-Reference/radiology-safety/mr-safety),
MRIsafety.com (https://www.mrisafety.com/), ISMRM (https://www.ismrm.org/).
