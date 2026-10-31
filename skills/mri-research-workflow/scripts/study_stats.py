"""MRFoundry study statistics for quantitative-biomarker comparisons (numpy only; python test_study_stats.py).

Rules these helpers enforce or make easy:
- The statistical unit is the SUBJECT (or lesion), not the voxel: summarize each ROI per subject and session first
  (median), then compute AUCs, CIs and repeatability on those values. Report n as the number of subjects.
- Development/test split: choose thresholds, compartments and model settings on development subjects only, then
  apply them unchanged to held-out subjects. threshold_on_dev() makes the separation explicit.
- Uncertainty by resampling subjects (cluster bootstrap): paired comparisons resample the same subjects for both
  biomarkers.
"""
if __name__ == '__main__' and '--api' in __import__('sys').argv:  # signatures only; works without numpy
    import ast as _ast, sys as _sys
    for _n in _ast.parse(open(__file__).read()).body:
        if isinstance(_n, (_ast.FunctionDef, _ast.ClassDef)) and not _n.name.startswith('_'):
            _f = _n if isinstance(_n, _ast.FunctionDef) else next((m for m in _n.body if isinstance(m, _ast.FunctionDef) and m.name == '__init__'), None)
            _a = _ast.unparse(_f.args).replace('self, ', '').replace('self', '') if _f else ''
            _d = (_ast.get_docstring(_n) or '').strip().splitlines()
            print(f"{_n.name}({_a})" + chr(10) + f"    {_d[0] if _d else ''}")
    _sys.exit(0)

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



# ---- sample size, two-group tests and ICC confidence intervals (standard formulas) --------------------------
def _z(p):
    from statistics import NormalDist
    return NormalDist().inv_cdf(p)


def _ceil(x):
    import math
    return int(math.ceil(x - 1e-9))


def n_per_group(delta, sd, alpha=0.05, power=0.8, sided=2, exact=False):
    """Evaluable participants PER GROUP for two independent groups of equal size:
    n = ceil(2 ((z_{1-alpha/sided} + z_{1-beta}) sd / delta)^2), beta = 1 - power (normal approximation). sd: within-group
    (between-participant) SD of ONE measurement per participant. exact=True: smallest n whose noncentral-t power
    (df = 2n - 2) reaches 'power' (needs scipy). Rounds up only once, at the end."""
    za, zb = _z(1 - alpha / sided), _z(power)
    n = _ceil(2 * ((za + zb) * sd / delta) ** 2)
    if not exact:
        return n
    from scipy.stats import nct, t as tdist
    m = max(2, n - 3)
    while True:
        df = 2 * m - 2; nc = abs(delta) / (sd * np.sqrt(2.0 / m)); tc = tdist.ppf(1 - alpha / sided, df)
        pw = 1 - nct.cdf(tc, df, nc) + (nct.cdf(-tc, df, nc) if sided == 2 else 0)
        if pw >= power:
            return int(m)
        m += 1


def n_paired(delta, sd_diff, alpha=0.05, power=0.8, sided=2, exact=False):
    """Evaluable participants for a paired / crossover comparison: n = ceil(((z_{1-alpha/sided} + z_{1-beta}) sd_diff / delta)^2).
    sd_diff: SD of each participant's difference between the two conditions (sqrt(2) times the within-subject SD
    when both conditions carry the test-retest variability; see sd_of_differences). exact=True: noncentral t, df = n - 1."""
    za, zb = _z(1 - alpha / sided), _z(power)
    n = _ceil(((za + zb) * sd_diff / delta) ** 2)
    if not exact:
        return n
    from scipy.stats import nct, t as tdist
    m = max(2, n - 3)
    while True:
        df = m - 1; nc = abs(delta) / (sd_diff / np.sqrt(m)); tc = tdist.ppf(1 - alpha / sided, df)
        pw = 1 - nct.cdf(tc, df, nc) + (nct.cdf(-tc, df, nc) if sided == 2 else 0)
        if pw >= power:
            return int(m)
        m += 1


def sd_of_differences(within_subject_sd):
    """SD of a within-participant difference of two measurements that each carry the within-subject SD: sqrt(2) wSD."""
    return float(np.sqrt(2.0) * within_subject_sd)


def combined_fraction(fractions):
    """Probability that a participant is lost to at least one of several independent causes: 1 - (1 - f1)(1 - f2)..."""
    return float(1 - np.prod([1 - float(p) for p in fractions]))


def inflate_for_loss(n_needed, loss_fraction):
    """Participants to recruit so that n_needed remain after a fraction loss_fraction is lost: ceil(n / (1 - loss))."""
    return _ceil(n_needed / (1 - float(loss_fraction)))


def n_total_unbalanced(n_needed_per_group, minority_share, loss_fraction=0.0):
    """Recruitment when group membership is only known after enrolment (a test result splits participants):
    ceil(n / (minority_share x (1 - loss_fraction))) participants so that the SMALLER group reaches n."""
    return _ceil(n_needed_per_group / (float(minority_share) * (1 - float(loss_fraction))))


def pooled_sd(a, b):
    """Pooled within-group SD sqrt(((n1-1) s1^2 + (n2-1) s2^2) / (n1 + n2 - 2)) with sample variances (ddof 1)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    return float(np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)))


def two_sample_t(a, b, ci=0.95, welch=False):
    """Difference mean(a) - mean(b) with a pooled-variance (welch=False) or Welch (welch=True) t interval, t, df,
    two-sided p, pooled SD and Hedges g (J = 1 - 3/(4 (n1 + n2) - 9)). One value per participant in each group."""
    from scipy.stats import t as tdist
    a = np.asarray(a, float); b = np.asarray(b, float); n1, n2 = len(a), len(b); d = a.mean() - b.mean()
    v1, v2 = a.var(ddof=1), b.var(ddof=1); sp = pooled_sd(a, b)
    if welch:
        se = np.sqrt(v1 / n1 + v2 / n2); df = (v1 / n1 + v2 / n2) ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    else:
        se = sp * np.sqrt(1 / n1 + 1 / n2); df = n1 + n2 - 2
    q = tdist.ppf(1 - (1 - ci) / 2, df); t = d / se
    g = d / sp * (1 - 3 / (4 * (n1 + n2) - 9))
    return {'difference': float(d), 'ci': [float(d - q * se), float(d + q * se)], 't': float(t), 'df': float(df),
            'p': float(2 * tdist.sf(abs(t), df)), 'pooled_sd': sp, 'hedges_g': float(g), 'n': [n1, n2]}


def icc_ci(data, form='2,1', ci=0.95):
    """ICC with its F-based confidence interval for an (n subjects x k sessions/raters) array, complete data.
    Forms as in icc(): '1,1' one-way; '2,1' two-way random, absolute agreement (Shrout & Fleiss 1979; McGraw & Wong
    1996 ICC(A,1)); '3,1' two-way mixed, consistency; '1,k', '2,k', '3,k' for the mean of k measurements ('2,k'
    bounds by Spearman-Brown of the '2,1' bounds). Returns (icc, (lo, hi)). Average regions or repeats per
    session first if the endpoint is their mean."""
    from scipy.stats import f as fdist
    Y = np.asarray(data, float); n, k = Y.shape; a = (1 - ci) / 2
    gm = Y.mean(); rm = Y.mean(1); cm = Y.mean(0)
    msr = k * np.sum((rm - gm) ** 2) / (n - 1); msc = n * np.sum((cm - gm) ** 2) / (k - 1)
    mse = np.sum((Y - rm[:, None] - cm[None, :] + gm) ** 2) / ((n - 1) * (k - 1)); msw = np.sum((Y - rm[:, None]) ** 2) / (n * (k - 1))
    f = form.replace(' ', ''); est = float(icc(Y, f))
    if f in ('1,1', '1,k'):
        F = msr / msw; df1, df2 = n - 1, n * (k - 1)
    elif f in ('3,1', '3,k'):
        F = msr / mse; df1, df2 = n - 1, (n - 1) * (k - 1)
    if f in ('1,1', '3,1', '1,k', '3,k'):
        FL = F / fdist.ppf(1 - a, df1, df2); FU = F * fdist.ppf(1 - a, df2, df1)
        if f.endswith(',1'):
            return est, (float((FL - 1) / (FL + k - 1)), float((FU - 1) / (FU + k - 1)))
        return est, (float(1 - 1 / FL), float(1 - 1 / FU))
    if f in ('2,1', '2,k'):
        r = icc(Y, '2,1'); aa = k * r / (n * (1 - r)); bb = 1 + k * r * (n - 1) / (n * (1 - r))
        v = (aa * msc + bb * mse) ** 2 / ((aa * msc) ** 2 / (k - 1) + (bb * mse) ** 2 / ((n - 1) * (k - 1)))
        Fs = fdist.ppf(1 - a, n - 1, v); Fss = fdist.ppf(1 - a, v, n - 1)
        lo = n * (msr - Fs * mse) / (Fs * (k * msc + (k * n - k - n) * mse) + n * msr)
        hi = n * (Fss * msr - mse) / (k * msc + (k * n - k - n) * mse + n * Fss * msr)
        if f == '2,k':
            lo, hi = k * lo / (1 + (k - 1) * lo), k * hi / (1 + (k - 1) * hi)
        return est, (float(lo), float(hi))
    raise ValueError(form)

