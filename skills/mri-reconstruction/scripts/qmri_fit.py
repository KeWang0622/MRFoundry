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

def fit_dictionary(images, dictionary, params, mask=None, noise_sigma=None):
    """Match each voxel curve to simulated curves (rows of dictionary, same contrast order) up to a scale factor.
    Use when the closed-form model does not describe your exact acquisition: simulate the exported sequence (or a
    validated signal model of it) over a parameter grid. Complex curves are matched with a complex scale.
    Magnitude data at low SNR: pass noise_sigma (SD of the real or imaginary noise, e.g. background_sigma); the
    match is then done on squared magnitudes, E[|S|^2] = A^2 + 2 sigma^2 for Rician noise, so the noise floor of
    late echoes or long TIs does not bias the fit (T2 too long, T1 too short). sigma may be a scalar or per voxel.
    Returns (best params [..., n_param], scale [...], normalized correlation [...])."""
    D = np.asarray(dictionary); P = np.asarray(params).reshape(len(D), -1)
    Y, m, sh = _flat(np.asarray(images), mask); y = Y[m]
    if noise_sigma is not None:
        sig = np.broadcast_to(np.asarray(noise_sigma, float), sh).reshape(-1)[m]
        z = np.abs(y) ** 2 - 2 * sig[:, None] ** 2                      # unbiased estimate of the noise-free power
        D2 = np.abs(D) ** 2; nD = np.linalg.norm(D2, axis=1)
        c = z @ (D2 / nD[:, None]).T                                      # projections; scale^2 = c / nD
        score = np.where(c > 0, c, 0.0)                                   # SSE = |z|^2 - c^2 (only for c > 0)
        i = np.argmax(score, 1); ci = c[np.arange(len(z)), i]
        corr = ci / np.maximum(np.linalg.norm(z, axis=1), 1e-30)
        scale = np.sqrt(np.maximum(ci, 0) / nD[i])
    else:
        Dn = D / np.linalg.norm(D, axis=1, keepdims=True); c = y @ Dn.conj().T if np.iscomplexobj(D) or np.iscomplexobj(y) else y @ Dn.T
        i = np.argmax(np.abs(c), 1); corr = np.abs(c[np.arange(len(y)), i]) / np.linalg.norm(y, axis=1)
        scale = c[np.arange(len(y)), i] / np.linalg.norm(D[i], axis=1)
    bp = np.full((len(m), P.shape[1]), np.nan); bp[m] = P[i]; sc = np.full(len(m), np.nan, dtype=np.asarray(scale).dtype); sc[m] = scale
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


# ---- multi-echo spin echo with imperfect refocusing (extended phase graphs) --------------------------------
def epg_cpmg(n_echoes, esp, t2, t1=1.0, refocus_deg=180.0, excite_deg=90.0):
    """CPMG echo amplitudes by extended phase graphs (Hennig 1988; Weigel 2015). Excitation about the axis
    perpendicular to the refocusing axis; refocus_deg is the actual (B1-scaled) refocusing angle; esp = echo
    spacing (s). With imperfect refocusing, stimulated echoes make the decay non-exponential (even echoes
    higher than odd ones): fitting a mono-exponential then biases T2. Returns |echo| for echoes 1..n."""
    n = 2 * n_echoes + 2
    F = np.zeros((3, n), complex)  # rows: F+, F-, Z
    F[2, 0] = 1.0
    def rot(a, phi):
        c2, s2, s = np.cos(a / 2) ** 2, np.sin(a / 2) ** 2, np.sin(a)
        return np.array([[c2, np.exp(2j * phi) * s2, -1j * np.exp(1j * phi) * s],
                         [np.exp(-2j * phi) * s2, c2, 1j * np.exp(-1j * phi) * s],
                         [-0.5j * np.exp(-1j * phi) * s, 0.5j * np.exp(1j * phi) * s, np.cos(a)]])
    def relax(F, t):
        E1, E2 = np.exp(-t / t1), np.exp(-t / t2)
        F = F.copy(); F[:2] *= E2; F[2] *= E1; F[2, 0] += 1 - E1
        return F
    def shift(F):
        F = F.copy(); F[0, 1:] = F[0, :-1].copy(); F[1, :-1] = F[1, 1:].copy(); F[1, -1] = 0; F[0, 0] = np.conj(F[1, 0])
        return F
    F = rot(np.deg2rad(excite_deg), np.pi / 2) @ F
    Rf = rot(np.deg2rad(refocus_deg), 0.0)
    out = []
    for _ in range(n_echoes):
        F = shift(relax(F, esp / 2))
        F = Rf @ F
        F = shift(relax(F, esp / 2))
        out.append(abs(F[0, 0]))
    return np.array(out)


def epg_t2_dictionary(n_echoes, esp, t2_grid, b1_grid, t1=1.0, refocus_deg=180.0, excite_deg=90.0):
    """Dictionary over (T2, B1 scale) for fit_dictionary: B1 scales both the excitation and refocusing angles.
    Refocusing angles a and 360 - a give identical echo trains, so B1 above and below the value that makes
    the refocusing angle 180 deg cannot be distinguished: keep the grid on one side or use a measured B1 map.
    Returns (dictionary [n_t2 * n_b1, n_echoes], params [n, 2] = (T2, B1))."""
    D, P = [], []
    for t2 in np.asarray(t2_grid, float):
        for b in np.asarray(b1_grid, float):
            D.append(epg_cpmg(n_echoes, esp, t2, t1, refocus_deg * b, excite_deg * b)); P.append((t2, b))
    return np.array(D), np.array(P)


# ---- arterial spin labelling (consensus single-compartment model, Alsop et al. 2015) ------------------------
def asl_cbf_pcasl(delta_m, m0, pld, label_duration, t1_blood=1.65, efficiency=0.85, partition=0.9):
    """PCASL CBF in ml/100 g/min: 6000 * lambda * dM * exp(PLD/T1b) / (2 alpha T1b M0 (1 - exp(-tau/T1b))).
    delta_m = control - label (same scaling as m0); times in s; t1_blood 1.65 s is the 3 T consensus value;
    m0 must be the equilibrium (proton-density) signal, corrected if its TR was short."""
    return 6000 * partition * np.asarray(delta_m) * np.exp(pld / t1_blood) / (
        2 * efficiency * t1_blood * np.asarray(m0) * (1 - np.exp(-label_duration / t1_blood)))


def asl_cbf_pasl(delta_m, m0, ti, ti1, t1_blood=1.65, efficiency=0.98, partition=0.9):
    """PASL (QUIPSS II / Q2TIPS) CBF in ml/100 g/min: 6000 * lambda * dM * exp(TI/T1b) / (2 alpha TI1 M0)."""
    return 6000 * partition * np.asarray(delta_m) * np.exp(ti / t1_blood) / (2 * efficiency * ti1 * np.asarray(m0))


def m0_finite_tr(m0_measured, tr, t1_tissue=1.3):
    """Fully relaxed M0 from an M0 image acquired with a finite (preparation) TR: M0 / (1 - exp(-TR/T1))."""
    return np.asarray(m0_measured, float) / (1 - np.exp(-tr / t1_tissue))


def asl_pairs_by_delay(volumes, volume_types, delays):
    """Group a 4-D ASL series [..., n_vol] by delay, independent of volume order: returns (unique delays,
    deltaM [..., n_delay] = mean(control) - mean(label) at each delay). volume_types: 'control'/'label' per
    volume (BIDS aslcontext); other types are ignored. delays: PLD (pCASL) or TI (PASL) per volume."""
    v = np.asarray(volumes, float); ty = np.asarray([str(x).strip().lower() for x in volume_types])
    d = np.round(np.asarray(delays, float), 6); u = np.unique(d[np.isin(ty, ['control', 'label'])])
    out = [v[..., (ty == 'control') & (d == x)].mean(-1) - v[..., (ty == 'label') & (d == x)].mean(-1) for x in u]
    return u, np.stack(out, -1)


def asl_gkm_pcasl(pld, att, tau, cbf=1.0, m0=1.0, t1_blood=1.65, efficiency=0.85, partition=0.9):
    """pCASL general kinetic model (Buxton 1998; single compartment, tissue T1 = blood T1, no outflow) in the
    consensus units: dM in the units of m0, cbf in ml/100 g/min, times in s.
    pld = time from the END of labelling to the readout of this voxel (add the slice timing offset for 2-D
    multi-slice); att = arrival time measured from the START of labelling; tau = label duration. The time
    since the start of labelling is therefore tau + pld (a frequent error is to use pld alone).
    For pld >= att this reduces exactly to the white-paper single-delay formula (asl_cbf_pcasl)."""
    pld = np.asarray(pld, float); att = np.asarray(att, float); t = tau + pld
    f = np.asarray(cbf, float) / 6000.0; m0b = np.asarray(m0, float) / partition
    amp = 2 * efficiency * m0b * f * t1_blood * np.exp(-att / t1_blood)
    during = amp * (1 - np.exp(-np.clip(t - att, 0, None) / t1_blood))
    after = amp * np.exp(-np.clip(pld - att, 0, None) / t1_blood) * (1 - np.exp(-tau / t1_blood))
    return np.where(t < att, 0.0, np.where(t < att + tau, during, after))


def fit_asl_multidelay(delta_m, m0, pld, tau, att_grid=None, **model):
    """Voxelwise CBF (ml/100 g/min) and ATT (s) from multi-delay pCASL by a grid search in ATT with closed-form
    nonnegative CBF. delta_m [..., n_delay] (control - label, averaged per delay), m0 [...] (fully relaxed),
    pld [n_delay] or [..., n_delay] (per-voxel effective delays, e.g. PLD + slice timing). model: t1_blood,
    efficiency, partition. ATT shorter than the shortest effective delay is not identifiable (the curve no longer
    depends on it); such voxels return the largest tied ATT, i.e. an upper bound. Returns (cbf, att)."""
    Y = np.asarray(delta_m, float); sh = Y.shape[:-1]; n = Y.shape[-1]; Y = Y.reshape(-1, n)
    M0 = np.broadcast_to(np.asarray(m0, float), sh).reshape(-1)
    P = np.broadcast_to(np.asarray(pld, float), sh + (n,)).reshape(-1, n)
    grid = np.arange(0.0, float(P.max() + tau), 0.005) if att_grid is None else np.asarray(att_grid, float)
    best = np.full(len(Y), np.inf); cbf = np.zeros(len(Y)); att = np.zeros(len(Y)); tol = 1e-10 * np.sum(Y * Y, 1)
    for a in grid:
        B = asl_gkm_pcasl(P, a, tau, 1.0, M0[:, None], **model)          # signal per unit CBF
        bb = np.sum(B * B, 1); c = np.where(bb > 0, np.sum(B * Y, 1) / np.maximum(bb, 1e-30), 0.0); c = np.maximum(c, 0)
        sse = np.sum((Y - c[:, None] * B) ** 2, 1)
        take = sse <= best + tol                                    # ties resolve to the largest ATT
        best[take] = sse[take]; cbf[take] = c[take]; att[take] = a
    return cbf.reshape(sh), att.reshape(sh)


# ---- DCE-MRI (Tofts / extended Tofts) ---------------------------------------------------------------------
def spgr_concentration(signal, t10, tr, flip_deg, relaxivity, n_baseline, b1=1.0):
    """Contrast-agent concentration from spoiled-GRE DCE signal [..., n_t] (fast exchange, R1 = R10 + r1 C).
    M0 is estimated per voxel from the mean of the first n_baseline frames and the known T10 (inverting
    S = M0 sin(a)(1 - E1)/(1 - cos(a) E1)); each frame is then inverted exactly to R1. Times in s, r1 in
    1/(mM s) -> C in mM; b1 scales the flip angle (scalar or per voxel). Returns (C [..., n_t], M0 [...])."""
    S = np.asarray(signal, float); r10 = 1.0 / np.maximum(np.asarray(t10, float), 1e-6)
    a = np.deg2rad(flip_deg) * np.asarray(b1, float) * np.ones_like(r10)
    e10 = np.exp(-tr * r10); f0 = np.sin(a) * (1 - e10) / (1 - np.cos(a) * e10)
    m0 = S[..., :n_baseline].mean(-1) / np.maximum(f0, 1e-12)
    y = np.clip(S / np.maximum(m0 * np.sin(a), 1e-12)[..., None], 1e-9, 1 - 1e-9)
    e1 = np.clip((1 - y) / (1 - y * np.cos(a)[..., None]), 1e-12, 1 - 1e-12)
    return (-np.log(e1) / tr - r10[..., None]) / relaxivity, m0


def conv_exp_pwlinear(t, x, k):
    """Exact integral_t0^t_n x(u) exp(-k (t_n - u)) du at every sample t_n, for x piecewise linear between the
    (possibly non-uniform) samples t. This is the Tofts convolution with the AIF interpolated linearly between
    frames; a rectangular sum (np.convolve * dt) lags by about half a frame and biases vp and Ktrans.
    Checked against fine-grid quadrature in test_qmri_fit.py."""
    t = np.asarray(t, float); x = np.asarray(x, float); h = np.diff(t); kh = k * h
    small = np.abs(kh) < 1e-4
    with np.errstate(divide='ignore', invalid='ignore'):
        A = np.where(small, h * (1 - kh / 2 + kh ** 2 / 6), -np.expm1(-kh) / np.where(small, 1, k))
        B = np.where(small, h * (0.5 - kh / 6 + kh ** 2 / 24), (h - A) / np.where(small, 1, kh))
    E = np.exp(-kh); out = np.zeros_like(x)
    for n in range(len(h)):
        out[n + 1] = E[n] * out[n] + x[n] * A[n] + (x[n + 1] - x[n]) * B[n]
    return out


def tofts_concentration(t, cp, ktrans, ve, vp=0.0):
    """Extended Tofts tissue concentration Ct(t) = vp Cp(t) + Ktrans int Cp(u) exp(-kep (t-u)) du, kep = Ktrans/ve,
    with Cp linear between samples (t may be non-uniform; t[0] is the start of the integral). cp is the PLASMA
    concentration (Cp = Cblood / (1 - Hct)). Rates are per unit of t (1/s if t in s; multiply by 60 for 1/min)."""
    return vp * np.asarray(cp, float) + ktrans * conv_exp_pwlinear(t, cp, ktrans / ve)


def fit_tofts(t, ct, cp, extended=True, kep_range=None, n_grid=400):
    """Voxelwise (extended) Tofts fit without initial guesses: for each kep on a log grid the model is linear in
    (Ktrans, vp), solved in closed form for all voxels; the best kep is refined by a parabola in log kep.
    Uses the exact piecewise-linear convolution, so non-uniform frame times are fine. ct: [..., n_t] tissue
    concentration, cp: [n_t] plasma concentration, t in s (or min). kep_range defaults to (1e-3, 20) / median
    frame spacing... in units of 1/t. Returns dict of arrays: ktrans, ve, vp, kep (per unit of t) and rmse.
    Test it on curves simulated by an independent route (fine-grid quadrature), not with this function."""
    t = np.asarray(t, float); cp = np.asarray(cp, float); Y = np.asarray(ct, float); sh = Y.shape[:-1]
    Y = Y.reshape(-1, len(t))
    if kep_range is None:
        kep_range = (1e-3 / (t[-1] - t[0]), 5.0 / max(np.median(np.diff(t)), 1e-9))
    grid = np.geomspace(*kep_range, n_grid)
    def solve(kep):
        q = conv_exp_pwlinear(t, cp, kep)
        if extended:
            M = np.stack([q, cp], 1); G = M.T @ M; rhs = Y @ M
            sol = np.linalg.solve(G + 1e-12 * np.trace(G) * np.eye(2), rhs.T).T
            neg = sol[:, 1] < 0                                   # vp >= 0: refit Ktrans alone
            sol[neg, 1] = 0; sol[neg, 0] = (Y[neg] @ q) / max(q @ q, 1e-30)
            fit = sol @ M.T
        else:
            kt = (Y @ q) / max(q @ q, 1e-30); sol = np.stack([kt, np.zeros_like(kt)], 1); fit = np.outer(kt, q)
        sol[:, 0] = np.maximum(sol[:, 0], 0)
        return sol, np.sum((Y - fit) ** 2, 1)
    sse = np.empty((len(Y), n_grid))
    for j, kep in enumerate(grid):
        sse[:, j] = solve(kep)[1]
    j = np.clip(np.argmin(sse, 1), 1, n_grid - 2); lg = np.log(grid)
    y0, y1, y2 = sse[np.arange(len(Y)), j - 1], sse[np.arange(len(Y)), j], sse[np.arange(len(Y)), j + 1]
    den = y0 - 2 * y1 + y2; step = np.where(den > 0, 0.5 * (y0 - y2) / np.where(den > 0, den, 1), 0)
    lk = lg[j] + np.clip(step, -1, 1) * (lg[1] - lg[0]); kep = np.exp(lk)
    ktrans = np.empty(len(Y)); vp = np.empty(len(Y)); err = np.empty(len(Y))
    for u in np.unique(np.round(lk, 9)):                         # group voxels sharing the refined kep
        idx = np.flatnonzero(np.round(lk, 9) == u); Ysub = Y[idx]
        q = conv_exp_pwlinear(t, cp, np.exp(u))
        if extended:
            M = np.stack([q, cp], 1); G = M.T @ M
            sol = np.linalg.solve(G + 1e-12 * np.trace(G) * np.eye(2), (Ysub @ M).T).T
            neg = sol[:, 1] < 0; sol[neg, 1] = 0; sol[neg, 0] = (Ysub[neg] @ q) / max(q @ q, 1e-30)
        else:
            sol = np.stack([(Ysub @ q) / max(q @ q, 1e-30), np.zeros(len(idx))], 1); M = np.stack([q, cp], 1)
        sol[:, 0] = np.maximum(sol[:, 0], 0)
        ktrans[idx], vp[idx] = sol[:, 0], sol[:, 1]
        err[idx] = np.sqrt(np.mean((Ysub - sol @ M.T) ** 2, 1))
    out = dict(ktrans=ktrans, ve=np.where(kep > 0, ktrans / kep, np.nan), vp=vp, kep=kep, rmse=err)
    return {k: v.reshape(sh) for k, v in out.items()}


def fit_tofts_linear(t, ct, cp, extended=True):
    """Linear least-squares (extended) Tofts fit (Murase 2004): Ct = (Ktrans + kep vp) int Cp - kep int Ct + vp Cp.
    Fast initial estimate; integrals by the trapezoid rule, so it is biased when frames are coarse. Prefer fit_tofts.
    ct (..., n_t) tissue concentration, cp (n_t) plasma concentration. Returns (Ktrans, ve, vp) arrays."""
    t = np.asarray(t, float); cp = np.asarray(cp, float); Y = np.atleast_2d(np.asarray(ct, float))
    icp = np.concatenate([[0], np.cumsum((cp[1:] + cp[:-1]) / 2 * np.diff(t))])
    ict = np.concatenate([np.zeros((len(Y), 1)), np.cumsum((Y[:, 1:] + Y[:, :-1]) / 2 * np.diff(t), 1)], 1)
    out = []
    for y, ic in zip(Y, ict):
        A = np.stack([icp, -ic] + ([cp] if extended else []), 1)
        c, *_ = np.linalg.lstsq(A, y, rcond=None)
        kep = c[1]; vp = c[2] if extended else 0.0; ktrans = c[0] - kep * vp
        out.append((ktrans, ktrans / kep if kep != 0 else np.nan, vp))
    o = np.array(out).T
    sh = np.shape(ct)[:-1]
    return tuple(v.reshape(sh) for v in o)
