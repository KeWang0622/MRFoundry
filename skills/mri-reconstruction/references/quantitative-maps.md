# Quantitative maps

**Summary.** Use the tested helpers in `scripts/qmri_fit.py` and `scripts/qsm_lib.py` (numpy/scipy). State the
signal model and its time origin, check units, validate on data simulated by an independent route (closed form,
quadrature, Bloch or EPG simulation of your exact timing), and calibrate any fixed nuisance setting on
development data ([model calibration](../../mri-research/references/model-calibration.md)).

## Relaxometry and dictionaries

`fit_monoexp` (T2/T2*), `fit_inversion_recovery` (three parameters; magnitude polarity restoration),
`fit_vfa` (optional B1), `fit_dictionary` (match simulated curves; pass `noise_sigma` for low-SNR magnitude
data so the Rician floor does not lengthen T2 or shorten T1), closed forms `ernst_signal`, `ir_signal`,
`bssfp_signal`. Incomplete recovery or readout perturbations: fit a simulation of the exact timing.

**Multi-echo spin echo with B1 inhomogeneity**: stimulated echoes bias mono-exponential T2. Use
`epg_t2_dictionary(n_echoes, esp, t2_grid, b1_grid)` (B1 scales excitation and refocusing) with
`fit_dictionary(..., noise_sigma=sigma)`; sigma from the background (Rician). B1 above and below the value that
makes the refocusing angle 180° give identical trains: keep the B1 grid on one side unless a B1 map exists.
Cover the full B1 range expected (low B1 needs a grid reaching well below 0.5).

## ASL

- Group control and label volumes by their own delay (BIDS aslcontext, per-volume PLD) with
  `asl_pairs_by_delay`; volume order and pairing vary between datasets.
- 2-D multi-slice: the effective delay of slice z is PLD + SliceTiming[z]; pass per-voxel delays.
- M0 acquired with a finite TR: `m0_finite_tr(m0, tr, t1_tissue)`; blood M0 = M0 / λ inside the model.
- Single delay: `asl_cbf_pcasl` / `asl_cbf_pasl` (consensus formula, Alsop et al. 2015).
- Multiple delays: `fit_asl_multidelay(delta_m, m0, pld, tau)` with `asl_gkm_pcasl` (Buxton general kinetic
  model). Time since the START of labelling is τ + PLD; ATT is measured from the start of labelling. Using PLD
  alone shifts ATT by τ and scales CBF by exp(-τ/T1b). For PLD >= ATT the model equals the single-delay
  formula: use that equality as a check. ATT shorter than the shortest effective delay is not identifiable
  (reported as an upper bound).

## DCE

- `spgr_concentration(signal, t10, tr, flip, r1, n_baseline)`: M0 per voxel from the baseline frames and T10,
  exact SPGR inversion to R1, C = (R1 - R10)/r1.
- Plasma AIF: Cp = Cblood / (1 - Hct), mean over the arterial mask.
- `fit_tofts(t, ct, cp)`: exact convolution for Cp linear between (possibly non-uniform) frames
  (`conv_exp_pwlinear`), grid search in kep with closed-form Ktrans and vp, no initial guess. Rates are per
  unit of t (x60 for 1/min when t is in s). A rectangular `np.convolve` sum lags by half a frame and biases vp
  and Ktrans; `fit_tofts_linear` (Murase) is only an initial estimate.
- Validate the forward model against fine-grid quadrature, never against itself.

## QSM

`qsm_lib.py` (`python qsm_lib.py --selftest`; tests compare the dipole kernel with the analytic field of a
magnetized sphere):

1. Phase in radians from the stored scaling; apply the stated sign convention.
2. `multiecho_field_hz`: phase0 removed by division by the first echo; Laplacian unwrapping (default) or
   temporal unwrapping when |f| < 1/(2 ΔTE_min). Field in Hz.
3. `pdf_background` (projection onto dipole fields) removes air/sinus fields; `vsharp` is faster and weaker
   with strong external sources. Values are reliable a few mm inside the mask; judge deep regions.
4. `invert_cg_l2` (data term inside the mask, gradient regularization); `invert_tkd` as a check. B0 direction
   in the ARRAY axis frame (oblique slabs are not (0, 0, 1)) and physical voxel sizes in the kernel.
   Expect moderate underestimation of chi from regularization; quantify it on `synthetic_head`.
5. `reference_to_roi(chi, rois, label)` (e.g. ventricular CSF) and `roi_means`.
