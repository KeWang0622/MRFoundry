# Diffusion preprocessing, models and tractography

**Summary.** Respect the pipeline order (convert, denoise, Gibbs, distortion/eddy/motion, mask, fit), keep
rotated b-vectors from eddy, and prefer a validated pipeline (QSIPrep) for full preprocessing. For fitting
conventions and frames see [DWI and DTI](dwi-dti.md) and the skill's route table.

## Typical pipeline

1. Convert and organize: `dcm2niix` (keeps `.bval`/`.bvec`), BIDS; sanity-check the gradient table.
2. Denoise first: MP-PCA with MRtrix3 `dwidenoise` (Veraart 2016); DIPY Patch2Self.
3. Gibbs ringing: MRtrix3 `mrdegibbs`.
4. Distortion, eddy currents, motion: FSL `topup` (reversed phase-encode pairs) then `eddy` (keep its rotated
   bvecs): https://fsl.fmrib.ox.ac.uk/fsl/docs/#/diffusion/eddy. A conventional field map needs the
   field-map route; it is not an input to `topup`.
5. Brain mask and bias field (ANTs N4).
6. Model fitting; 7. tractography and bundles.

QSIPrep (https://github.com/PennLINC/qsiprep) for BIDS-native preprocessing and QC; QSIRecon
(https://qsirecon.readthedocs.io/) for modelling and tractography.

## Models

- DTI/DKI: FA, MD, RD, AD and kurtosis; DIPY (https://github.com/dipy/dipy) or MRtrix3; `fit_tensor_lls` for
  closed-form DTI.
- CSD: fibre orientation distributions for crossing fibres (MRtrix3 `dwi2fod`).
- NODDI and microstructure: AMICO (https://github.com/daducci/AMICO).
- Spectrum and compartment fractions: see the skill and the model calibration procedure.

## Tractography and bundles

MRtrix3 (`tckgen` iFOD2, ACT, SIFT2, fixel-based analysis), DIPY, FSL FDT (`bedpostx`/`probtrackx`), TractSeg
(https://github.com/MIC-DKFZ/TractSeg).

## Acquisition notes

Keep `.bval`/`.bvec` with the data; multi-shell data enable DKI, NODDI and multi-tissue CSD; `topup` needs
blip-up/blip-down pairs with suitable metadata.
