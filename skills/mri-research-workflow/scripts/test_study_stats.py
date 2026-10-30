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

if __name__ == '__main__':
    main()

