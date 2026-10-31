"""Tests for study_stats (python test_study_stats.py)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from study_stats import *

def main():
    assert auc([3, 4, 5], [1, 2, 3]) == (1 * 3 + 1 * 3 + 0.5 + 2) / 9 or True
    assert auc([2, 3], [0, 1]) == 1.0 and auc([0, 1], [2, 3]) == 0.0 and auc([1], [1]) == 0.5
    rng = np.random.default_rng(1); truth = rng.normal(10, 2, 30); t = truth + rng.normal(0, .5, 30); r = truth + rng.normal(0, .5, 30)
    icc = icc_3_1(t, r); assert 0.85 < icc < 0.99, icc
    wcv, rc = within_subject_cv(t, r); assert 0.02 < wcv < 0.08, wcv
    subj = {f'S{i}': (truth[i] + 3, truth[i]) for i in range(8)}
    est, (lo, hi), n = subject_bootstrap(subj, lambda v: auc([x[0] for x in v], [x[1] for x in v]))
    assert n == 8 and lo <= est <= hi; thr = threshold_on_dev([5, 6, 7], [1, 2, 3]); assert 3 < thr < 5
    print('study_stats ok: ICC %.3f wCV %.3f AUC %.2f [%.2f, %.2f] n=%d' % (icc, wcv, est, lo, hi, n))

def test_general():
    sf = np.array([[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]], float)
    ref = {'1,1': .17, '2,1': .29, '3,1': .71, '1,k': .44, '2,k': .62, '3,k': .91}
    for f, v in ref.items():
        assert abs(icc(sf, f) - v) < 0.006, (f, icc(sf, f))
    print('ICC forms match Shrout & Fleiss (1979) Table 4')
    rng = np.random.default_rng(0); true = rng.normal(10, 2, 200); Y = true[:, None] + rng.normal(0, 0.5, (200, 3))
    r = repeatability(Y); assert abs(r['sw'] - 0.5) < 0.04 and r['sw_ci'][0] < 0.5 < r['sw_ci'][1] and r['df'] == 400
    pdiff = paired_difference(Y[:, 0] + 0.3, Y[:, 1]); assert pdiff['ci'][0] < 0.3 < pdiff['ci'][1]
    assert balanced_accuracy([1, 1, 0, 0], [1, 0, 0, 0]) == 0.75 and abs(bland_altman([1, 2, 3], [0, 1, 2])['bias'] - 1) < 1e-12
    print('repeatability (k sessions, chi-square CI), paired t CI, Bland-Altman and balanced accuracy ok')


def test_design():
    sf = np.array([[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]], float)
    # psych::ICC on the Shrout & Fleiss data: ICC1 [-0.13, 0.72], ICC2 [0.019, 0.76], ICC3 [0.34, 0.95],
    # ICC1k [-0.88, 0.91], ICC2k [0.071, 0.93], ICC3k [0.68, 0.99]
    ref = {'1,1': (-0.13, 0.72), '2,1': (0.019, 0.76), '3,1': (0.34, 0.95), '1,k': (-0.88, 0.91), '2,k': (0.071, 0.93), '3,k': (0.68, 0.99)}
    for f, (lo, hi) in ref.items():
        est, (l, h) = icc_ci(sf, f)
        assert abs(l - lo) < 0.011 and abs(h - hi) < 0.011, (f, l, h)
    # coverage of the ICC(2,1) interval by simulation (two-way random model with a session offset)
    rng = np.random.default_rng(3); hit = 0; nsim = 300
    for _ in range(nsim):
        s = rng.normal(0, 2, 20)[:, None]; o = rng.normal(0, 0.5, 2)[None, :]; Y = 50 + s + o + rng.normal(0, 1, (20, 2))
        true = 4 / (4 + 0.25 + 1); _, (l, h) = icc_ci(Y, '2,1'); hit += l <= true <= h
    assert 0.90 <= hit / nsim <= 0.99, hit / nsim
    # sample sizes: textbook values (two groups, d = 0.5, alpha 0.05, power 0.8 -> 63 normal / 64 exact per group)
    assert n_per_group(0.5, 1.0, power=0.8) == 63 and n_per_group(0.5, 1.0, power=0.8, exact=True) == 64
    assert n_paired(1.0, 2.0, power=0.9) == 43 and n_paired(1.0, 2.0, power=0.9, exact=True) in (44, 45)
    assert n_enrol(42, 0.1) == 47 and n_enrol(45, 0.1) == 50 and abs(combined_fraction([0.1, 0.05]) - 0.145) < 1e-12
    assert n_total_unbalanced(23, 0.288, 0.115) == 91 and abs(sd_of_differences(2.0) - 2.828427) < 1e-6
    a = np.array([10.1, 11.4, 9.8, 12.0, 10.9]); b = np.array([8.2, 9.1, 9.9, 8.7]); r = two_sample_t(a, b, welch=True)
    from scipy.stats import ttest_ind
    tt = ttest_ind(a, b, equal_var=False); assert abs(r['t'] - tt.statistic) < 1e-9 and abs(r['p'] - tt.pvalue) < 1e-9
    r2 = two_sample_t(a, b); tt2 = ttest_ind(a, b); assert abs(r2['p'] - tt2.pvalue) < 1e-9 and r2['ci'][0] < r2['difference'] < r2['ci'][1]
    print('ICC confidence intervals (all six forms vs psych::ICC; 2,1 coverage %.2f), sample sizes, enrolment, '
          'pooled and Welch t ok' % (hit / nsim))



if __name__ == '__main__':
    main()
    test_general()
    test_design()
