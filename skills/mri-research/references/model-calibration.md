# Calibrating model-based quantitative estimates

Use this for any estimate that depends on a fitted signal model with fixed settings:
signal-fraction and diffusivity-spectrum models (RSI, NNLS spectra, IVIM, free water),
multi-component T2 and myelin water, magnetization transfer, perfusion and DCE models,
and relaxometry with fixed nuisance parameters. These models often fit the data well
while the target parameter is biased, because neighbouring parameters trade off.

## Procedure

1. **Define the target and its tolerance**: the quantity reported (for example, a
   fraction, rate or relaxation time per region) and the error that would change a
   conclusion.
2. **Separate development and evaluation data.** Choose every model setting (fixed
   parameters, basis, regularization weight, thresholds) on development data only,
   never on evaluation data and never by the size of the effect you hope to show.
3. **Calibrate on pooled development curves.** Average voxels into region,
   tissue-class or subject curves to obtain high SNR. Fit each candidate model or
   fixed setting, then compare the residual RMS and the residual pattern across the
   acquisition variable (b, TE, TI, time). Prefer the simplest model without a
   systematic residual. Without development data, use literature values for the same
   organ, field strength and protocol, and report a sensitivity range.
4. **Check identifiability.** Vary each fixed nuisance parameter across the range the
   data cannot reject (near-best residuals) and report how much the target moves for
   each compared group. If it moves more than the tolerance, the data do not determine
   the target under this model: add flexibility (regularized spectrum, more
   compartments) or report the dependence.
5. **Run stratified recovery tests.** Simulate the actual acquisition and noise level.
   Draw truth parameters for each compared group from development fits, and generate
   signals with a model that differs from the fitting model (continuous distributions,
   partial volume, noise floor). Report bias per group and per true-value bin, and the
   slope of estimate versus truth, and the spread (voxelwise precision) as well as the bias.
   A pooled bias near zero is not evidence that any one tissue is unbiased. Choosing settings
   by pooled RMSE over a broad prior selects the prior's centre, and minimizing bias alone
   favours weak regularization with unstable voxel values. A test that simulates with the
   fitting model itself is circular.
6. **Choose hyperparameters with an outcome-blind criterion that is sensitive to the
   target**: worst-group or binned recovery RMSE (bias and spread) at
   development-calibrated parameters, or a discrepancy principle for regularization; then
   confirm the worst bias and the voxelwise precision or test-retest stability meet the
   study's requirements. Signal-prediction error alone is often insensitive to the target.
7. **Model the noise**: estimate sigma from background or repeated measurements, use a
   Rician-aware fit or floor correction where the magnitude floor matters.
8. **Report** the chosen settings with the residual evidence, the identifiability
   spread, the stratified recovery bias and the limitations.

## Helpers

- `diffusion-mri/scripts/spectrum_fit.py`: `calibrate_basis`, `stratified_recovery_test`,
  `fit_weights` (regularized NNLS), `fit_fixed_basis`, `floor_correct`.
- `mri-reconstruction/scripts/qmri_fit.py`: closed-form and dictionary fits for
  relaxometry; use them inside the same calibration and recovery procedure.
