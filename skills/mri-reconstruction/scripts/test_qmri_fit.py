"""Tests for qmri_fit (python test_qmri_fit.py, a few seconds)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qmri_fit import *

def main():
    rng = np.random.default_rng(0)
    te = np.array([5, 10, 15, 20]) * 1e-3; T2 = rng.uniform(0.01, 0.08, (8, 8)); S0 = rng.uniform(0.5, 2, (8, 8))
    s0, t2 = fit_monoexp(te, S0[..., None] * np.exp(-te / T2[..., None]))
    assert np.allclose(t2, T2, rtol=1e-6) and np.allclose(s0, S0, rtol=1e-6); print('monoexp ok')
    ti = np.array([0.05, 0.15, 0.4, 0.8, 1.6, 3.0]); T1 = rng.uniform(0.3, 2.0, (8, 8)); a = 1.0; b = -1.7   # imperfect inversion
    sig = a + b * np.exp(-ti / T1[..., None])
    t1, aa, bb = fit_inversion_recovery(ti, np.abs(sig)); assert np.allclose(t1, T1, rtol=6e-3), np.max(abs(t1 / T1 - 1)); print('IR magnitude (polarity restored) ok, max rel err %.2e' % np.max(abs(t1 / T1 - 1)))
    t1c, _, _ = fit_inversion_recovery(ti, sig * np.exp(1j * 0.7)); assert np.allclose(t1c, T1, rtol=6e-3); print('IR complex ok')
    naive = -ti / np.log(np.clip((1 - np.abs(sig) / a) / 2, 1e-9, None))   # wrong 2-parameter inversion of |1-2exp| for comparison only
    flips = np.array([3, 8, 15, 25]); tr = 0.015; m0 = 2.0
    t1v, m0v = fit_vfa(flips, tr, ernst_signal(flips, tr, T1[..., None], m0=m0)); assert np.allclose(t1v, T1, rtol=1e-6) and np.allclose(m0v, m0); print('VFA ok')
    on = bssfp_signal(40, 5e-3, 1.0, 0.1, te=0.0); e1, e2 = np.exp(-5e-3 / 1.0), np.exp(-5e-3 / 0.1); a = np.deg2rad(40)
    ref = np.sin(a) * (1 - e1) / (1 - (e1 - e2) * np.cos(a) - e1 * e2); assert abs(abs(on) - ref) < 1e-9, (abs(on), ref); print('bSSFP fixed point matches on-resonance closed form')
    assert abs(abs(bssfp_signal(40, 5e-3, 1.0, 0.1, off_resonance_hz=100.0, te=0)) - ref) > 1e-3; print('bSSFP off-resonance changes the signal (banding) ok')
    grid = np.geomspace(0.1, 3, 400); D = np.array([ir_signal(ti, t, recovery=2.0) for t in grid])
    truth = ir_signal(ti, 0.9, recovery=2.0) * 3.0; p, sc, co = fit_dictionary(truth[None], D, grid[:, None])
    assert abs(p[0, 0] - 0.9) / 0.9 < 0.01 and abs(sc[0] - 3) < 0.05 and co[0] > 0.9999; print('dictionary fit ok')
    print('all qmri_fit tests passed')

if __name__ == '__main__':
    main()

