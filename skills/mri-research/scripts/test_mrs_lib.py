#!/usr/bin/env python3
"""Tests for mrs_lib (python test_mrs_lib.py, a few seconds). Synthetic singlet/multiplet basis at textbook shifts."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrs_lib import *

rng = np.random.default_rng(3)
n, dwell, f0, carrier = 2048, 2.5e-4, 123.2e6, 4.7
t = np.arange(n) * dwell
def lines(peaks, decay=2 * np.pi * 1.0):
    """peaks: list of (ppm, protons). Basis = 1 mmol/L, all protons, intrinsic Lorentzian decay."""
    return sum(nh * np.exp(2j * np.pi * (d - carrier) * f0 * 1e-6 * t) for d, nh in peaks) * np.exp(-decay * t)
basis = {'NAA': lines([(2.01, 3), (2.49, 1), (2.67, 1)]), 'Cr': lines([(3.03, 3), (3.92, 2)]),
         'Cho': lines([(3.20, 9), (3.53, 2)]), 'mI': lines([(3.53, 2), (3.61, 2), (4.06, 1), (3.27, 1)]),
         'Glu': lines([(2.04, 1), (2.12, 1), (2.34, 2), (3.74, 1)])}
basis['MM'] = sum(a * np.exp(2j * np.pi * (d - carrier) * f0 * 1e-6 * t) for d, a in [(0.9, 3), (1.3, 3), (2.0, 2)]) * np.exp(-60 * t)

# ppm axis convention
sp = np.abs(spectrum(basis['NAA'])); ax = ppm_axis(n, dwell, f0, carrier)
assert abs(ax[np.argmax(sp)] - 2.01) < 0.01
print("ppm_axis/spectrum put a +delta resonance at +delta ppm")

# simulate a voxel: tissue fractions, relaxation, broadening, drift, phase jitter, residual water, noise, scale factors
TR, TE = 2.0, 0.03
conc_tissue = {'NAA': 11.0, 'Cr': 7.5, 'Cho': 1.8, 'mI': 5.5, 'Glu': 9.0}
frac = {'gm': 0.5, 'wm': 0.35, 'csf': 0.15}; wc = {'gm': 43300.0, 'wm': 35880.0, 'csf': 55556.0}
rel_w = {'gm': relaxation_attenuation(TR, TE, 1.82, 0.10), 'wm': relaxation_attenuation(TR, TE, 1.08, 0.07),
         'csf': relaxation_attenuation(TR, TE, 4.16, 0.50)}
rel_m = relaxation_attenuation(TR, TE, 1.4, 0.25)
tissue = frac['gm'] + frac['wm']
broad = np.exp(-2 * np.pi * 2.0 * t - (2 * np.pi * 2.5) ** 2 * t ** 2 / 4)
clean = sum(conc_tissue[k] * tissue * rel_m * basis[k] for k in conc_tissue) * broad + 2.0 * basis['MM'] * broad
clean = clean + 3000.0 * np.exp(2j * np.pi * (4.68 - carrier) * f0 * 1e-6 * t) * np.exp(-40 * t)     # residual water
water = 2 * sum(frac[c] * wc[c] * rel_w[c] for c in frac) * np.exp(-2 * np.pi * 1.0 * t) * broad
sc_m, sc_w, ntr = 3.7e-3, 2.1e-5, 32
def transients(x, sc, k, noise):
    out = []
    for _ in range(k):
        df, ph = rng.normal(0, 3.0), rng.normal(0, 0.3)
        out.append(sc * (x * np.exp(1j * (2 * np.pi * df * t + ph)) + noise * (rng.normal(size=n) + 1j * rng.normal(size=n))))
    return np.array(out)
met = transients(clean, sc_m, ntr, 6.0); wat = transients(water, sc_w, 4, 6.0)

met_al, dfs, phs = spectral_registration(met / sc_m, dwell)
assert np.std(np.diff(dfs)) > 1.0                       # drift was present and estimated
fit = lcm_fit(met_al.mean(0), basis, dwell, f0, carrier, ppm_range=(0.2, 4.2))
wamp = water_amplitude(spectral_registration(wat / sc_w, dwell)[0].mean(0), dwell)
est = {k: water_referenced_concentration(fit['amplitudes'][k], wamp, rel_m, frac, wc, rel_w) for k in conc_tissue}
err = {k: est[k] / conc_tissue[k] - 1 for k in conc_tissue}
assert all(abs(e) < 0.06 for e in err.values()), err
print("aligned, fitted and water-referenced concentrations: " + ", ".join(f"{k} {e:+.1%}" for k, e in err.items()))
# common scaling errors are large: forgetting the scale factors or the tissue fraction
bad = water_referenced_concentration(fit['amplitudes']['NAA'] * sc_m, wamp * sc_w, rel_m, frac, wc, rel_w)
assert abs(bad / conc_tissue['NAA'] - 1) > 0.5
vox = water_referenced_concentration(fit['amplitudes']['NAA'], wamp, rel_m, frac, wc, rel_w, metabolite_compartments=('gm', 'wm', 'csf'))
assert abs(vox / est['NAA'] - tissue) < 1e-9
print("stored scale factors left in, or CSF counted as metabolite tissue, give large errors (shown)")
print("all mrs_lib tests passed")

