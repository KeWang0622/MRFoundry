"""MRFoundry study statistics for quantitative-biomarker comparisons (numpy only; python test_study_stats.py).

Rules these helpers enforce or make easy:
- The statistical unit is the SUBJECT (or lesion), not the voxel: summarize each ROI per subject and session first
  (median), then compute AUCs, CIs and repeatability on those values. Report n as the number of subjects.
- Development/test split: choose thresholds, compartments and model settings on development subjects only, then
  apply them unchanged to held-out subjects. threshold_on_dev() makes the separation explicit.
- Uncertainty by resampling subjects (cluster bootstrap): paired comparisons resample the same subjects for both
  biomarkers.
"""
import numpy as np

def auc(pos, neg):
    """Mann-Whitney AUC (probability a positive value exceeds a negative one; ties count 1/2)."""
    p = np.asarray(pos, float)[:, None]; n = np.asarray(neg, float)[None, :]
    return float(((p > n).sum() + 0.5 * (p == n).sum()) / (p.size * n.size))

def subject_bootstrap(values_by_subject, stat, n_boot=2000, seed=0, ci=0.95):
    """values_by_subject: dict subject -> object passed to stat(list_of_objects). Resamples subjects with replacement.
    Returns (estimate, (lo, hi), n_subjects)."""
    subs = sorted(values_by_subject); rng = np.random.default_rng(seed); est = stat([values_by_subject[s] for s in subs]); bs = []
    for _ in range(n_boot):
        pick = rng.choice(len(subs), len(subs), replace=True); v = stat([values_by_subject[subs[i]] for i in pick])
        if np.isfinite(v): bs.append(v)
    a = (1 - ci) / 2; return float(est), (float(np.quantile(bs, a)), float(np.quantile(bs, 1 - a))), len(subs)

def roi_auc_by_subject(per_subject, biomarker, higher_in_lesion=True):
    """per_subject: {subject: {'lesion': value, 'normal': value, ...}} (one summary value per ROI). Returns AUC over subjects."""
    les = [d['lesion'][biomarker] if isinstance(d['lesion'], dict) else d['lesion'] for d in per_subject]
    nor = [d['normal'][biomarker] if isinstance(d['normal'], dict) else d['normal'] for d in per_subject]
    return auc(les, nor) if higher_in_lesion else auc(nor, les)

def icc_3_1(test, retest):
    """Two-way mixed, consistency, single measurement ICC(3,1) for paired test/retest values (one per subject/ROI)."""
    Y = np.stack([np.asarray(test, float), np.asarray(retest, float)], 1); n, k = Y.shape; gm = Y.mean()
    ssr = k * ((Y.mean(1) - gm) ** 2).sum(); ssc = n * ((Y.mean(0) - gm) ** 2).sum(); sse = ((Y - gm) ** 2).sum() - ssr - ssc
    msr = ssr / (n - 1); mse = sse / ((n - 1) * (k - 1)); return float((msr - mse) / (msr + (k - 1) * mse))

def within_subject_cv(test, retest):
    """Within-subject coefficient of variation sqrt(mean(d^2/2)) / mean, and repeatability coefficient 2.77*sw."""
    a = np.asarray(test, float); b = np.asarray(retest, float); sw = np.sqrt(np.mean((a - b) ** 2 / 2))
    return float(sw / np.mean((a + b) / 2)), float(2.77 * sw)

def threshold_on_dev(dev_pos, dev_neg):
    """Youden-optimal threshold chosen on DEVELOPMENT values only (positive = higher). Apply unchanged to test data."""
    v = np.unique(np.r_[dev_pos, dev_neg]); best, thr = -1, None
    for t in (v[:-1] + v[1:]) / 2 if len(v) > 1 else v:
        j = np.mean(np.asarray(dev_pos) > t) + np.mean(np.asarray(dev_neg) <= t) - 1
        if j > best: best, thr = j, float(t)
    return thr



# ---- general repeatability and paired-comparison statistics (standard formulas) ----------------------------
def icc(data, form='3,1'):
    """Intraclass correlation for an (n subjects x k sessions/raters) array (Shrout & Fleiss 1979; McGraw & Wong 1996).
    form: '1,1' one-way random; '2,1' two-way random, absolute agreement; '3,1' two-way mixed, consistency;
    append 'k' (e.g. '2,k') for the reliability of the mean of k measurements. State the form you report."""
    Y = np.asarray(data, float); n, k = Y.shape
    gm = Y.mean(); rm = Y.mean(1); cm = Y.mean(0)
    msr = k * np.sum((rm - gm) ** 2) / (n - 1)
    msc = n * np.sum((cm - gm) ** 2) / (k - 1)
    sse = np.sum((Y - rm[:, None] - cm[None, :] + gm) ** 2); mse = sse / ((n - 1) * (k - 1))
    msw = np.sum((Y - rm[:, None]) ** 2) / (n * (k - 1))
    f = form.replace(' ', '')
    if f == '1,1': return (msr - msw) / (msr + (k - 1) * msw)
    if f == '2,1': return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    if f == '3,1': return (msr - mse) / (msr + (k - 1) * mse)
    if f == '1,k': return (msr - msw) / msr
    if f == '2,k': return (msr - mse) / (msr + (msc - mse) / n)
    if f == '3,k': return (msr - mse) / msr
    raise ValueError(form)


def repeatability(data, ci=0.95):
    """Within-subject SD, CV and repeatability coefficient for (n subjects x k >= 2 sessions).
    sw^2 = mean within-subject variance (ddof 1); chi-square CI for sw with n(k-1) degrees of freedom;
    wCV_rms = sqrt(mean(var_i / mean_i^2)); RC = 2.77 sw (Bland & Altman 1996)."""
    from scipy.stats import chi2
    Y = np.asarray(data, float); n, k = Y.shape
    v = Y.var(1, ddof=1); m = Y.mean(1); sw = np.sqrt(v.mean()); df = n * (k - 1); a = (1 - ci) / 2
    return {'sw': float(sw), 'sw_ci': [float(sw * np.sqrt(df / chi2.ppf(1 - a, df))), float(sw * np.sqrt(df / chi2.ppf(a, df)))],
            'wcv_rms': float(np.sqrt(np.mean(v / m ** 2))), 'wcv_pooled': float(sw / m.mean()), 'rc': float(2.77 * sw), 'df': int(df)}


def paired_difference(a, b, ci=0.95):
    """Paired comparison of a - b (one value per subject): mean, t-based CI, Cohen's dz and two-sided p."""
    from scipy.stats import t as tdist
    d = np.asarray(a, float) - np.asarray(b, float); n = len(d); sd = d.std(ddof=1); se = sd / np.sqrt(n)
    q = tdist.ppf(1 - (1 - ci) / 2, n - 1); tt = d.mean() / se if se > 0 else np.inf
    return {'mean': float(d.mean()), 'ci': [float(d.mean() - q * se), float(d.mean() + q * se)], 'dz': float(d.mean() / sd) if sd > 0 else float('inf'),
            't': float(tt), 'p': float(2 * tdist.sf(abs(tt), n - 1)), 'n': int(n), 'df': int(n - 1)}


def bland_altman(a, b):
    """Bias and 95% limits of agreement of a - b."""
    d = np.asarray(a, float) - np.asarray(b, float); s = d.std(ddof=1)
    return {'bias': float(d.mean()), 'loa': [float(d.mean() - 1.96 * s), float(d.mean() + 1.96 * s)], 'n': int(len(d))}


def balanced_accuracy(y_true, y_pred):
    """Mean of sensitivity and specificity for binary labels (compute at the declared unit, e.g. one value per subject)."""
    t = np.asarray(y_true, bool); p = np.asarray(y_pred, bool)
    return float((np.mean(p[t]) + np.mean(~p[~t])) / 2)
