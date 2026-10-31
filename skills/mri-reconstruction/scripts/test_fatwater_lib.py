"""Tests for fatwater_lib (python test_fatwater_lib.py): isolated vials 0-100% fat, smooth field, 1.5 T and 3 T."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fatwater_lib import *


def phantom(n=64, seed=0):
    yy, xx = np.mgrid[0:n, 0:n] / n - 0.5
    labels = np.zeros((n, n), int); pdff = np.array([0, 5, 10, 20, 35, 50, 70, 90, 100], float)
    r2s = np.array([25, 60, 35, 120, 45, 80, 30, 150, 50], float)
    for i in range(9):
        cy, cx = (i // 3 - 1) * 0.3, (i % 3 - 1) * 0.3
        labels[(yy - cy) ** 2 + (xx - cx) ** 2 < 0.1 ** 2] = i + 1          # isolated vials in air
    return labels, pdff, r2s, yy, xx


def simulate(field_T, te, flip, tr, t1w, t1f, b1amp, field_scale, sigma, seed):
    rng = np.random.default_rng(seed); labels, pdff, r2s, yy, xx = phantom()
    off = fat_offsets_hz(field_T, FAT_PPM_REL_WATER)
    psi = field_scale * (0.6 + 0.8 * xx - 0.9 * yy ** 2 + 0.4 * xx * yy)   # smooth field (Hz)
    b1 = 1 + b1amp * (xx + 0.5 * yy)
    rho_f = np.zeros(labels.shape); rho_w = np.zeros(labels.shape); r2 = np.zeros(labels.shape)
    for i in range(9):
        m = labels == i + 1; rho_f[m] = pdff[i] / 100; rho_w[m] = 1 - pdff[i] / 100; r2[m] = r2s[i]
    W = rho_w * spgr_weight(flip, tr, t1w, b1); F = rho_f * spgr_weight(flip, tr, t1f, b1)
    ph0 = np.exp(1j * 0.7 * (xx - yy))
    fb = fat_basis(te, off, FAT_AMPLITUDES)
    sig = (W[None] + F[None] * fb[:, None, None]) * np.exp(-r2[None] * te[:, None, None]) * \
        np.exp(1j * 2 * np.pi * psi[None] * te[:, None, None]) * ph0[None]
    sig = sig + sigma * (rng.normal(size=sig.shape) + 1j * rng.normal(size=sig.shape))
    return sig, labels, pdff, r2s, b1, off


cases = [  # field, echo times, flip, TR, T1 water, T1 fat, B1 spread, field scale (Hz), noise
    (3.0, 1.2e-3 + 1.0e-3 * np.arange(6), 5.0, 9e-3, 1.0, 0.35, 0.15, 150.0, 0.004),
    (1.5, 1.4e-3 + 2.0e-3 * np.arange(6), 15.0, 14e-3, 0.8, 0.3, 0.10, 90.0, 0.004),
    (3.0, 1.0e-3 + 1.3e-3 * np.arange(5), 3.0, 7e-3, 1.2, 0.4, 0.20, -120.0, 0.0015),
    (1.5, 1.2e-3 + 2.3e-3 * np.arange(4), 10.0, 10e-3, 1.0, 0.3, 0.10, 100.0, 0.004),   # swap-prone: 4 echoes
]
for k, (B0, te, flip, tr, t1w, t1f, b1amp, fs, sigma) in enumerate(cases):
    sig, labels, pdff, r2s, b1, off = simulate(B0, te, flip, tr, t1w, t1f, b1amp, fs, sigma, k)
    t0 = time.time()
    res = fit_fat_water(sig, te, off, FAT_AMPLITUDES, mask=labels > 0)
    ff = fat_fraction(res['water_real'], res['fat_real'], flip, tr, t1w, t1f, b1)
    ff_signal = res['pdff_uncorrected']
    err = [np.median(ff[labels == i + 1]) - pdff[i] for i in range(9)]
    rerr = [np.median(res['r2s'][labels == i + 1]) - r2s[i] for i in range(9)]
    assert max(abs(e) for e in err) < 1.5, (B0, np.round(err, 2))
    assert all(abs(e) <= max(6, 0.1 * r) for e, r in zip(rerr, r2s)), (B0, np.round(rerr, 1))
    biased = max(abs(np.median(ff_signal[labels == i + 1]) - pdff[i]) for i in range(9))
    magd = max(abs(np.median(fat_fraction(res['water'], res['fat'], flip, tr, t1w, t1f, b1)[labels == i + 1]) - pdff[i]) for i in (0, 8))
    print(f"{B0} T, {len(te)} echoes: max |PDFF error| {max(abs(e) for e in err):.2f} pp, max |R2* error| "
          f"{max(abs(e) for e in rerr):.1f} 1/s (without T1/flip correction {biased:.1f} pp; magnitude discrimination at 0/100 %: {magd:.1f} pp), {time.time() - t0:.1f} s")
    # voxelwise argmin alone swaps some vials (the failure mode the regularized choice prevents)
    if k == 3:
        alt = fit_fat_water(sig, te, off, FAT_AMPLITUDES, mask=labels > 0, penalty=0.0)
        swap = max(abs(np.median(fat_fraction(alt['water_real'], alt['fat_real'], flip, tr, t1w, t1f, b1)[labels == i + 1]) - pdff[i]) for i in range(9))
        assert swap > 1.5, swap
        print(f"  (without the smooth-field choice the worst vial is off by {swap:.1f} pp)")
print("fat-water separation: isolated vials 0-100% fat at 1.5 T and 3 T within 1.5 pp and R2* within max(6 1/s, 10%)")

