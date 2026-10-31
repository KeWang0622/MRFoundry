"""MRFoundry QSM helpers (numpy only; tested in test_qsm_lib.py).

Pipeline, each step validated in the test:
  phase_rad = stored * scale (apply the documented sign)  ->  multiecho_field_hz (phase0 removed, unwrapped)
  -> pdf_background (strong air/sinus fields; vsharp is a faster, less accurate alternative)
  -> invert_cg_l2 (invert_tkd as an independent check)  ->  reference_to_roi (e.g. ventricular CSF = 0)
  -> roi_means. Expect moderate underestimation of chi from regularization; judge it on synthetic_head.
Conventions: arrays are [i, j, k] in ARRAY axis order; voxel_size_mm along those axes (anisotropic is fine);
b0_dir is the unit vector of B0 in the array-axis frame (oblique slabs: not (0, 0, 1)); fields in Hz, chi in ppm,
f = gamma_bar * B0 * 1e-6 * (d * chi) with D(k) = 1/3 - (k.b)^2/|k|^2 and k in cycles/mm per axis.
Quick check of your data and geometry: python qsm_lib.py --selftest (synthetic head; prints correlations and scale).
"""
import numpy as np

GAMMA_BAR_1H = 42.577478518e6  # Hz/T


def _pad(a, shape):
    out = np.zeros(shape, dtype=a.dtype); out[tuple(slice(0, n) for n in a.shape)] = a; return out


def _crop(a, shape):
    return a[tuple(slice(0, n) for n in shape)]


def padded_shape(shape, factor=1.5):
    """Grid used for FFT convolutions (zero padding avoids wrap-around of dipole fields)."""
    return tuple(int(2 * np.ceil(n * factor / 2)) for n in shape)


def kspace_grid(shape, voxel_size_mm):
    """k coordinates (cycles/mm) along each array axis for an FFT grid."""
    return np.meshgrid(*[np.fft.fftfreq(n, d=v) for n, v in zip(shape, voxel_size_mm)], indexing='ij')


def dipole_kernel(shape, voxel_size_mm, b0_dir):
    """Unit dipole kernel D(k) = 1/3 - (k.b)^2/|k|^2 on an FFT grid (D(0) = 0), physical k, any b0 direction."""
    b = np.asarray(b0_dir, float); b = b / np.linalg.norm(b)
    k = kspace_grid(shape, voxel_size_mm); k2 = sum(c ** 2 for c in k)
    kb = sum(c * bi for c, bi in zip(k, b))
    with np.errstate(divide='ignore', invalid='ignore'):
        D = 1.0 / 3.0 - kb ** 2 / k2
    D[k2 == 0] = 0.0
    return D


def ppm_per_hz(b0_T, gamma_bar=GAMMA_BAR_1H):
    return 1e6 / (gamma_bar * b0_T)


def field_from_chi(chi_ppm, voxel_size_mm, b0_dir, b0_T, gamma_bar=GAMMA_BAR_1H, pad=1.5):
    """Forward model: field (Hz) of a susceptibility distribution (ppm), zero padded."""
    sh = chi_ppm.shape; ps = padded_shape(sh, pad)
    D = dipole_kernel(ps, voxel_size_mm, b0_dir)
    f = np.real(np.fft.ifftn(D * np.fft.fftn(_pad(np.asarray(chi_ppm, float), ps))))
    return _crop(f, sh) / ppm_per_hz(b0_T, gamma_bar)


def sphere_kernel(shape, voxel_size_mm, radius_mm):
    """Normalized spherical mean-value kernel (physical radius, anisotropic voxels) centred at index 0 (FFT layout)."""
    ax = [np.fft.fftfreq(n, d=1.0 / n) * v for n, v in zip(shape, voxel_size_mm)]   # signed distances in mm
    g = np.meshgrid(*ax, indexing='ij')
    s = (sum(c ** 2 for c in g) <= radius_mm ** 2).astype(float)
    return s / s.sum()


def erode(mask, voxel_size_mm, radius_mm):
    """Mask eroded by a physical radius (voxels whose whole sphere lies inside the mask)."""
    m = np.asarray(mask, bool); ps = padded_shape(m.shape, 1.2)
    S = sphere_kernel(ps, voxel_size_mm, radius_mm)
    c = np.real(np.fft.ifftn(np.fft.fftn(S) * np.fft.fftn(_pad(m.astype(float), ps))))
    return _crop(c, m.shape) > 1 - 1e-6


def laplacian_unwrap(phase, voxel_size_mm, pad=1.25):
    """Laplacian phase unwrapping (Schofield & Zhu 2003): returns the unwrapped phase up to a harmonic function,
    which background-field removal discards. Works through noise-only regions (they add harmonic terms inside
    the brain). Physical voxel sizes are used in the Laplacian."""
    sh = phase.shape; ps = padded_shape(sh, pad)
    k = kspace_grid(ps, voxel_size_mm); k2 = (2 * np.pi) ** 2 * sum(c ** 2 for c in k)
    lap = lambda u: np.real(np.fft.ifftn(-k2 * np.fft.fftn(u)))
    s, c = _pad(np.sin(phase), ps), _pad(np.cos(phase), ps)
    L = c * lap(s) - s * lap(c)
    with np.errstate(divide='ignore', invalid='ignore'):
        inv = np.where(k2 > 0, -1.0 / k2, 0.0)
    return _crop(np.real(np.fft.ifftn(inv * np.fft.fftn(L))), sh)


def multiecho_field_hz(magnitude, phase_rad, te, voxel_size_mm, mask=None, method='laplacian'):
    """Field offset (Hz) from multi-echo GRE [i, j, k, echo] with phase(TE) = phase0(r) + 2 pi f TE.
    phase0 is removed by complex division by the first echo. method='laplacian' (default): each echo difference
    is Laplacian-unwrapped and f is the magnitude-weighted least-squares slope through the origin; the result
    equals the true field up to smooth harmonic terms, which background removal (pdf_background) absorbs.
    method='temporal': no spatial unwrapping; exact when |f| < 1/(2 dTE_min) everywhere (short echo spacing).
    Echo times need not be uniform. Values outside mask (if given) are set to 0."""
    te = np.asarray(te, float); o = np.argsort(te); te = te[o]
    mag = np.asarray(magnitude, float)[..., o]; ph = np.asarray(phase_rad, float)[..., o]
    z0 = mag[..., 0] * np.exp(1j * ph[..., 0])
    num = np.zeros(mag.shape[:3]); den = np.zeros(mag.shape[:3]); f_prev = None
    for e in range(1, len(te)):
        d = np.angle(mag[..., e] * np.exp(1j * ph[..., e]) * np.conj(z0)); dt = te[e] - te[0]
        if method == 'temporal':
            du = d if f_prev is None else d + 2 * np.pi * np.round((2 * np.pi * f_prev * dt - d) / (2 * np.pi))
        else:
            du = laplacian_unwrap(d, voxel_size_mm)
        w = (mag[..., e] * mag[..., 0]) ** 2
        num += w * dt * du; den += w * dt ** 2
        f_prev = num / np.maximum(den, 1e-30) / (2 * np.pi)
    return f_prev if mask is None else f_prev * np.asarray(mask, bool)


def vsharp(field_hz, mask, voxel_size_mm, radii_mm=None, threshold=0.05):
    """V-SHARP background field removal (Li et al. 2011; Wu et al. 2012). Spherical mean-value filtering with
    radii decreasing towards the mask boundary, then deconvolution with the largest-radius kernel (truncated
    below threshold). Returns (local_field_hz, valid_mask); valid_mask = mask eroded by the smallest radius.
    Default radii: from 12 mm down to 2 voxels of the coarsest axis."""
    m = np.asarray(mask, bool); sh = m.shape; vmax = float(max(voxel_size_mm))
    if radii_mm is None:
        radii_mm = np.arange(12.0, 2 * vmax - 1e-6, -vmax)
    radii_mm = sorted(np.atleast_1d(radii_mm), reverse=True)
    ps = padded_shape(sh, 1.25)
    F = np.fft.fftn(_pad(np.asarray(field_hz, float) * m, ps))
    delta = np.zeros(ps); delta[(0,) * len(ps)] = 1.0
    out = np.zeros(sh); assigned = np.zeros(sh, bool); S_big = None
    for r in radii_mm:
        S = np.fft.fftn(delta - sphere_kernel(ps, voxel_size_mm, r)).real
        if S_big is None:
            S_big = S
        er = erode(m, voxel_size_mm, r)
        fr = _crop(np.real(np.fft.ifftn(S * F)), sh)
        new = er & ~assigned; out[new] = fr[new]; assigned |= er
    with np.errstate(divide='ignore', invalid='ignore'):
        inv = np.where(np.abs(S_big) > threshold, 1.0 / S_big, 0.0)
    local = _crop(np.real(np.fft.ifftn(inv * np.fft.fftn(_pad(out * assigned, ps)))), sh)
    valid = erode(m, voxel_size_mm, radii_mm[-1])
    return local * valid, valid


def pdf_background(field_hz, mask, voxel_size_mm, b0_dir, weights=None, n_iter=200, tol=1e-6, pad=1.5):
    """Projection onto dipole fields (Liu et al., NMR Biomed 2011): fit the field inside the mask with dipoles
    placed only OUTSIDE it (least squares by conjugate gradients); that fitted part is the background field.
    Robust to strong air/sinus fields and keeps the local field up to the mask edge. Returns (local_hz, mask).
    weights: optional data weights (e.g. magnitude) inside the mask."""
    m = np.asarray(mask, bool); sh = m.shape; ps = padded_shape(sh, pad)
    M = _pad(m.astype(float), ps); out = 1.0 - M
    w2 = M if weights is None else _pad(np.asarray(weights, float) ** 2, ps) * M
    D = dipole_kernel(ps, voxel_size_mm, b0_dir)
    Dop = lambda x: np.real(np.fft.ifftn(D * np.fft.fftn(x)))
    f = _pad(np.asarray(field_hz, float), ps)
    A = lambda x: out * Dop(w2 * Dop(out * x))
    b = out * Dop(w2 * f)
    x = np.zeros(ps); r = b.copy(); p = r.copy(); rs = np.sum(r * r); b2 = np.sum(b * b)
    for _ in range(n_iter):
        Ap = A(p); a = rs / max(np.sum(p * Ap), 1e-30); x += a * p; r -= a * Ap; rn = np.sum(r * r)
        if rn < tol ** 2 * b2:
            break
        p = r + (rn / rs) * p; rs = rn
    bg = _crop(Dop(out * x), sh)
    return (np.asarray(field_hz, float) - bg) * m, m


def invert_tkd(local_hz, mask, voxel_size_mm, b0_dir, b0_T, threshold=0.19, gamma_bar=GAMMA_BAR_1H):
    """Truncated k-space division (Shmueli et al. 2009): fast, but streaks and underestimates (about the
    fraction of k-space truncated). Prefer invert_cg_l2 for values; use TKD as an independent sanity check."""
    sh = local_hz.shape; ps = padded_shape(sh, 1.5)
    D = dipole_kernel(ps, voxel_size_mm, b0_dir)
    Dt = np.where(np.abs(D) >= threshold, D, threshold * np.where(D >= 0, 1.0, -1.0))
    Dinv = np.where(D == 0, 0.0, 1.0 / Dt)
    chi = np.real(np.fft.ifftn(Dinv * np.fft.fftn(_pad(np.asarray(local_hz, float) * ppm_per_hz(b0_T, gamma_bar) * mask, ps))))
    return _crop(chi, sh) * mask


def invert_cg_l2(local_hz, mask, voxel_size_mm, b0_dir, b0_T, lam=5e-4, weights=None, n_iter=200, tol=1e-4,
                 gamma_bar=GAMMA_BAR_1H):
    """Dipole inversion by conjugate gradients: min || W M (D chi - f) ||^2 + lam || grad chi ||^2 with the data
    term only inside mask (f in ppm). Gradient uses physical voxel sizes (1/mm). Larger lam smooths and lowers
    contrast; check the scale on a phantom with your geometry (test_qsm_lib.py shows how)."""
    sh = local_hz.shape; ps = padded_shape(sh, 1.5); m = _pad(np.asarray(mask, float), ps)
    w2 = m if weights is None else _pad(np.asarray(weights, float) ** 2, ps) * m
    D = dipole_kernel(ps, voxel_size_mm, b0_dir)
    k = kspace_grid(ps, voxel_size_mm); v = voxel_size_mm
    E2 = sum((2 - 2 * np.cos(2 * np.pi * c * vi)) / vi ** 2 for c, vi in zip(k, v))     # |finite difference|^2
    fppm = _pad(np.asarray(local_hz, float) * ppm_per_hz(b0_T, gamma_bar), ps)
    Dop = lambda x: np.real(np.fft.ifftn(D * np.fft.fftn(x)))
    A = lambda x: Dop(w2 * Dop(x)) + lam * np.real(np.fft.ifftn(E2 * np.fft.fftn(x)))
    b = Dop(w2 * fppm)
    x = np.zeros(ps); r = b - A(x); p = r.copy(); rs = np.sum(r * r); b2 = np.sum(b * b)
    for _ in range(n_iter):
        Ap = A(p); a = rs / max(np.sum(p * Ap), 1e-30); x += a * p; r -= a * Ap; rn = np.sum(r * r)
        if rn < tol ** 2 * b2:
            break
        p = r + (rn / rs) * p; rs = rn
    return _crop(x, sh) * np.asarray(mask, bool)


def reference_to_roi(chi, rois, reference_label, mask=None):
    """Subtract the mean chi of a reference region (e.g. ventricular CSF). Returns (chi_ref, reference_mean)."""
    sel = (np.asarray(rois) == reference_label)
    if mask is not None:
        sel &= np.asarray(mask, bool)
    ref = float(np.mean(chi[sel])) if sel.any() else 0.0
    return (chi - ref) * (np.ones_like(chi) if mask is None else np.asarray(mask, bool)), ref


def roi_means(values, rois, mask=None):
    """Mean value per nonzero ROI label, restricted to mask if given: {label: (mean, n_voxels)}."""
    out = {}; r = np.asarray(rois)
    for lab in np.unique(r[r > 0]):
        sel = (r == lab) if mask is None else ((r == lab) & np.asarray(mask, bool))
        if sel.any():
            out[int(lab)] = (float(np.mean(values[sel])), int(sel.sum()))
    return out


def synthetic_head(shape=(64, 64, 40), voxel_size_mm=(1.5, 1.5, 2.0), b0_dir=(0.0, 0.26, 0.966), b0_T=3.0,
                   te=(0.004, 0.009, 0.014, 0.019), noise=0.02, seed=0):
    """Simulated multi-echo head for self-tests: brain ellipsoid, deep nuclei and ventricles inside, strong air /
    sinus sources outside the brain, smooth nonzero phase0, wrapped phase. Returns a dict with mag, phase,
    te, mask, rois (1..4 nuclei, 5 CSF), chi_ppm (truth, CSF-referenced inside the brain), local_hz (truth)."""
    rng = np.random.default_rng(seed); v = np.asarray(voxel_size_mm, float)
    g = np.meshgrid(*[(np.arange(n) - n / 2) * vi for n, vi in zip(shape, v)], indexing='ij')
    x, y, z = g
    def ell(c, r):
        return ((x - c[0]) / r[0]) ** 2 + ((y - c[1]) / r[1]) ** 2 + ((z - c[2]) / r[2]) ** 2 <= 1
    head = ell((0, 0, 0), (46, 46, 38)); brain = ell((0, 0, 0), (37, 37, 29))      # scalp/skull margin outside the mask
    chi = np.zeros(shape)
    rois = np.zeros(shape, np.uint8)
    nuclei = [((-12, 6, 2), (6, 5, 6), 0.12), ((12, 6, 2), (6, 5, 6), 0.08), ((-8, -10, -4), (4, 4, 5), 0.18),
              ((10, -9, -4), (5, 4, 5), 0.05)]
    for i, (c, r, val) in enumerate(nuclei, 1):
        sel = ell(c, r); chi[sel] = val; rois[sel] = i
    csf = ell((0, 12, 6), (4, 7, 6)); chi[csf] = -0.02; rois[csf] = 5
    tex = brain & ~(rois > 0); chi[tex] += (0.01 * np.sin(x / 9.0) * np.cos(y / 11.0))[tex]          # mild texture
    air = ((~head) | ell((0, 42, -14), (10, 3, 6))) & ~brain                         # outside air and a frontal sinus
    chi_all = chi * brain + 9.4 * air
    f_total = field_from_chi(chi_all, v, b0_dir, b0_T)
    f_local = field_from_chi(chi * brain, v, b0_dir, b0_T)
    phase0 = 0.8 * np.sin(x / 30.0) + 0.5 * np.cos(y / 25.0) + 0.3
    mag = np.where(head & ~air, 1.0, 0.03)
    te = np.asarray(te, float)
    ph = np.stack([np.angle(np.exp(1j * (phase0 + 2 * np.pi * f_total * t))) for t in te], -1)
    ph = np.angle(np.exp(1j * (ph + noise * rng.normal(size=ph.shape) / np.maximum(mag[..., None], 1e-3))))
    chi_ref = (chi - np.mean(chi[csf])) * brain
    return dict(mag=np.repeat(mag[..., None], len(te), -1), phase=ph, te=te, mask=brain, rois=rois * brain,
                chi_ppm=chi_ref, local_hz=f_local * brain, voxel_size_mm=tuple(v), b0_dir=b0_dir, b0_T=b0_T)


def _corr(a, b):
    a = a - a.mean(); b = b - b.mean(); return float(np.sum(a * b) / np.sqrt(np.sum(a * a) * np.sum(b * b)))


def run_pipeline(magnitude, phase_rad, te, mask, voxel_size_mm, b0_dir, b0_T, rois=None, reference_label=None,
                 lam=5e-4, gamma_bar=GAMMA_BAR_1H):
    """Default chain: field -> PDF -> CG-L2 -> optional reference. Returns dict(field_hz, local_hz, chi_ppm, ref)."""
    f = multiecho_field_hz(magnitude, phase_rad, te, voxel_size_mm, mask)
    w = np.sqrt(np.mean(np.asarray(magnitude, float) ** 2, -1)) * mask
    loc, _ = pdf_background(f, mask, voxel_size_mm, b0_dir, weights=w / max(w.max(), 1e-30))
    chi = invert_cg_l2(loc, mask, voxel_size_mm, b0_dir, b0_T, lam=lam, gamma_bar=gamma_bar)
    ref = 0.0
    if rois is not None and reference_label is not None:
        chi, ref = reference_to_roi(chi, rois, reference_label, mask)
    return dict(field_hz=f, local_hz=loc, chi_ppm=chi, reference_mean=ref)




def _print_api(namespace):
    """Signatures and one-line summaries of the public functions (python <module>.py --api)."""
    import inspect
    for name, f in sorted(namespace.items()):
        if inspect.isfunction(f) and not name.startswith('_') and f.__module__ == '__main__':
            doc = ((inspect.getdoc(f) or '').splitlines() or [''])[0]
            print(f"{name}{inspect.signature(f)}" + chr(10) + f"    {doc}")


if __name__ == '__main__':
    import sys
    if '--api' in sys.argv:
        _print_api(dict(globals()))
    if '--selftest' in sys.argv:
        h = synthetic_head()
        out = run_pipeline(h['mag'], h['phase'], h['te'], h['mask'], h['voxel_size_mm'], h['b0_dir'], h['b0_T'], h['rois'], 5)
        deep = erode(h['mask'], h['voxel_size_mm'], 12)
        rm = roi_means(out['chi_ppm'], h['rois'], h['mask']); tm = roi_means(h['chi_ppm'], h['rois'], h['mask'])
        est = np.array([rm[k][0] for k in sorted(rm) if k != 5]); tru = np.array([tm[k][0] for k in sorted(tm) if k != 5])
        print(f"deep local field corr {_corr(out['local_hz'][deep], h['local_hz'][deep]):.3f}; "
              f"ROI slope {np.sum(est * tru) / np.sum(tru * tru):.2f}, corr {_corr(est, tru):.3f}")
