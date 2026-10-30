"""MRFoundry quantitative-mapping helpers: voxelwise relaxometry fits and closed-form signals for checks.

Conventions: parameter arrays are in seconds/degrees; images are [..., n_contrasts] (last axis = TE, TI,
flip angle...). All fits are vectorized over voxels, need no initial guess, and return NaN outside the mask.
Before trusting a map, simulate YOUR exported acquisition on known T1/T2 values (Bloch simulator) and
check that the fit recovers them; if the closed-form model is biased for your timing (for example
incomplete recovery between inversions with readout perturbations), fit against simulated signals
with fit_dictionary instead. Tested with numpy 2.x (python test_qmri_fit.py).
"""
import numpy as np

def _flat(images, mask):
    im = np.asarray(images); sh = im.shape[:-1]
    m = np.ones(sh, bool) if mask is None else np.asarray(mask, bool)
    return im.reshape(-1, im.shape[-1]), m.ravel(), sh

def fit_monoexp(te, images, mask=None, iters=20):
    """S(TE) = S0 exp(-TE / T2) for magnitude multi-echo data (T2 or T2*). Returns (S0, T2).
    Log-linear fit weighted by S^2, then Gauss-Newton refinement on the magnitude signal."""
    te = np.asarray(te, float); Y, m, sh = _flat(np.abs(images), mask); S0 = np.full(len(Y), np.nan); T2 = S0.copy()
    y = np.clip(Y[m], 1e-12, None); w = y ** 2; A = np.stack([np.ones_like(te), -te], 1)
    L = np.log(y); ATA = np.einsum('ve,ei,ej->vij', w, A, A); ATb = np.einsum('ve,ei,ve->vi', w, A, L)
    p = np.linalg.solve(ATA, ATb[..., None])[..., 0]; s0 = np.exp(p[:, 0]); r2 = np.clip(p[:, 1], 1e-6, None)
    for _ in range(iters):
        e = np.exp(-np.outer(r2, te)); f = s0[:, None] * e; J = np.stack([e, -te * f], 2); r = y - f
        H = np.einsum('vei,vej->vij', J, J) + 1e-12 * np.eye(2); g = np.einsum('vei,ve->vi', J, r)
        d = np.linalg.solve(H, g[..., None])[..., 0]; s0 = s0 + d[:, 0]; r2 = np.clip(r2 + d[:, 1], 1e-6, None)
    S0[m] = s0; T2[m] = 1 / r2
    return S0.reshape(sh), T2.reshape(sh)

def _grid_ls(Y, basis_t):
    """For each candidate (rows of basis_t: n_grid x n_contrast exponentials) fit a + b*basis by LS; return SSE [v, g], a, b."""
    n = Y.shape[1]; x = basis_t; xm = x.mean(1, keepdims=True); xc = x - xm; sxx = (xc ** 2).sum(1)
    ym = Y.mean(1, keepdims=True); yc = Y - ym; sxy = yc @ xc.T
    b = sxy / sxx[None]; a = ym - b * xm.T; sse = (yc ** 2).sum(1, keepdims=True) - b * sxy
    return sse, a, b

def fit_inversion_recovery(ti, images, mask=None, t1_range=(0.02, 6.0), n_grid=1200, magnitude=None):
    """S(TI) = a + b exp(-TI / T1) (three parameters: imperfect inversion and incomplete recovery are absorbed in a, b;
    exact only if every inversion starts from the same longitudinal state). Returns (T1, a, b).
    Complex input: each voxel is phased by its longest-TI sample and the real part is fitted.
    Magnitude input: polarity restoration (Barral et al., MRM 2010): signs of the first k samples are flipped for
    every k and the best fit is kept. Grid search in T1 with closed-form a, b: no initial guess needed."""
    ti = np.asarray(ti, float); order = np.argsort(ti); ti = ti[order]
    im = np.asarray(images)[..., order]; magnitude = (not np.iscomplexobj(im)) if magnitude is None else magnitude
    Y, m, sh = _flat(im, mask); Y = Y[m]
    if not magnitude:
        ph = np.exp(-1j * np.angle(Y[:, -1:])); Y = (Y * ph).real
    else:
        Y = np.abs(Y)
    grid = np.geomspace(*t1_range, n_grid); E = np.exp(-ti[None, :] / grid[:, None])
    best = np.full(len(Y), np.inf); T1 = np.full(len(Y), np.nan); A = T1.copy(); B = T1.copy()
    flips = range(len(ti) + 1) if magnitude else [0]
    for k in flips:
        Z = Y.copy(); Z[:, :k] *= -1
        sse, a, b = _grid_ls(Z, E); i = np.argmin(sse, 1); s = sse[np.arange(len(Z)), i]; upd = s < best
        best[upd] = s[upd]; T1[upd] = grid[i[upd]]; A[upd] = a[np.arange(len(Z)), i][upd]; B[upd] = b[np.arange(len(Z)), i][upd]
    out = [np.full(len(m), np.nan) for _ in range(3)]
    for o, v in zip(out, (T1, A, B)): o[m] = v
    return tuple(o.reshape(sh) for o in out)

def fit_vfa(flip_deg, tr, images, mask=None, b1=1.0):
    """Spoiled-GRE variable flip angle (DESPOT1): S/sin(a) = E1 * S/tan(a) + M0 (1 - E1). Returns (T1, M0).
    Assumes ideal spoiling; check with a Bloch simulation of your sequence (RF spoiling is not ideal)."""
    Y, m, sh = _flat(np.abs(images), mask)
    b1v = np.broadcast_to(np.asarray(b1, float), sh).reshape(-1, 1)          # scalar or per-voxel B1 scale
    aa = (np.deg2rad(np.asarray(flip_deg, float))[None, :] * b1v)[m]; y = Y[m]
    x = y / np.tan(aa); z = y / np.sin(aa); xm = x.mean(1); zm = z.mean(1)
    slope = ((x - xm[:, None]) * (z - zm[:, None])).sum(1) / ((x - xm[:, None]) ** 2).sum(1); icpt = zm - slope * xm
    T1 = np.full(len(m), np.nan); M0 = T1.copy(); e1 = np.clip(slope, 1e-9, 1 - 1e-9)
    T1[m] = -tr / np.log(e1); M0[m] = icpt / (1 - e1)
    return T1.reshape(sh), M0.reshape(sh)

def fit_dictionary(images, dictionary, params, mask=None):
    """Match each voxel curve to simulated curves (rows of dictionary, same contrast order) up to a scale factor.
    Use when the closed-form model does not describe your exact acquisition: simulate the exported sequence (or a
    validated signal model of it) over a parameter grid. Complex curves are matched with a complex scale.
    Returns (best params [..., n_param], scale [...], normalized correlation [...])."""
    D = np.asarray(dictionary); P = np.asarray(params).reshape(len(D), -1)
    Y, m, sh = _flat(np.asarray(images), mask); y = Y[m]
    Dn = D / np.linalg.norm(D, axis=1, keepdims=True); c = y @ Dn.conj().T if np.iscomplexobj(D) or np.iscomplexobj(y) else y @ Dn.T
    i = np.argmax(np.abs(c), 1); corr = np.abs(c[np.arange(len(y)), i]) / np.linalg.norm(y, axis=1)
    scale = c[np.arange(len(y)), i] / np.linalg.norm(D[i], axis=1)
    bp = np.full((len(m), P.shape[1]), np.nan); bp[m] = P[i]; sc = np.full(len(m), np.nan, dtype=scale.dtype); sc[m] = scale
    co = np.full(len(m), np.nan); co[m] = corr
    return bp.reshape(sh + (P.shape[1],)), sc.reshape(sh), co.reshape(sh)

# ---- closed-form / steady-state signals for checking simulations -------------------------------------------
def ernst_signal(flip_deg, tr, t1, te=0.0, t2=np.inf, m0=1.0):
    """Ideally spoiled GRE steady state at TE (real RF spoiling deviates; compare with a Bloch simulation)."""
    a = np.deg2rad(flip_deg); e1 = np.exp(-tr / t1)
    return m0 * np.sin(a) * (1 - e1) / (1 - np.cos(a) * e1) * np.exp(-te / t2)

def ir_signal(ti, t1, m0=1.0, inversion_efficiency=1.0, recovery=np.inf):
    """Longitudinal magnetization at TI after inversion from Mz = m0 (1 - exp(-recovery/T1)) (single readout, no saturation)."""
    mz0 = m0 * (1 - np.exp(-recovery / t1))
    return m0 - (m0 + inversion_efficiency * mz0) * np.exp(-np.asarray(ti) / t1)

def bssfp_signal(flip_deg, tr, t1, t2, te=None, off_resonance_hz=0.0, phase_cycle_deg=180.0, m0=1.0):
    """Steady-state balanced SSFP transverse magnetization (complex, receiver demodulated with the RF phase) at TE
    after an RF pulse, by solving the Bloch fixed point of hard-pulse RF + free precession (no closed-form shortcut).
    On resonance with 180-degree phase cycling the magnitude at TE=0 equals
    m0 sin(a)(1-E1)/(1-(E1-E2)cos(a)-E1E2). te defaults to TR/2."""
    te = tr / 2 if te is None else te; a = np.deg2rad(flip_deg)
    t1, t2, df = np.broadcast_arrays(np.asarray(t1, float), np.asarray(t2, float), np.asarray(off_resonance_hz, float))
    out = np.empty(t1.shape, complex)
    for idx in np.ndindex(t1.shape):
        def free(t):
            e1, e2, th = np.exp(-t / t1[idx]), np.exp(-t / t2[idx]), 2 * np.pi * df[idx] * t
            c, s = np.cos(th), np.sin(th)
            return np.array([[e2 * c, e2 * s, 0], [-e2 * s, e2 * c, 0], [0, 0, e1]]), np.array([0, 0, m0 * (1 - e1)])
        def rf(phi):
            cp, sp = np.cos(phi), np.sin(phi); ca, sa = np.cos(a), np.sin(a)
            Rz = np.array([[cp, -sp, 0], [sp, cp, 0], [0, 0, 1]]); Rx = np.array([[1, 0, 0], [0, ca, sa], [0, -sa, ca]])
            return Rz @ Rx @ Rz.T
        P, b = free(tr); dphi = np.deg2rad(phase_cycle_deg)
        # two-TR period starting just before an RF of phase 0: M -> R(0) -> free -> R(dphi) -> free
        M1 = P @ rf(0.0); M2 = P @ rf(dphi); Mtot = M2 @ M1
        btot = M2 @ b + b                                       # relaxation source terms of both TRs
        Mminus = np.linalg.solve(np.eye(3) - Mtot, btot)          # just before the phase-0 RF
        Mplus = rf(0.0) @ Mminus; Pte, bte = free(te); Mte = Pte @ Mplus + bte
        out[idx] = Mte[0] + 1j * Mte[1]
    return out if out.shape else out[()]

