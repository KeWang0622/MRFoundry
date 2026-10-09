# MRI image analysis & processing

Use this once you have **images** (not raw k-space): organizing, converting,
registering, segmenting, and analyzing MR data. This is the "after
reconstruction" half of MRI research — structural, functional, and diffusion
analysis, plus the neuroimaging pipelines the community standardizes on. For
getting from scanner raw data to images, see [`recon-methods.md`](recon-methods.md) and
[`data-and-formats.md`](data-and-formats.md).

All tools below were link-verified; pick by task, and point users to each
project's own docs for depth (pointer-not-dump).

## File formats & dataset organization

- **DICOM** — the clinical/scanner image standard. Read/write in Python with
  **pydicom** (https://github.com/pydicom/pydicom).
- **NIfTI** — the analysis-world volume format. Convert DICOM→NIfTI with
  **dcm2niix** (https://github.com/rordenlab/dcm2niix), the fast de-facto tool.
  Read/write NIfTI (and more) with **nibabel** (https://github.com/nipy/nibabel).
- **BIDS (Brain Imaging Data Structure)** — the standard for organizing a
  neuroimaging dataset so pipelines can run on it automatically:
  https://bids.neuroimaging.io/ . Convert into BIDS with **heudiconv**
  (https://github.com/nipy/heudiconv) or dcm2bids. Many pipelines are "BIDS
  Apps" that consume a BIDS dataset directly.

## The major neuroimaging suites (structural / multi-modal)

These are the field's workhorses; each spans many tasks (registration,
segmentation, stats). Choose by ecosystem and modality:

- **FreeSurfer** — https://surfer.nmr.mgh.harvard.edu/ — cortical surface
  reconstruction and subcortical segmentation from structural (T1) MRI; the
  standard for cortical thickness / surface analysis.
- **FSL** — https://fsl.fmrib.ox.ac.uk/fsl/docs/ — comprehensive library
  covering fMRI (FEAT), diffusion (FDT), structural (FIRST/FAST), and
  registration (FLIRT/FNIRT); includes perfusion (BASIL) and MRS (FSL-MRS).
- **SPM** — https://www.fil.ion.ucl.ac.uk/spm/ — MATLAB toolbox for statistical
  parametric mapping of fMRI/PET (and M/EEG); the classic mass-univariate GLM
  ecosystem. **Ask which version:** development moved to
  https://github.com/spm/spm and numbering switched to calendar releases (latest
  stable **25.01.02**, Jan 2025; 26.01 in release candidate). A great deal of
  published work and many third-party toolboxes still assume **SPM12**, so paths
  and scripts are not interchangeable — name the version in a methods section.
- **AFNI** — https://afni.nimh.nih.gov/ — a broad C/Python suite focused on
  functional MRI processing, analysis, and visualization.
- **ANTs** (ANTsX) — https://github.com/ANTsX/ANTs — best-in-class registration
  (SyN), plus segmentation and template/normalization tools; usable standalone
  or from other pipelines. Python via ANTsPy.

## Functional MRI (fMRI)

- **Preprocessing:** **fMRIPrep** (https://github.com/nipreps/fmriprep) — a
  robust, BIDS-native, minimally-opinionated preprocessing pipeline that has
  become the community default. Runs as a container on a BIDS dataset.
- **Analysis:** **nilearn** (https://github.com/nilearn/nilearn) for
  Python-based statistics/ML and connectivity on NIfTI data; or the GLM/stats
  in SPM, FSL (FEAT), and AFNI. Covers task and resting-state (functional
  connectivity) designs.

## Quality control & motion correction

- **MRIQC** — https://github.com/nipreps/mriqc — automated image-quality metrics
  and visual reports for structural and functional MRI; run it before analysis
  to catch bad scans.
- **Retrospective motion correction:** FSL **MCFLIRT**
  (https://fsl.fmrib.ox.ac.uk/fsl/docs/#/registration/mcflirt) and SPM
  **Realign** align a time series after acquisition; fMRIPrep does this within
  its pipeline. (Prospective/real-time motion correction is an acquisition
  topic — see [`sequences-and-trajectories.md`](sequences-and-trajectories.md).)

## Diffusion MRI (dMRI)

For DWI/DTI inputs, gradient conventions, fitting and QC, read the
[diffusion guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/diffusion-mri/references/dwi-dti.md) and use the
`diffusion-mri` skill.

- **MRtrix3** — https://github.com/MRtrix3/mrtrix3 — advanced diffusion modeling
  (constrained spherical deconvolution) and tractography (fibre density, ACT).
- **DIPY** — https://dipy.org/ — Python diffusion library: DTI/DKI fitting,
  registration, tractography, denoising.
- **FSL FDT** (within FSL, above) — DTI fitting, bedpostx/probtrackx
  probabilistic tractography.
- **TractSeg** — https://github.com/MIC-DKFZ/TractSeg — CNN-based automatic
  white-matter tract segmentation (skips manual ROI drawing).

## Segmentation (deep learning)

- **nnU-Net** — https://github.com/MIC-DKFZ/nnUNet — self-configuring
  segmentation framework; a strong baseline that adapts to a new dataset with
  minimal tuning. The default first thing to try for a new seg task.
- **TotalSegmentator** — https://github.com/wasserth/TotalSegmentator —
  pretrained segmentation of 100+ anatomical structures (CT and MR).
- **MONAI** — https://github.com/Project-MONAI/MONAI — PyTorch framework for
  medical-imaging deep learning (transforms, networks, losses, training);
  build custom pipelines when nnU-Net's fixed recipe isn't enough.

## Cardiac, body, MSK & radiomics

Analysis beyond the brain — where deep-learning segmentation and quantitative
feature extraction dominate:

- **Cardiac** — cine segmentation (LV/RV/myocardium), strain, and parametric
  mapping. **nnU-Net** (above) is the de-facto backbone; benchmark on the ACDC
  and M&Ms cardiac datasets (see [`data-and-formats.md`](data-and-formats.md)), and use **MONAI** for
  custom models.
- **Body & MSK** — abdominal-organ and musculoskeletal segmentation:
  **TotalSegmentator** (100+ structures) and nnU-Net are the usual starting
  points.
- **Radiomics** — extract reproducible quantitative image features (shape,
  first-order intensity, texture) from images + masks for downstream modeling.
  **pyradiomics** — https://github.com/AIM-Harvard/pyradiomics — is the standard
  (van Griethuysen JJM, et al. *Cancer Res* 2017;77(21):e104–e107,
  doi:10.1158/0008-5472.CAN-17-0339). Follow **IBSI** conventions for feature
  standardization.

## Workflow & reproducibility

- **Nipype** — https://github.com/nipy/nipype — wraps FSL/SPM/FreeSurfer/ANTs/
  AFNI behind uniform Python interfaces and a workflow engine, so multi-tool
  pipelines are scriptable and reproducible.
- Prefer **BIDS + BIDS Apps + containers** (Docker/Singularity) for
  reproducible analyses; most modern pipelines (e.g., fMRIPrep) ship this way.

## Which tool for which task (quick guide)

- *Convert scanner DICOMs to analysis-ready NIfTI/BIDS* → dcm2niix (+ heudiconv
  for BIDS).
- *Cortical thickness / surface analysis from a T1* → FreeSurfer.
- *Register/normalize volumes to a template* → ANTs (SyN) or FSL FLIRT/FNIRT.
- *Preprocess a task/resting fMRI dataset* → fMRIPrep, then nilearn/FSL/SPM/AFNI
  for stats.
- *Tractography / white-matter analysis* → MRtrix3 or DIPY; TractSeg for
  automated tracts.
- *Segment an organ/structure/lesion* → try TotalSegmentator (if covered) or
  nnU-Net; MONAI to build a custom model.
- *Glue several tools into one reproducible pipeline* → Nipype + BIDS.
- *Check data quality before analysis* → MRIQC.
- *Segment cardiac cine / benchmark a model* → nnU-Net on ACDC or M&Ms.
- *Extract radiomic features for modeling* → pyradiomics (follow IBSI).
