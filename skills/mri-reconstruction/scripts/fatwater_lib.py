"""MRFoundry water-fat separation with a multi-peak fat model, common R2* and a regularized field map
(numpy only; tested in test_fatwater_lib.py: python test_fatwater_lib.py).

Signal model per voxel (complex echoes after a phase-preserving coil combination, the SAME coil weights for every
echo): y(TE) = (W + F sum_p a_p exp(i s 2 pi f_p TE)) exp(-R2* TE) exp(i s 2 pi psi TE), f_p = (ppm_p - water_ppm)
1e-6 gamma B0 in Hz, psi the field map in Hz, s = +1 if a component at offset f contributes exp(+i 2 pi f TE)
(pass sign=-1 for the opposite convention). Pure fat at field psi resembles pure water at psi + f_main (the
water-fat swap): the voxelwise best fit is ambiguous, so fit_fat_water picks, per voxel, among the local minima of
the residual over the field the one that agrees with a smooth field estimated from confident voxels. It needs
no initial guess and works for isolated vials as long as the field is spatially smooth.
PDFF: fat_fraction(...) with optional T1/flip-angle (spoiled GRE) correction to proton density.
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

# Six-peak fat spectrum relative to water (ppm) and relative amplitudes (Hamilton et al. 2011; ISMRM fat-water
# toolbox). Use the spectrum supplied with the data when there is one.
FAT_PPM_REL_WATER = (-3.80, -3.40, -2.60, -1.94, -0.39, 0.60)
FAT_AMPLITUDES = (0.087, 0.693, 0.128, 0.004, 0.039, 0.048)
GAMMA_MHZ_PER_T = 42.577478518


def fat_offsets_hz(field_strength_T, fat_ppm, water_ppm=None, gamma_mhz_per_t=GAMMA_MHZ_PER_T):
    """Frequency offsets of the fat peaks relative to water in Hz. fat_ppm are absolute positions (then give
    water_ppm, e.g. 4.7) or offsets relative to water (water_ppm=None)."""
    ppm = np.asarray(fat_ppm, float) - (0.0 if water_ppm is None else float(water_ppm))
    return ppm * 1e-6 * gamma_mhz_per_t * 1e6 * field_strength_T


def fat_basis(te_s, offsets_hz, amplitudes, sign=1):
    """Complex fat signal at each echo time: sum_p a_p exp(i sign 2 pi f_p TE), amplitudes normalized to sum 1."""
    a = np.asarray(amplitudes, float); a = a / a.sum(); te = np.asarray(te_s, float)
    return np.sum(a[:, None] * np.exp(1j * sign * 2 * np.pi * np.asarray(offsets_hz, float)[:, None] * te[None, :]), 0)


def _residuals(Y, te, fb, fields, r2s, sign):
    """VARPRO residual ||y||^2 - z^H G^-1 z for every (field, r2s) pair: [n_field, n_r2s, n_vox]."""
    e2 = np.sum(np.abs(Y) ** 2, 0)
    out = np.empty((len(fields), len(r2s), Y.shape[1]))
    for j, r in enumerate(r2s):
        d = np.exp(-r * te); B = np.stack([d, d * fb], 1)                # [n_echo, 2]
        G = B.conj().T @ B; Gi = np.linalg.inv(G)
        for i, f in enumerate(fields):
            z = B.conj().T @ (Y * np.exp(-1j * sign * 2 * np.pi * f * te)[:, None])   # [2, n_vox]
            out[i, j] = e2 - np.real(np.sum(z.conj() * (Gi @ z), 0))
    return out


def _smooth(values, weights, mask, sigma_vox):
    """Normalized Gaussian smoothing inside the mask (FFT, zero padded); returns the smooth map everywhere."""
    sh = values.shape; pad = [int(3 * sigma_vox) + 1] * len(sh)
    shp = tuple(s + 2 * p for s, p in zip(sh, pad))
    k = np.ones(shp)
    for ax, n in enumerate(shp):
        g = np.exp(-0.5 * (np.fft.fftfreq(n) * n / sigma_vox) ** 2)
        k = k * g.reshape([-1 if a == ax else 1 for a in range(len(shp))])
        # separable Gaussian built in the spatial domain, transformed below
    K = np.fft.fftn(k)
    def conv(x):
        xp = np.zeros(shp); xp[tuple(slice(p, p + s) for p, s in zip(pad, sh))] = x
        return np.real(np.fft.ifftn(np.fft.fftn(xp) * K))[tuple(slice(p, p + s) for p, s in zip(pad, sh))]
    w = weights * mask
    return conv(w * values) / np.maximum(conv(w), 1e-12 * w.max() + 1e-30)


def fit_fat_water(signal, te_s, offsets_hz, amplitudes, mask=None, sign=1, field_range_hz=None, field_step_hz=None,
                  r2s_grid=None, smooth_sigma_vox=None, n_iter=4, penalty=2.0):
    """Water-fat separation of complex multi-echo images signal [n_echo, ...] (one phase-preserving combination).
    Returns dict(water_real, fat_real (signed real amplitudes after removing the common phase phase0: use these
    for PDFF), water, fat (unconstrained complex), r2s (1/s), field_hz, phase0, pdff_uncorrected (%)).
    Field grid: one alias period 1/min(dTE) unless field_range_hz=(lo, hi) is given; R2* grid 0..400 1/s by default.
    Each voxel chooses among the local minima of its residual over the field the one minimizing
    log(cost / min cost) + penalty ((psi - smooth field) / |main fat offset|)^2, with the smooth field re-estimated
    n_iter times by magnitude- and confidence-weighted smoothing (sigma default: 1/8 of the largest dimension).
    Needs at least 4 echoes with R2* free; with 3 echoes pass a single fixed value in r2s_grid."""
    Y = np.asarray(signal, complex); te = np.asarray(te_s, float); sh = Y.shape[1:]
    if len(te) < 4 and (r2s_grid is None or np.size(r2s_grid) > 1):
        raise ValueError('fewer than 4 echoes cannot separate water, fat, field and R2*: fix R2* (r2s_grid=[value])')
    msk = np.ones(sh, bool) if mask is None else np.asarray(mask, bool)
    Yv = Y.reshape(len(te), -1)[:, msk.ravel()]
    fb = fat_basis(te, offsets_hz, amplitudes, sign)
    a = np.asarray(amplitudes, float); fmain = abs(np.asarray(offsets_hz, float)[np.argmax(a)])
    dte = np.min(np.diff(np.sort(te)))
    if field_range_hz is None:
        field_range_hz = (-0.5 / dte, 0.5 / dte)
    step = field_step_hz or max(0.5, (field_range_hz[1] - field_range_hz[0]) / 400)
    fields = np.arange(field_range_hz[0], field_range_hz[1] + 1e-9, step)
    r2_coarse = np.asarray(r2s_grid if r2s_grid is not None else np.linspace(0, 400, 21), float)
    cost = _residuals(Yv, te, fb, fields, r2_coarse, sign).min(1)          # [n_field, n_vox]
    nf, nv = cost.shape
    cm, cp = np.roll(cost, 1, 0), np.roll(cost, -1, 0)
    periodic = abs((field_range_hz[1] - field_range_hz[0]) - 1.0 / dte) < 2 * step
    is_min = (cost <= cm) & (cost <= cp)
    if not periodic:
        is_min[0] = cost[0] <= cost[1]; is_min[-1] = cost[-1] <= cost[-2]
    cmin = cost.min(0) + 1e-30
    best = fields[np.argmin(cost, 0)]
    # confidence: how much worse the best minimum at least fmain/2 away is
    far = np.abs(((fields[:, None] - best[None, :]) + 0.5 / dte) % (1.0 / dte) - 0.5 / dte) > 0.5 * fmain if periodic else \
        np.abs(fields[:, None] - best[None, :]) > 0.5 * fmain
    c2 = np.where(far, cost, np.inf).min(0)
    conf = np.clip(np.log(c2 / cmin), 0, 5)
    amp = np.sqrt(np.sum(np.abs(Yv) ** 2, 0))
    sigma = smooth_sigma_vox or max(sh) / 8.0
    psi = best.copy(); full = np.zeros(sh)
    for _ in range(n_iter):
        full[:] = 0; full[msk] = psi
        wmap = np.zeros(sh); wmap[msk] = amp ** 2 * conf
        fsm = _smooth(full, wmap, msk.astype(float), sigma)[msk]
        J = np.where(is_min, np.log(cost / cmin) + penalty * ((fields[:, None] - fsm[None, :]) / fmain) ** 2, np.inf)
        psi = fields[np.argmin(J, 0)]
        conf = np.ones_like(conf)
    # local refinement of field and R2*
    r2_fine = np.arange(0, (r2_coarse.max() if len(r2_coarse) else 400) + 1e-9, 1.0)
    fine = np.arange(-2 * step, 2 * step + 1e-9, step / 8)
    bestc = np.full(nv, np.inf); bf = psi.copy(); br = np.zeros(nv)
    for df in fine:
        f = psi + df
        Yd = Yv * np.exp(-1j * sign * 2 * np.pi * np.outer(te, f))
        for r in r2_fine[::5]:
            d = np.exp(-r * te); B = np.stack([d, d * fb], 1); Gi = np.linalg.inv(B.conj().T @ B); z = B.conj().T @ Yd
            c = np.sum(np.abs(Yv) ** 2, 0) - np.real(np.sum(z.conj() * (Gi @ z), 0))
            t = c < bestc; bestc[t] = c[t]; bf[t] = f[t]; br[t] = r
    Yd = Yv * np.exp(-1j * sign * 2 * np.pi * np.outer(te, bf)); bestc[:] = np.inf; rr = br.copy()
    for r in np.arange(-5, 5.01, 0.5):
        rv = np.clip(br + r, 0, None)
        dd = np.exp(-np.outer(te, rv))                                    # [n_echo, n_vox]
        B0 = dd; B1 = dd * fb[:, None]
        g00 = np.sum(np.abs(B0) ** 2, 0); g11 = np.sum(np.abs(B1) ** 2, 0); g01 = np.sum(B0.conj() * B1, 0)
        z0 = np.sum(B0.conj() * Yd, 0); z1 = np.sum(B1.conj() * Yd, 0); det = g00 * g11 - np.abs(g01) ** 2
        w_ = (g11 * z0 - g01 * z1) / det; f_ = (g00 * z1 - np.conj(g01) * z0) / det
        c = np.sum(np.abs(Yd - B0 * w_ - B1 * f_) ** 2, 0)
        t = c < bestc; bestc[t] = c[t]; rr[t] = rv[t]
    dd = np.exp(-np.outer(te, rr)); B0 = dd; B1 = dd * fb[:, None]
    g00 = np.sum(np.abs(B0) ** 2, 0); g11 = np.sum(np.abs(B1) ** 2, 0); g01 = np.sum(B0.conj() * B1, 0)
    z0 = np.sum(B0.conj() * Yd, 0); z1 = np.sum(B1.conj() * Yd, 0); det = g00 * g11 - np.abs(g01) ** 2
    wv = (g11 * z0 - g01 * z1) / det; fv = (g00 * z1 - np.conj(g01) * z0) / det
    # common phase: water and fat share the phase at TE = 0, so fit REAL amplitudes after removing it. Unlike
    # |F| / (|W| + |F|), this keeps PDFF unbiased near 0 % and 100 % fat at moderate SNR.
    phi = np.angle(wv + fv)
    h00 = g00.real; h11 = g11.real; h01 = np.real(g01)
    for _ in range(3):
        ye = Yd * np.exp(-1j * phi)[None]
        r0 = np.real(np.sum(B0.conj() * ye, 0)); r1 = np.real(np.sum(B1.conj() * ye, 0)); dr = h00 * h11 - h01 ** 2
        wr = (h11 * r0 - h01 * r1) / dr; fr = (h00 * r1 - h01 * r0) / dr
        phi = np.angle(np.sum(np.conj(B0 * wr + B1 * fr) * Yd, 0))
    out = {k: np.zeros(sh, complex if k in ('water', 'fat') else float)
           for k in ('water', 'fat', 'water_real', 'fat_real', 'phase0', 'r2s', 'field_hz')}
    out['water'][msk] = wv; out['fat'][msk] = fv; out['r2s'][msk] = rr; out['field_hz'][msk] = bf
    out['water_real'][msk] = wr; out['fat_real'][msk] = fr; out['phase0'][msk] = phi
    out['pdff_uncorrected'] = fat_fraction(out['water_real'], out['fat_real'])
    return out


def spgr_weight(flip_deg, tr_s, t1_s, b1=1.0):
    """Steady-state spoiled-GRE signal per unit proton density: sin(a) (1 - E1) / (1 - cos(a) E1), a = flip x b1."""
    a = np.deg2rad(flip_deg) * np.asarray(b1, float); e1 = np.exp(-tr_s / t1_s)
    return np.sin(a) * (1 - e1) / (1 - np.cos(a) * e1)


def fat_fraction(water, fat, flip_deg=None, tr_s=None, t1_water_s=None, t1_fat_s=None, b1=1.0, clip=True):
    """PDFF in percent: F / (W + F). Real inputs (water_real, fat_real from fit_fat_water: common phase removed)
    are used with their signs, which keeps the estimate unbiased near 0 % and 100 %; complex inputs use magnitudes
    (|F| / (|W| + |F|), biased upward near 0 % and downward near 100 % at low SNR). With flip_deg, tr_s and both
    T1 values the spoiled-GRE T1/flip weighting is removed (b1 = actual/nominal flip map); without them the result
    is a signal fat fraction. clip limits the result to [0, 100]."""
    if np.iscomplexobj(water) or np.iscomplexobj(fat):
        W = np.abs(water).astype(float); F = np.abs(fat).astype(float)
    else:
        W = np.asarray(water, float); F = np.asarray(fat, float)
    if flip_deg is not None:
        W = W / np.maximum(spgr_weight(flip_deg, tr_s, t1_water_s, b1), 1e-12)
        F = F / np.maximum(spgr_weight(flip_deg, tr_s, t1_fat_s, b1), 1e-12)
    tot = W + F
    ff = 100.0 * F / np.where(np.abs(tot) > 1e-30, tot, 1e-30)
    return np.clip(ff, 0, 100) if clip else ff
