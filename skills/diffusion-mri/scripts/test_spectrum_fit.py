"""Self-test for spectrum_fit.py (python test_spectrum_fit.py).

Values below are an arbitrary synthetic example (not taken from any organ, protocol or study):
1. an unregularized fine-grid NNLS spectrum is less stable than a regularized spectrum or a few atoms;
2. a misplaced fixed atom biases high-fraction tissue although pooled bias can look small;
3. calibrating the basis on pooled development curves finds a better atom and lowers the worst-group bias.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spectrum_fit import *

b = np.repeat([0, 150, 400, 900, 1600, 2500, 3500], [2, 3, 4, 4, 6, 6, 6]).astype(float)
cut = 0.9e-3
grid = np.geomspace(1e-5, 4e-3, 400)
def logn(med, s):
    w = np.exp(-.5 * ((np.log(grid) - np.log(med)) / s) ** 2)
    return w / w.sum()
COMP = np.stack([logn(0.42e-3, .3), logn(1.5e-3, .2), logn(3.0e-3, .05)])
def make(rng, n, b, lo=(0.05, 0.25), hi=(0.45, 0.75)):
    g = rng.integers(0, 2, n)
    fs = np.where(g == 0, rng.uniform(*lo, n), rng.uniform(*hi, n))
    ff = rng.uniform(0.05, 0.15, n)
    f = np.stack([fs, 1 - fs - ff, ff], 1)
    w = f @ COMP
    return w @ np.exp(-np.outer(grid, b)), (w[:, grid < cut]).sum(1), np.where(g == 0, 'low', 'high')

few = [0.42e-3, 1.5e-3, 3.0e-3]
fine = np.geomspace(5e-5, 3.5e-3, 60)
r_few = recovery_test(lambda r, n, b: make(r, n, b)[:2], lambda M, b: fraction_below(fit_weights(M, b, few), few, cut), b, 0.02, n=600)
r_fine = recovery_test(lambda r, n, b: make(r, n, b)[:2], lambda M, b: fraction_below(fit_weights(M, b, fine), fine, cut), b, 0.02, n=600)
r_reg = recovery_test(lambda r, n, b: make(r, n, b)[:2], lambda M, b: fraction_below(fit_weights(M, b, fine, lam=0.05, smooth=True), fine, cut), b, 0.02, n=600)
assert r_few['sd'] < r_fine['sd'] and r_reg['sd'] < r_fine['sd'], (r_few, r_fine, r_reg)
print('spread: few atoms %.3f, regularized fine grid %.3f, unregularized fine grid %.3f' % (r_few['sd'], r_reg['sd'], r_fine['sd']))

# development curves: tissue-class averages from separate development data (high SNR after averaging)
rng = np.random.default_rng(7)
dev = []
for lo, hi in [((0.08, 0.12), (0.08, 0.12)), ((0.25, 0.3), (0.25, 0.3)), ((0.6, 0.65), (0.6, 0.65))]:
    S, _, _ = make(rng, 400, b, lo, hi)
    dev.append(np.abs(S + rng.normal(0, .02, S.shape) + 1j * rng.normal(0, .02, S.shape)).mean(0))
cands = {f'slow={d * 1e3:.2f}': [d, 1.5e-3, 3.0e-3] for d in [0.2e-3, 0.3e-3, 0.42e-3, 0.55e-3, 0.7e-3]}
cal = calibrate_basis(np.array(dev), b, cands, lambda w, D: fraction_below(w, D, cut), sigma=0.02 / np.sqrt(400))
print('calibration ranking:', [(e['name'], round(e['residual_rms'], 5)) for e in cal['ranked']])
assert cal['best'] == 'slow=0.42', cal['best']

def strat(D):
    return stratified_recovery_test(make, lambda M, bb: fraction_below(fit_fixed_basis(M, bb, D), D, cut), b, 0.02, n=1500, seed=3)
s_bad, s_good = strat([0.2e-3, 1.5e-3, 3.0e-3]), strat(cands[cal['best']])
print('misplaced atom: pooled bias %+.3f, groups %s, worst %.3f' % (s_bad['bias'], {k: round(v['bias'], 3) for k, v in s_bad['groups'].items()}, s_bad['worst_abs_bias']))
print('calibrated atom: pooled bias %+.3f, groups %s, worst %.3f' % (s_good['bias'], {k: round(v['bias'], 3) for k, v in s_good['groups'].items()}, s_good['worst_abs_bias']))
assert s_good['worst_abs_bias'] < s_bad['worst_abs_bias'] and abs(s_bad['groups']['high']['bias']) > abs(s_bad['groups']['low']['bias'])
print('ok')

# Conventional ADC range
S = np.exp(-np.array([0, 0, 500, 1000, 1500, 2000, 3000]) * 1.5e-3)[None] * 0.5 + np.exp(-np.array([0, 0, 500, 1000, 1500, 2000, 3000]) * 0.3e-3)[None] * 0.5
bb = np.array([0, 0, 500, 1000, 1500, 2000, 3000])
a1 = adc_fit(S, bb, bmax=1000)[0]; a_all = adc_fit(S, bb, bmax=3000)[0]
assert a_all < a1, (a1, a_all)
print('adc_fit: ADC(b<=1000) %.2e mm2/s vs all shells %.2e' % (a1, a_all))


# B5: voxelwise test-retest stability from two noise realizations
st_fine = stratified_recovery_test(lambda r, n, b: make(r, n, b)[:2], lambda M, b: fraction_below(fit_weights(M, b, fine), fine, cut), b, 0.02, n=600, retest_tol=0.1)
st_reg = stratified_recovery_test(lambda r, n, b: make(r, n, b)[:2], lambda M, b: fraction_below(fit_weights(M, b, fine, lam=0.05, smooth=True), fine, cut), b, 0.02, n=600, retest_tol=0.1)
assert st_reg['retest_frac_over_tol'] < st_fine['retest_frac_over_tol']
print(f"retest check: unregularized fine grid {st_fine['retest_frac_over_tol']:.2f} vs regularized {st_reg['retest_frac_over_tol']:.2f} of voxels change by > 0.1")
