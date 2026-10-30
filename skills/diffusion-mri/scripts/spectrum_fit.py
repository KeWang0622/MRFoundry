"""MRFoundry helpers for signal-fraction / diffusivity-spectrum fits (numpy + scipy).

Use with a recovery test before trusting fractions: fits of exp(-b D) mixtures are ill-conditioned.
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

def fixed_compartment_fraction(signals, bvals, diffusivities, target_below, sigma=None, normalize_b0=True):
    """Well-posed signal fraction: NNLS on a few fixed, well-separated compartment diffusivities (e.g. restricted,
    hindered, free), optional Rician floor correction with sigma, then the weight fraction with D < target_below.
    Pick the compartment values from literature/development data and confirm them with recovery_test."""
    S = np.atleast_2d(np.asarray(signals, float))
    if sigma is not None: S = floor_correct(S, sigma)
    w = fit_weights(S, bvals, diffusivities, normalize_b0=normalize_b0)
    return fraction_below(w, diffusivities, target_below), w
