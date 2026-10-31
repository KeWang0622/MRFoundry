"""Tests for mrfoundry_rawrecon (python test_rawrecon.py)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrfoundry_rawrecon import *

rng = np.random.default_rng(0)
ny = nx = 64
y, x = np.mgrid[0:ny, 0:nx]
obj = ((x - 32) ** 2 / 24 ** 2 + (y - 30) ** 2 / 20 ** 2 < 1).astype(float)
obj += 0.6 * ((x - 22) ** 2 + (y - 26) ** 2 < 36) + 0.3 * ((x - 40) ** 2 + (y - 36) ** 2 < 49)
obj[10:14, 30:34] += 0.8  # asymmetric feature for orientation checks
phase = np.exp(1j * 0.6 * np.pi * ((x - 32) / 64 + 0.5 * (y - 32) / 64))
img = obj * phase
C = 8
ang = 2 * np.pi * np.arange(C) / C
sens = np.array([np.exp(-(((x - 32 - 40 * np.cos(a)) ** 2 + (y - 32 - 40 * np.sin(a)) ** 2) / (2 * 30 ** 2)))
                 * np.exp(1j * a) for a in ang])
sens /= np.sqrt(np.sum(np.abs(sens) ** 2, 0, keepdims=True))
coil = sens * img
ksp = fft2c(coil)
assert np.allclose(ifft2c(ksp), coil) and np.isclose(np.sum(np.abs(ksp) ** 2), np.sum(np.abs(coil) ** 2))
print("centred orthonormal FFT pair: round trip and energy preserved")

obj_small = np.zeros((16, 16)); obj_small[3:6, 9:13] = 1.0; obj_small[11, 2] = 2.0
for sgn in (-1, 1):
    s = direct_dft_signed(obj_small, sgn)
    assert np.allclose(image_from_kspace(s, sgn), obj_small, atol=1e-12)
wrong = np.abs(image_from_kspace(direct_dft_signed(obj_small, 1), -1))
assert np.allclose(wrong, np.roll(obj_small[::-1, ::-1], (1, 1), axis=(0, 1)), atol=1e-12)
assert np.allclose(direct_dft_signed(obj_small, -1), fft2c(obj_small), atol=1e-12)
print("encoding sign: image_from_kspace matches an explicit-sum forward model for both signs; the wrong sign mirrors and shifts by one pixel")

psi = np.cov(rng.normal(size=(C, 5000)) + 0.5 * rng.normal(size=(1, 5000)))
Lc = np.linalg.cholesky(psi)
noise = Lc @ ((rng.normal(size=(C, 200000)) + 1j * rng.normal(size=(C, 200000))) / np.sqrt(2))
psi_hat = noise_covariance(noise)
assert np.allclose(noise_covariance(prewhiten(noise, psi_hat)), np.eye(C), atol=1e-10)
print("noise covariance estimate and prewhitening give identity covariance")

wide = np.zeros((C, ny, 2 * nx), complex)
wide[:, :, nx // 2:nx // 2 + nx] = coil
kw = fft2c(wide)
kr = remove_readout_oversampling(kw, 2, axis=-1)
assert kr.shape == ksp.shape
assert np.allclose(ifft2c(kr), coil, atol=1e-12) and np.allclose(kr, ksp, atol=1e-12)
print("readout oversampling removal recovers the nominal-FOV image")

for Rf in (2, 3):
    mask = np.zeros(ny, bool)
    mask[::Rf] = True
    acs_sl = slice(ny // 2 - 12, ny // 2 + 12)
    mask[acs_sl] = True
    ku = ksp * mask[None, :, None]
    kg = grappa_2d(ku, Rf, ksp[:, acs_sl, :])
    e, _ = nrmse(rss(ifft2c(ksp)), rss(ifft2c(kg)), obj > 0)
    e0, _ = nrmse(rss(ifft2c(ksp)), rss(ifft2c(ku)), obj > 0)
    assert e < 0.03 and e < e0 / 5, (Rf, e, e0)
    print("GRAPPA R=%d with 24 ACS lines: NRMSE %.4f (zero-filled %.3f)" % (Rf, e, e0))

pf = np.zeros(ny, bool)
pf[ny // 2 - 12:] = True  # asymmetric sampling: 12 lines before the centre, all lines after
kp = ksp * pf[None, :, None]
ipocs = pocs_partial_fourier(kp, pf, n_iter=40)
ezf, _ = nrmse(rss(ifft2c(ksp)), rss(ifft2c(kp)), obj > 0)
epc, _ = nrmse(rss(ifft2c(ksp)), rss(ipocs), obj > 0)
assert epc < 0.5 * ezf, (epc, ezf)
print("POCS partial Fourier: NRMSE %.4f vs zero-filled %.4f" % (epc, ezf))

m2 = np.zeros(ny, bool)
m2[::2] = True
m2[ny // 2 - 8:ny // 2 + 8] = True
xs = sense_cg(ksp * m2[None, :, None], m2, sens, n_iter=100)
e, a = nrmse(img, xs, obj > 0, fit_scale=False)
assert e < 1e-3, e
print("CG-SENSE (R=2 + 16 ACS) recovers the complex image without rescaling: NRMSE %.1e" % e)

full = np.ones(ny, bool)
rec_full = lambda k: rss(ifft2c(k))
sd = pseudo_replica(rec_full, 1000 * ksp, None, n_rep=200, seed=1)
# unit-variance complex k-space noise -> magnitude noise std 1/sqrt(2) at high SNR (ortho FFT, sum|s|^2 = 1)
assert abs(np.median(sd[obj > 0]) - 1 / np.sqrt(2)) < 0.05, np.median(sd[obj > 0])
r2 = lambda k: np.abs(sense_cg(k, m2, sens, n_iter=60))
sd2 = pseudo_replica(r2, 1000 * ksp * m2[None, :, None], None, n_rep=60, seed=2, mask=np.repeat(m2[:, None], nx, 1)[None].repeat(C, 0))
sd1 = pseudo_replica(lambda k: np.abs(sense_cg(k, full, sens, n_iter=60)), 1000 * ksp, None, n_rep=60, seed=3)
inside = obj > 0
assert np.median(sd2[inside]) > np.median(sd1[inside])
print("pseudo-replica noise: accelerated SENSE noisier than full sampling (median ratio %.2f)" % (np.median(sd2[inside]) / np.median(sd1[inside])))
print("all raw-data reconstruction tests passed")



# ---- B5: SNR units with correlated complex noise, dwell scaling and averages; covariance convention; orientation
rng = np.random.default_rng(7)
Cc = 6
G = rng.normal(size=(Cc, Cc)) + 1j * rng.normal(size=(Cc, Cc))
psi_img = (G @ G.conj().T) / Cc + 0.5 * np.eye(Cc)             # complex, strongly correlated channels
assert np.max(np.abs(psi_img.imag)) > 0.1
sens6 = sens[:Cc] / np.sqrt(np.sum(np.abs(sens[:Cc]) ** 2, 0, keepdims=True))
def cnoise(cov, shape):
    L = np.linalg.cholesky(cov); z = (rng.normal(size=(cov.shape[0],) + shape) + 1j * rng.normal(size=(cov.shape[0],) + shape)) / np.sqrt(2)
    return np.tensordot(L, z, axes=(1, 0))
dwell_img, dwell_noise, navg, amp = 5e-6, 2.5e-6, 3, 40.0
psi_noise = psi_img * dwell_img / dwell_noise                      # wider bandwidth -> more noise per sample
noise_scan = cnoise(psi_noise, (20000,))
psi_est = scale_noise_covariance(noise_covariance(noise_scan), dwell_noise, dwell_img)
assert np.linalg.norm(psi_est - psi_img) / np.linalg.norm(psi_img) < 0.05
X = noise_scan.T                                                   # samples as rows: the conjugation trap
assert np.allclose(X.T @ X.conj() / X.shape[0], noise_covariance(noise_scan), atol=1e-2 * np.abs(psi_noise).max())
assert np.linalg.norm(X.conj().T @ X / X.shape[0] - psi_noise) / np.linalg.norm(psi_noise) > 0.2
kav = np.mean([fft2c(amp * sens6 * img) + cnoise(psi_img, (ny, nx)) for _ in range(navg)], axis=0)
snr = snr_units_image(ifft2c(kav), psi_est, n_averages=navg, sens=sens6)
q = np.real(np.einsum('cyx,cd,dyx->yx', sens6.conj(), np.linalg.inv(psi_img), sens6))
truth_snr = np.sqrt(2 * navg) * amp * np.abs(img) * np.sqrt(q)
hi = truth_snr > 25
assert abs(np.median(np.abs(snr[hi]) / truth_snr[hi]) - 1) < 0.03
pure = snr_units_image(ifft2c(np.mean([cnoise(psi_img, (ny, nx)) for _ in range(navg)], 0)), psi_est, navg, sens6)
assert abs(np.std(pure.real) - 1) < 0.05 and abs(np.std(pure.imag) - 1) < 0.05
low = np.abs(pure) < np.percentile(np.abs(pure), 15)
print(f"snr_units_image: median SNR ratio {np.median(np.abs(snr[hi]) / truth_snr[hi]):.3f}; pure-noise real SD {np.std(pure.real):.3f}"
      f" (SD in the lowest-15% magnitude pixels {np.std(pure.real[low]):.2f}: biased, never use it)")
print("noise covariance: dwell scaling recovered; samples-as-rows conj(Psi) trap detected")

ref = np.abs(img)
name, sh, cc, _ = orientation_check(np.roll(ref[::-1, ::-1], (1, 1), (0, 1)), ref)
assert name == 'flip_xy' and sh == (1, 1) and cc > 0.999
assert orientation_check(ref, ref)[:2] == ('identity', (0, 0))
assert orientation_check(ref.T, ref)[0] == 'transpose'
print("orientation_check names the flip/transpose and shift that map a reconstruction onto the reference")
print("all B5 raw-data tests passed")



# ---- B5: choose the reconstruction by simulated error with realistic noise (not by data consistency)
R3 = 3; acs3 = np.zeros(ny, bool); acs3[ny // 2 - 10: ny // 2 + 10] = True
m3 = np.zeros(ny, bool); m3[::R3] = True; m3 |= acs3
maps3 = coil_maps_from_acs(ksp * m3[None, :, None], acs3)
assert np.median(np.abs(np.sum(maps3.conj() * sens, 0))[obj > 0]) > 0.95       # close to the true maps
def grappa_rss(k):
    return rss(ifft2c(grappa_2d(k, R3, k[:, acs3, :])))
cands = {'grappa R3 (exact data consistency)': grappa_rss,
         'cg-sense lam=0': lambda k: np.abs(sense_cg(k, m3, maps3, lamda=0.0, n_iter=60)),
         'cg-sense lam=0.05': lambda k: np.abs(sense_cg(k, m3, maps3, lamda=0.05, n_iter=60))}
ranked = rank_reconstructions(cands, obj, sens, m3, n_rep=2, region=obj > 0, noise_scale=0.08)
assert ranked[-1][1] == 'cg-sense lam=0' and ranked[0][1] == 'cg-sense lam=0.05'   # noise amplification ranks last
print("rank_reconstructions (R=3, noisy simulation): " + "; ".join(f"{n} NRMSE {e:.3f}" for e, n in ranked))
print("all B5 reconstruction-selection tests passed")

