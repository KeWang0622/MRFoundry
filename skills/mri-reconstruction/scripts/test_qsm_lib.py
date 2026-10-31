#!/usr/bin/env python3
"""Tests for qsm_lib (python test_qsm_lib.py, about 20 s on one core)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qsm_lib import *

# 1) dipole kernel against the analytic field of a uniformly magnetized sphere (independent of the FFT model):
#    outside f = gamma B0 dchi (a^3 / 3 r^3)(3 cos^2 theta - 1); inside 0 (Lorentz-corrected kernel).
vox = (1.0, 1.25, 1.5); b0 = np.array([0.3, 0.2, 0.93]); b0 /= np.linalg.norm(b0); a = 10.0; B0 = 3.0
sh = (80, 72, 64)
g = np.meshgrid(*[(np.arange(n) - n // 2) * v for n, v in zip(sh, vox)], indexing='ij')
r = np.sqrt(sum(c ** 2 for c in g)); chi = (r <= a).astype(float)
unit = GAMMA_BAR_1H * B0 * 1e-6                                      # Hz per ppm
f = field_from_chi(chi, vox, b0, B0) / unit
cos = sum(c * bi for c, bi in zip(g, b0)) / np.maximum(r, 1e-9)
f_an = (a ** 3 / (3 * np.maximum(r, 1e-9) ** 3)) * (3 * cos ** 2 - 1)
shell = (r > 1.5 * a) & (r < 3 * a)
rms_out = np.sqrt(np.mean((f[shell] - f_an[shell]) ** 2)); mean_in = abs(np.mean(f[r < 0.7 * a]))
assert rms_out < 0.01 and mean_in < 0.01, (rms_out, mean_in)      # in units of the susceptibility step
print(f"dipole kernel (oblique B0, anisotropic voxels) matches the analytic sphere field: rms error {rms_out:.4f} of dchi outside"
      f" (field up to {np.abs(f_an[shell]).max():.2f}), inside mean {mean_in:.4f}")
# the frequent error: B0 along the third array axis for an oblique slab
f_wrong = field_from_chi(chi, vox, (0, 0, 1), B0) / unit
assert np.abs(f_wrong[shell] - f_an[shell]).max() > 0.08
print("assuming B0 || third array axis for an oblique slab gives errors of half the field (detected)")

# 2) temporal and Laplacian field estimation with nonzero phase0 and wraps
te = np.array([0.003, 0.0055, 0.008, 0.0125])
yy = np.meshgrid(*[np.arange(n) for n in (32, 32, 16)], indexing='ij')
f_true = 60 * np.sin(yy[0] / 9.0) + 40 * np.cos(yy[1] / 7.0) + 2.0 * yy[2]          # |f| < 1/(2 * 2.5 ms)
ph0 = 1.2 * np.sin(yy[1] / 6.0)
phase = np.stack([np.angle(np.exp(1j * (ph0 + 2 * np.pi * f_true * t))) for t in te], -1)
mag = np.ones(phase.shape)
ft = multiecho_field_hz(mag, phase, te, (1, 1, 1), method='temporal')
assert np.abs(ft - f_true).max() < 1e-6
fl = multiecho_field_hz(mag, phase, te, (1, 1, 1), method='laplacian')
inner = (slice(4, -4),) * 3
d = (fl - f_true)[inner].ravel()
X, Y, Z = [c[inner].ravel().astype(float) for c in yy]
H = np.stack([np.ones_like(X), X, Y, Z, X * Y, Y * Z, X * Z, X ** 2 - Y ** 2, Y ** 2 - Z ** 2], 1)   # harmonic quadratics
res = d - H @ np.linalg.lstsq(H, d, rcond=None)[0]
assert np.std(res) < 0.05 * np.std(f_true[inner])        # the difference is a smooth harmonic term
print("multiecho_field_hz: temporal unwrapping exact for short echo spacing; Laplacian result differs by a smooth term")

# 3) full pipeline on a synthetic head with strong air and sinus fields, oblique B0 and anisotropic voxels
h = synthetic_head()
out = run_pipeline(h['mag'], h['phase'], h['te'], h['mask'], h['voxel_size_mm'], h['b0_dir'], h['b0_T'], h['rois'], 5)
deep = erode(h['mask'], h['voxel_size_mm'], 12)
c = np.corrcoef(out['local_hz'][deep], h['local_hz'][deep])[0, 1]
rm = roi_means(out['chi_ppm'], h['rois'], h['mask']); tm = roi_means(h['chi_ppm'], h['rois'], h['mask'])
est = np.array([rm[k][0] for k in sorted(rm) if k != 5]); tru = np.array([tm[k][0] for k in sorted(tm) if k != 5])
slope = np.sum(est * tru) / np.sum(tru * tru); rc = np.corrcoef(est, tru)[0, 1]
assert c > 0.85 and rc > 0.97 and 0.7 < slope < 1.1, (c, rc, slope)
print(f"pipeline (Laplacian unwrap -> PDF -> CG-L2 -> CSF reference): deep local-field corr {c:.3f}, ROI corr {rc:.3f}, slope {slope:.2f}")
v_loc, v_valid = vsharp(out['field_hz'], h['mask'], h['voxel_size_mm'])
cv = np.corrcoef(v_loc[deep], h['local_hz'][deep])[0, 1]
print(f"  (V-SHARP on the same field: deep corr {cv:.3f}; prefer PDF when air/sinus fields are strong)")
print("all qsm_lib tests passed")

