# Raw-data reconstruction checklist

**Summary.** Most silent failures with acquired or vendor-style k-space are conventions, not algorithms.
Record layout, k = 0 position, encoding sign, oversampling, noise covariance and sampling before
reconstructing; validate the whole chain on data simulated with an independent forward model; choose the
method and its regularization by simulated error; report SNR in defined units. Helpers:
`scripts/mrfoundry_rawrecon.py` (numpy only, `python scripts/test_rawrecon.py`) and
`scripts/mrfoundry_reconlib.py`.

## Helpers (mrfoundry_rawrecon.py)

| Function | Purpose |
|---|---|
| `fft2c`, `ifft2c` | centred orthonormal 2D transforms (k = 0 at n//2), as in SigPy |
| `image_from_kspace(ksp, encoding_sign)`, `direct_dft_signed` | reconstruction honouring the encoding sign; explicit-sum forward model for checks |
| `noise_covariance(noise[coil, samples])`, `scale_noise_covariance`, `prewhiten` | Psi = E[n n^H]; dwell-time conversion; whitening of noise, calibration and imaging data with one W |
| `remove_readout_oversampling` | crop the central FOV after the readout transform |
| `grappa_2d`, `pocs_partial_fourier`, `coil_maps_from_acs`, `sense_cg(lamda)` | parallel imaging and partial Fourier |
| `snr_units_image(coil_images, psi, n_averages, sens)` | Kellman–McVeigh SNR units (real and imaginary noise SD 1) |
| `pseudo_replica` | noise maps, g-factor |
| `rank_reconstructions(candidates, truth, sens, mask, psi)` | pick method and λ by simulated error with your noise |
| `orientation_check(img, ref)` | names the flip/transpose and shift between a reconstruction and a reference |
| `nrmse` | normalized error with optional scale fit |

## Conventions to establish

- **Layout**: axis order (coil, ky, kx), readout axis, where k = 0 sits. Asymmetric echoes and partial Fourier
  move the peak: locate the k-space maximum instead of assuming n//2. Acquisitions stored in chronological
  order must be placed by their encode index (and average index); never assume storage order.
- **Readout oversampling** (often 2x): crop the central field of view after the readout transform before
  comparing with a nominal matrix.
- **Noise**: estimate Psi from the noise scan; with samples as rows X [samples, coil] the estimate is
  X.T @ X.conj() / N (X.conj().T @ X is conj(Psi)). Noise per sample scales with bandwidth: Psi_imaging =
  Psi_noise * noise_dwell / imaging_dwell. Averaging N acquisitions divides the covariance by N.
- **Sampling**: acceleration, acquired line offset, ACS lines (integrated or separate), partial-Fourier
  coverage. Keep acquired samples; fill missing lines with GRAPPA/SENSE and asymmetric coverage with POCS or
  homodyne rather than reporting zero-filled blur.
- **FFT and scaling**: centred orthonormal transforms differ from numpy's unnormalized `ifft2` by a constant.
  State the intensity scale and the coil combination (RSS or sensitivity-weighted).
- **Encoding sign**: s(k) = Σ m(r) exp(-i2πk·r) is reconstructed by `ifft2c`; data defined with
  exp(+i2πk·r) need `fft2c` (`image_from_kspace(..., encoding_sign=+1)`). The wrong choice mirrors the image in
  both axes and shifts it by one pixel for even matrices.
- **Orientation**: confirm row/column order and flips against an asymmetric feature or reference with
  `orientation_check`.

## Choosing the method and regularization

Simulate k-space from a smooth phantom (or a high-SNR reference) through your exact sampling with your
measured noise covariance, reconstruct with each candidate (GRAPPA, CG-SENSE with several λ or iteration
counts, POCS settings) and compare NRMSE against the known image: `rank_reconstructions`. Unregularized
SENSE and GRAPPA at R >= 3 amplify noise; mild Tikhonov or early stopping often wins. Report the SNR cost of
acceleration with a g-factor or pseudo-replicas.

## SNR units

Prewhiten with Psi/N (N averages), combine with the sensitivity-weighted (Roemer) combination and scale by
sqrt(2) so that the real and imaginary noise each have SD 1 (Kellman & McVeigh 2005): `snr_units_image`. An
RSS of prewhitened images times sqrt(2) has the same scale at high SNR. Verify on pure noise or with
pseudo-replicas; selecting low-magnitude pixels of the image to measure noise is biased low.

## Non-Cartesian

`mrfoundry_reconlib.py`: `direct_dft(image, kxy, fov)` is the exact forward model for checks (kxy in cycles/m,
last axis (kx, ky); image [y, x]); `nufft_least_squares` wraps SigPy, which orders coordinates like the image
axes (ky, kx) in grid units: swapping them transposes the image. Use density compensation or least squares,
calibrate absolute scale on a simulated object of known magnitude, and for radial data estimate gradient
delays from the data (opposed or orthogonal spokes; BART `estdelay` implements RING) before the final
reconstruction. EPI is Cartesian: regrid ramp samples and correct Nyquist ghosts, then reconstruct as Cartesian.

## Standalone entrypoints

Read acceleration, ACS, oversampling, partial Fourier, coil count, dwell times and noise information from the
file or header, never from constants tuned to one dataset; rerun on a second simulated dataset with different
values, and run `finish_check.py` before finishing.
