---
name: mri-research
description: >-
  Start here when an MRI task does not clearly match a specialist skill, spans
  several areas, or involves image-level analysis or spectroscopy:
  DICOM/NIfTI/BIDS conversion and orientation, registration, segmentation,
  FreeSurfer, fMRI and GLM analysis, MR spectroscopy quantification (tested
  alignment, linear-combination fit and water referencing), plus papers,
  datasets and tools. Holds shared references: tool setup, data formats,
  evaluation and attribution, model calibration, project memory. Routes to the
  specialists for sequences, reconstruction and quantitative maps (including QSM,
  ASL, DCE), diffusion, hardware and safety, deep learning and study statistics.
metadata:
  author: Ke Wang
  version: "0.11.0"
---

# MRFoundry: MRI Research Hub

Find the row that matches the task, open that one file or skill, and work from it.

## Route

| Task | Go to |
|---|---|
| Pulse sequences, RF and gradient waveforms, Pulseq export, Bloch simulation | `pulse-sequence-design` skill |
| k-space to images; T1/T2/T2*, EPG, ASL, DCE and QSM maps | `mri-reconstruction` skill (QSM: `scripts/qsm_lib.py`) |
| Diffusion (ADC, DTI/DKI, fractions, tractography) | `diffusion-mri` skill |
| Hardware, shimming, field maps, SAR, PNS, receiver noise | `mri-hardware` skill |
| Trained reconstruction networks | `deep-learning-recon` skill |
| Studies, statistics, deliverable checks, papers | `mri-research-workflow` skill (always run its finish check) |
| **MR spectroscopy quantification** | `scripts/mrs_lib.py` here (below) and [quantitative MRI and spectroscopy](references/quantitative-and-spectroscopy.md) |
| Image analysis: registration, segmentation, FreeSurfer, fMRI/GLM, fMRIPrep | [analysis and processing](references/analysis-processing.md) |
| File formats (DICOM, NIfTI orientation, BIDS, ISMRMRD, twix, P-file) and datasets | [data and formats](references/data-and-formats.md) |
| Fixed settings of a model-based estimate | [model calibration](references/model-calibration.md) |
| Installing or repairing tools (only if an install fails) | [tool setup](references/tool-setup.md) |
| Method comparisons, evidence and citation audits | [evaluation and attribution](references/evaluation-and-attribution.md) |
| Physics and courses; sequences overview; reconstruction methods; software; hardware overview | [foundations](references/foundations.md), [sequences and trajectories](references/sequences-and-trajectories.md), [recon methods](references/recon-methods.md), [tools](references/tools.md), [hardware](references/hardware.md) |
| Papers, APIs, venues and writing; image contrast primer | [literature access](references/literature-access.md), [publishing](references/publishing.md), [radiology primer](references/radiology-primer.md), [reading list](references/reading-list.md) |
| Project notes across sessions (only when `.mrfoundry/INDEX.md` exists or the user asks); optional `AGENTS.md` pointer | [project memory](references/project-memory.md), [agents pointer](references/agents-pointer.md) |

## MR spectroscopy (`scripts/mrs_lib.py`; `--api` lists signatures; worked example in `scripts/test_mrs_lib.py`)

1. Put metabolite and water acquisitions in the same physical units: divide each by its stored scale factor
   (and by the number of transients if summed). Check the frequency convention (`ppm_axis`; conjugate if the
   data use the opposite sign).
2. `spectral_registration` aligns transients (frequency and phase drift), then average.
3. `lcm_fit(fid, basis, dwell, f0, carrier_ppm, ppm_range)`: global shift, phase, Lorentzian and Gaussian
   broadening, nonnegative amplitudes, spline baseline; inspect the fit, residual and baseline figure.
4. `water_amplitude` (time-zero water signal) and `water_referenced_concentration` (Gasparovic et al. 2006):
   water content and relaxation per compartment, metabolite relaxation, protons, and division by the
   metabolite-containing tissue fraction (CSF has water but no metabolites).
5. Validate scaling on a simulated voxel built from the basis with known concentrations (the test shows how).

## Ground rules

Confirm load-bearing links resolve; respect dataset licences and access gates; summarize rather than copy
copyrighted text; image reading here is orientation, not diagnosis; cite primary sources.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder>
