# DWI and DTI: acquisition to interpretable maps

Read for diffusion-weighted data, tensor fitting, ADC/FA/MD maps or a diffusion
study plan. Diffusion MRI measures water displacement statistics; it is not a
generative diffusion model. DENSE measures coherent tissue displacement and
belongs in the sequence-design reference, not the DTI pipeline.

## Choose the measurement before the model

| Term | What it describes | Decision it changes |
|---|---|---|
| DWI | Images acquired with diffusion sensitization, indexed by b-value and direction | Preserve each volume's encoding and acquisition metadata. |
| ADC | An apparent diffusivity estimated under a chosen signal model | Report b-values and fitting method; a bright DWI image alone is not proof of low diffusivity. |
| DTI | A symmetric diffusion tensor fitted to directional DWI | Needs sufficient independent directions and an appropriate b-value range; cannot resolve multiple fiber populations within a voxel. |
| HARDI / multi-shell | Angular sampling / sampling at multiple b-values | These describe acquisition, not a unique fitted model. |
| DKI, CSD, NODDI | Different models for non-Gaussian diffusion, fiber orientations or microstructure | Check each model's acquisition requirements and assumptions before fitting. |

For a single tensor, `S(b,g) = S0 exp(-b gᵀ D g)`, with unit direction `g`,
`b` in s/mm² and diffusivity in mm²/s. Six independent tensor components plus
`S0` must be estimated: six independent diffusion directions and a b≈0 reference
are an algebraic minimum, not a robust acquisition recommendation. Select angular
coverage, repeats, b-values and SNR for the question; do not fit a tensor blindly
to all high-b shells. See the [DIPY tensor tutorial](https://docs.dipy.org/stable/examples_built/reconstruction/reconst_dti.html).

## Inspect the inputs

- Match NIfTI volume count to `.bval` and `.bvec` entries; check finite values,
  b≈0 volumes, shells and direction norms. Preserve original files.
- Inspect b-vector coordinates against image orientation. Conversion, rotation
  and resampling can change conventions; do not fix a suspected flip by trial
  and error until the anatomy merely looks plausible.
- Retain BIDS `PhaseEncodingDirection`, `TotalReadoutTime`, voxel sizes and
  acquisition details. A filename saying AP/PA is not sufficient metadata.
- Examine representative b≈0 and diffusion-weighted volumes for dropout, motion,
  distortion, ghosts, coverage and noise floor before deciding the pipeline.

## Preprocess, then fit

Use official [FSL diffusion guidance](https://fsl.fmrib.ox.ac.uk/fsl/docs/diffusion/index.html)
and established MRtrix3/DIPY workflows. Denoising and Gibbs correction generally
precede interpolation; check denoiser assumptions and partial-Fourier caveats in
[`mrdegibbs`](https://userdocs.mrtrix.org/en/latest/reference/commands/mrdegibbs.html).

`topup` estimates susceptibility fields from suitable differing phase-encoding
images, commonly reversed-PE b≈0 pairs. A conventional fieldmap is a different
input route, not an interchangeable `topup` input. `eddy` addresses motion and
eddy-current effects and can use a susceptibility estimate. Use its corrected
images **with the rotated b-vectors** for downstream fitting; inspect outlier
and motion reports. See the [eddy guide](https://fsl.fmrib.ox.ac.uk/fsl/docs/diffusion/eddy/users_guide/index.html).

For BIDS datasets, [QSIPrep](https://qsiprep.readthedocs.io/) handles preprocessing;
[QSIRecon](https://qsirecon.readthedocs.io/) handles downstream diffusion modeling
and tractography. Here “reconstruction” means diffusion-model reconstruction,
not reconstructing raw scanner k-space. Avoid repeating corrections on derivatives.

Fit with DIPY, MRtrix3 or FSL using the selected shells, corrected gradients and
an inspected mask. Keep the estimator and software version in the run record.

## Evaluate and report

- MD is the mean tensor eigenvalue; AD is the largest eigenvalue and RD the mean
  of the other two. FA measures eigenvalue anisotropy, not “white-matter health.”
- Inspect FA/MD, fit residuals, eigenvalue behavior, masks and principal-direction
  maps together. Report diffusivity units and display scales.
- Crossing fibers, partial volume, motion, noise and protocol differences can
  change tensor metrics. A metric change alone does not identify a biological
  mechanism; design controls and report alternative explanations.
- Tractography is model-dependent inference; streamline counts are not axon
  counts. Use suitable orientation models and validate downstream claims.

Example request: “Compare FA between groups.” First inspect acquisition and
preprocessing comparability, motion and registration; then choose fitting,
statistics and confound handling. Deliver QC figures, maps, effect sizes and
limitations, not only a significant p-value.
