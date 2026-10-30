"""MRFoundry helpers for signal-fraction / diffusivity-spectrum fits (numpy + scipy).

Fits of exp(-b D) mixtures are ill-conditioned. Calibrate fixed settings on development data
(calibrate_basis), check identifiability, and use stratified recovery tests before trusting fractions.
"""
import numpy as np
from scipy.optimize import nnls

def background_sigma(magnitude, background_mask):
    """Gaussian noise sigma from magnitude background (Rayleigh mean / sqrt(pi/2))."""
    v = np.asarray(magnitude)[np.asarray(background_mask, bool)]
    return float(v.mean() / np.sqrt(np.pi / 2))

def floor_correct(magnitude, sigma):
    """Second-moment Rician correction sqrt(max(M^2 - 2 sigma^2, 0)); reduces high-b noise-floor bias."""
    m = np.asarray(magnitude, float)
    return np.sqrt(np.clip(m ** 2 - 2 * sigma ** 2, 0, None))

def fit_weights(signals, bvals, diffusivities, lam=0.0, smooth=False, normalize_b0=True):
    """Nonnegative weights w (n_voxels, n_basis) for signals ~ sum_j w_j exp(-b D_j).
    lam > 0 adds Tikhonov (smooth=False) or second-difference (smooth=True) regularization.
    With normalize_b0, signals are divided by their mean b=0 value first; weights then sum to ~1."""
    b = np.asarray(bvals, float); D = np.asarray(diffusivities, float); Y = np.atleast_2d(np.asarray(signals, float))
    if normalize_b0:
        b0 = Y[:, b < 1e-6 + b.min()].mean(1, keepdims=True); Y = Y / np.clip(b0, 1e-12, None)
    A = np.exp(-np.outer(b, D)); R = np.diff(np.eye(len(D)), 2, axis=0) if smooth else np.eye(len(D))
    if lam > 0: A = np.vstack([A, np.sqrt(lam) * R])
    pad = np.zeros(R.shape[0]) if lam > 0 else np.zeros(0)
    return np.array([nnls(A, np.concatenate([y, pad]))[0] for y in Y])

def fraction_below(weights, diffusivities, cutoff):
    """Fraction of total weight in basis components with D < cutoff."""
    w = np.asarray(weights); D = np.asarray(diffusivities)
    return w[:, D < cutoff].sum(1) / np.clip(w.sum(1), 1e-12, None)

def recovery_test(make_truth, fit_fn, bvals, sigma, n=2000, seed=0):
    """Generic recovery test.
    make_truth(rng, n, bvals) -> (noise-free signals (n, n_b) with S(b=0)~1, true target (n,))
    fit_fn(magnitude_signals, bvals) -> estimated target (n,)
    Adds complex Gaussian noise (Rician magnitude) of std sigma and returns bias, spread, r, median |error|.
    Generate truth from tissue models that differ from the fitting basis."""
    rng = np.random.default_rng(seed)
    S, truth = make_truth(rng, n, np.asarray(bvals, float))
    M = np.abs(S + rng.normal(0, sigma, S.shape) + 1j * rng.normal(0, sigma, S.shape))
    est = np.asarray(fit_fn(M, np.asarray(bvals, float)), float); err = est - truth
    r = float(np.corrcoef(est, truth)[0, 1]) if est.std() > 0 and truth.std() > 0 else float('nan')
    return {'bias': float(err.mean()), 'sd': float(err.std()), 'r': r, 'median_abs_error': float(np.median(np.abs(err))), 'n': int(n)}


def adc_fit(signals, bvals, bmax=1000.0, bmin=0.0):
    """Conventional mono-exponential ADC from b in [bmin, bmax] only (clinical convention b <= 1000 s/mm^2;
    higher b values bend the curve through kurtosis/restriction and lower the ADC). Log-linear least squares per
    voxel over all directions/repeats of the selected shells. signals (n_vox, n_b) magnitude; returns ADC in the
    inverse units of bvals (s/mm^2 -> mm^2/s; multiply by 1e3 for um^2/ms)."""
    b = np.asarray(bvals, float); keep = (b >= bmin - 1e-6) & (b <= bmax + 1e-6)
    if len(np.unique(np.round(b[keep]))) < 2: raise ValueError('need at least two distinct b-values within the ADC range')
    Y = np.log(np.clip(np.atleast_2d(np.asarray(signals, float))[:, keep], 1e-12, None)); A = np.stack([np.ones(keep.sum()), -b[keep]], 1)
    coef, *_ = np.linalg.lstsq(A, Y.T, rcond=None)
    return coef[1]


def fit_fixed_basis(signals, bvals, diffusivities, sigma=None, normalize_b0=True):
    """NNLS fit on a fixed set of compartment diffusivities (any number of compartments), with optional
    Rician floor correction. Returns weights normalized to sum 1 per voxel. Choose the basis with
    calibrate_basis on development data and confirm it with stratified_recovery_test; do not copy
    diffusivities from examples or from a different organ, field or protocol."""
    S = np.atleast_2d(np.asarray(signals, float))
    if sigma is not None:
        S = floor_correct(S, sigma)
    w = fit_weights(S, bvals, diffusivities, normalize_b0=normalize_b0)
    return w / np.clip(w.sum(1, keepdims=True), 1e-12, None)


def calibrate_basis(dev_curves, bvals, candidates, target_fn, sigma=None, rel_tol=0.10):
    """Compare candidate fixed bases on pooled DEVELOPMENT curves and diagnose identifiability.

    dev_curves: (n_curves, n_b) ROI- or tissue-class-averaged development signals (averaging gives high
    SNR; keep groups that the study compares, e.g. one curve per tissue class and subject).
    candidates: dict name -> diffusivity array. target_fn(weights, diffusivities) -> target per curve
    (e.g. lambda w, D: fraction_below(w, D, cutoff)).
    Returns a list sorted by pooled normalized residual. Each entry has the residual per curve and per
    b-value (look for systematic patterns), the target per curve and 'near_best' (residual within
    (1 + rel_tol) of the best). 'identifiability' reports, per curve, the spread of the target among
    near-best candidates: if it exceeds the tolerance that matters for the study, the data cannot fix
    that parameter; increase flexibility (regularized spectrum, more atoms) or report the dependence."""
    b = np.asarray(bvals, float)
    Y = np.atleast_2d(np.asarray(dev_curves, float))
    if sigma is not None:
        Y = floor_correct(Y, sigma)
    b0 = Y[:, b < 1e-6 + b.min()].mean(1, keepdims=True)
    Yn = Y / np.clip(b0, 1e-12, None)
    out = []
    for name, D in candidates.items():
        D = np.asarray(D, float)
        w = fit_weights(Yn, b, D, normalize_b0=False)
        pred = w @ np.exp(-np.outer(D, b))
        res = Yn - pred
        out.append({'name': name, 'diffusivities': D.tolist(),
                    'residual_rms': float(np.sqrt(np.mean(res ** 2))),
                    'residual_rms_per_curve': np.sqrt(np.mean(res ** 2, 1)).tolist(),
                    'mean_residual_per_b': res.mean(0).tolist(),
                    'target_per_curve': np.asarray(target_fn(w, D), float).tolist()})
    out.sort(key=lambda e: e['residual_rms'])
    best = out[0]['residual_rms']
    for e in out:
        e['near_best'] = e['residual_rms'] <= best * (1 + rel_tol) + 1e-15
    near = np.array([e['target_per_curve'] for e in out if e['near_best']])
    ident = {'n_near_best': int(len(near)), 'target_spread_per_curve': (near.max(0) - near.min(0)).tolist()}
    return {'ranked': out, 'best': out[0]['name'], 'identifiability': ident}


def stratified_recovery_test(make_truth, fit_fn, bvals, sigma, n=2000, seed=0, n_bins=4):
    """Recovery test that reports bias where it matters, not only pooled.

    make_truth(rng, n, bvals) -> (signals, truth) or (signals, truth, group_labels); draw the truth
    parameters for each compared group from development fits (not from a broad prior).
    Returns pooled bias/sd/r, the slope of estimate vs truth (1 = no compression), bias in truth-
    quantile bins, bias per group and 'worst_abs_bias' (max over bins and groups). Use the worst
    bin/group bias to choose models: a pooled bias near zero can hide large bias in one tissue, and
    minimizing RMSE over a broad prior favours the prior's centre."""
    rng = np.random.default_rng(seed)
    b = np.asarray(bvals, float)
    made = make_truth(rng, n, b)
    S, truth = made[0], np.asarray(made[1], float)
    groups = np.asarray(made[2]) if len(made) > 2 else None
    M = np.abs(S + rng.normal(0, sigma, S.shape) + 1j * rng.normal(0, sigma, S.shape))
    est = np.asarray(fit_fn(M, b), float)
    err = est - truth
    slope = float(np.polyfit(truth, est, 1)[0]) if truth.std() > 0 else float('nan')
    edges = np.quantile(truth, np.linspace(0, 1, n_bins + 1))
    bins = []
    for i in range(n_bins):
        m = (truth >= edges[i]) & ((truth <= edges[i + 1]) if i == n_bins - 1 else (truth < edges[i + 1]))
        if m.any():
            bins.append({'truth_range': [float(edges[i]), float(edges[i + 1])], 'bias': float(err[m].mean()), 'n': int(m.sum())})
    per_group = {}
    if groups is not None:
        for g in np.unique(groups):
            m = groups == g
            per_group[str(g)] = {'bias': float(err[m].mean()), 'sd': float(err[m].std()), 'n': int(m.sum())}
    worst = max([abs(x['bias']) for x in bins] + [abs(v['bias']) for v in per_group.values()])
    r = float(np.corrcoef(est, truth)[0, 1]) if est.std() > 0 and truth.std() > 0 else float('nan')
    return {'bias': float(err.mean()), 'sd': float(err.std()), 'r': r, 'slope': slope, 'bins': bins,
            'groups': per_group, 'worst_abs_bias': float(worst), 'n': int(n)}
