---
name: mri-hardware
description: >-
  Read before any calculation, design or advice about MR hardware or safety: B0
  field maps and shimming (spherical harmonics, current limits, oblique
  geometry), gradient and RF coils (Biot-Savart, efficiency, linearity, B1), RF
  exposure (B1+rms, SAR, IEC 60601-2-33 modes), dB/dt and nerve stimulation,
  receiver noise, coil combination and SNR scaling, low-field and open-source
  consoles, quench and implants. Prevents silent errors in units, frames, field
  components, harmonic normalization, bounded optimization and limit definitions.
  Ships tested SI helpers checked against analytic cases. Not clinical advice;
  waveform programming belongs to pulse-sequence-design.
metadata:
  author: Ke Wang
  version: "0.11.0"
---

# MRFoundry: MRI Hardware and Safety

Hardware numbers are useful only with their units, conventions and a check. Use the tested helpers in
`scripts/mrfoundry_hwlib.py` (numpy/scipy, SI units) and import them rather than re-deriving them:
`python .agents/skills/mri-hardware/scripts/mrfoundry_hwlib.py --api` lists signatures (do not cat the source); `scripts/test_hwlib.py` shows
each helper on an analytic case.

## Route

| Task | Use (`mrfoundry_hwlib.py`) |
|---|---|
| Field map from multi-echo phase (nonzero phase0, uneven echo times) | `fieldmap_multiecho(phase, te, magnitude, max_abs_hz)` (temporal unwrapping; also spatially unwrap if fields can exceed 1/(2 ΔTE_min)) |
| Shim basis at voxel positions | `voxel_world_coords(affine, shape)` (full affine, mm to m), then evaluate the vendor's polynomials there; `solid_harmonics`, `fit_harmonics` for analysis |
| Optimal shim currents within limits | `shim_currents(field, roi, channel_maps, lower, upper, current_during_acquisition=I_acq)`: absolute currents, `frequency_adjust` (= -offset) and a KKT optimality report |
| Any bounded least-squares fit you wrote yourself | `bounded_lsq_kkt(A, b, x, lower, upper)` must return ok |
| Coil fields, gradient efficiency and linearity | `biot_savart`, `circle_path`, `loop_bz_on_axis`, `gradient_metrics` |
| RF exposure | `rf_energy`, `b1_rms` (window includes dead time), `b1_rms_of_train`, `b1_for_flip`, `sar_scale`, `iec_sar_limits`, `time_averaged_sar` |
| Gradient safety | `slew_rate`, `dbdt_at_radius`, `effective_stimulus_duration`, `pns_threshold_dbdt`, `iec_dbdt_limit` |
| Receiver noise and SNR | `noise_covariance`, `prewhitening_matrix`, `roemer_combine` (SNR units), `rss_combine`, `snr_scale` |

Derivations, standard values and references: [computations](references/computations.md).

## Checks that prevent silent errors

1. **Write the convention down before computing**: units (T, mT, µT; Hz, ppm; mT/m vs G/cm; per ampere),
   frame and axis (z = bore axis; world RAS+ from the NIfTI affine), field component (Bz vs |B|), region of
   interest, and which limit (6-min vs 10-s SAR, peak vs RMS, normal vs first-level mode).
2. **Field-model bookkeeping for shimming**: the measured map already contains the field of the currents that
   were on during the acquisition. Solve for ABSOLUTE new currents with `current_during_acquisition`, bound
   those, and map the free offset to the centre-frequency convention you report.
3. **Prove optimality, do not assume it**: run `bounded_lsq_kkt` on any constrained solution (column scaling
   left unscaled, bounds applied to scaled variables and sign flips all pass a "residual went down" check).
   Report which channels sit at their limits.
4. **Validate the tool on an analytic case first** (loop on axis, solenoid, synthetic harmonic field, a
   rectangular RF train) and check discretization convergence before the real geometry.
5. **Use established solvers for geometry-dependent physics** (Biot-Savart for coils; full-wave EM with a
   body model for local SAR; published PNS models). Never present a uniform-body estimate as local SAR.
6. **Report margins and limits**: standard and edition, mode, averaging window, assumptions and what was not
   modelled. Say when a qualified MR safety expert is required.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder>

## More (open only when needed)

- Hardware chain, low-field and open-source consoles, coil and shim design tools, MR safety references:
  [hardware landscape](references/landscape.md) and the hub's [hardware guide](../mri-research/references/hardware.md).
- Citations: [reading list](references/reading-list.md). Setup problems:
  [tool setup guide](../mri-research/references/tool-setup.md). Project notes (only with `.mrfoundry/INDEX.md`):
  [project memory](../mri-research/references/project-memory.md).
- Waveforms: `pulse-sequence-design`. Reconstruction: `mri-reconstruction`.
