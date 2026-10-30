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

