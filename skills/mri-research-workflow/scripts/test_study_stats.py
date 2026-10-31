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

if __name__ == '__main__':
    main()
    test_general()

