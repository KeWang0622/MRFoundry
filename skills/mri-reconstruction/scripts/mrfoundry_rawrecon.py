"""MRFoundry raw-data reconstruction helpers (numpy only; tested in test_rawrecon.py).

Conventions: multi-coil k-space arrays are [coil, ky, kx] (2D) with the k = 0 sample at
index n//2 along each axis (centred), and image arrays are [coil, y, x]. The FFT pair is
centred and orthonormal (norm='ortho'), matching SigPy's sp.fft/sp.ifft, so sums of
squares are preserved and white k-space noise stays white with the same variance in the
image. numpy's default unnormalized ifft2 (as in cartesian_image) differs by a constant
factor: say which scaling you report.
"""
import numpy as np


def fft2c(img, axes=(-2, -1)):
    """Centred orthonormal 2D FFT (image -> k-space)."""
    return np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(img, axes=axes), axes=axes, norm="ortho"), axes=axes)


def ifft2c(ksp, axes=(-2, -1)):
    """Centred orthonormal 2D inverse FFT (k-space -> image)."""
    return np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(ksp, axes=axes), axes=axes, norm="ortho"), axes=axes)


def rss(coil_images, axis=0):
    return np.sqrt(np.sum(np.abs(coil_images) ** 2, axis=axis))


def image_from_kspace(ksp, encoding_sign=-1, axes=(-2, -1)):
    """Centred orthonormal reconstruction that honours the encoding sign of the data.

    Standard MRI signal model: s(k) = sum_r m(r) exp(-i 2 pi k.r)  (encoding_sign=-1) -> image = ifft2c(s).
    Some vendors or simulators use exp(+i 2 pi k.r) (encoding_sign=+1) -> image = fft2c(s). Using the wrong
    transform mirrors the image in both axes and, for even matrix sizes, shifts it by one pixel. Read the sign
    from the data documentation; confirm it with direct_dft_signed on a small asymmetric object."""
    if encoding_sign not in (-1, 1):
        raise ValueError('encoding_sign must be -1 or +1')
    return ifft2c(ksp, axes) if encoding_sign == -1 else fft2c(ksp, axes)


def direct_dft_signed(image, encoding_sign=-1):
    """Independent forward model for convention checks: centred k and r indices (k = 0 and r = 0 at n//2),
    s[ky, kx] = sum_{y, x} m[y, x] exp(sign * i 2 pi (ky y / ny + kx x / nx)), orthonormal scaling.
    Written as an explicit sum (no FFT), so it checks FFT shift, sign and scaling conventions of a pipeline."""
    m = np.asarray(image)
    ny, nx = m.shape
    ky = np.arange(ny) - ny // 2
    kx = np.arange(nx) - nx // 2
    Ey = np.exp(encoding_sign * 2j * np.pi * np.outer(ky, ky) / ny)
    Ex = np.exp(encoding_sign * 2j * np.pi * np.outer(kx, kx) / nx)
    return Ey @ m @ Ex.T / np.sqrt(ny * nx)


# ------------------------------------------------------------------ noise
def noise_covariance(noise):
    """Noise covariance Psi = E[n n^H] (C x C) from noise-only samples [coil, samples] (any trailing shape).
    Convention trap: with samples as ROWS (X of shape [samples, coil]) the same matrix is X.T @ X.conj() / N;
    X.conj().T @ X gives conj(Psi), which whitens incorrectly whenever coils are correlated (complex Psi)."""
    n = np.asarray(noise).reshape(np.shape(noise)[0], -1)
    n = n - n.mean(axis=1, keepdims=True)
    return (n @ n.conj().T) / n.shape[1]


def prewhiten(data, psi):
    """Apply W = L^-1 (psi = L L^H) along the coil axis 0: whitened noise has identity
    covariance. Prewhiten the noise scan, calibration and imaging data with the same W,
    before coil-sensitivity estimation and reconstruction."""
    W = np.linalg.inv(np.linalg.cholesky(psi))
    d = np.asarray(data)
    return np.tensordot(W, d, axes=(1, 0))


def scale_noise_covariance(psi_noise, noise_dwell, imaging_dwell):
    """Per-sample noise covariance at the imaging dwell time from a noise scan at another dwell time.
    Thermal noise variance per sample is proportional to the receiver bandwidth 1/dwell (ideal filter), so
    Psi_imaging = Psi_noise * noise_dwell / imaging_dwell. Averaging N acquisitions divides it by N."""
    return np.asarray(psi_noise) * (float(noise_dwell) / float(imaging_dwell))


def snr_units_image(coil_images, psi, n_averages=1, sens=None):
    """Coil combination in SNR units (Kellman & McVeigh, MRM 2005).

    coil_images [coil, ...]: images from ORTHONORMAL transforms (ifft2c) of k-space that was averaged over
    n_averages; psi: per-sample noise covariance of ONE acquisition at the imaging dwell. With sens given, the
    result is the optimal B1-weighted combination sqrt(2) s^H Phi^-1 x / sqrt(s^H Phi^-1 s), Phi = psi/n_averages,
    whose real and imaginary noise each have SD 1, so |image| is SNR (signal over the SD of one real noise
    component). Without sens, the root-sum-of-squares of the prewhitened images times sqrt(2) is returned
    (same scale at high SNR). Check with a pseudo-replica or pure-noise run: the noise SD of the real part must be
    1. Never estimate the noise SD from low-magnitude pixels of the same image: selecting by magnitude biases it."""
    x = np.asarray(coil_images, complex); phi = np.asarray(psi, complex) / float(n_averages)
    W = np.linalg.inv(np.linalg.cholesky(phi))
    xw = np.tensordot(W, x, axes=(1, 0))
    if sens is None:
        return np.sqrt(2.0) * np.sqrt(np.sum(np.abs(xw) ** 2, axis=0))
    sw = np.tensordot(W, np.asarray(sens, complex), axes=(1, 0))
    num = np.sum(np.conj(sw) * xw, axis=0); den = np.sqrt(np.sum(np.abs(sw) ** 2, axis=0))
    return np.sqrt(2.0) * num / np.maximum(den, 1e-30)


def orientation_check(image, reference, mask=None, max_shift=2):
    """Which of the 8 flips/transposes (and small circular shifts) best matches a reference, by correlation of
    magnitudes. Use after reconstructing data simulated from a known asymmetric object with an independent
    forward model (direct_dft_signed, or direct_dft in mrfoundry_reconlib for non-Cartesian k): anything other
    than ('identity', (0, 0)) means an axis-order, sign or centring error. Returns (name, shift, corr, table)."""
    a = np.abs(np.asarray(image)); r = np.abs(np.asarray(reference))
    cands = {'identity': a, 'flip_y': a[::-1], 'flip_x': a[:, ::-1], 'flip_xy': a[::-1, ::-1]}
    if a.shape[0] == a.shape[1]:
        cands.update({'transpose': a.T, 'transpose_flip_y': a.T[::-1], 'transpose_flip_x': a.T[:, ::-1],
                      'transpose_flip_xy': a.T[::-1, ::-1]})
    m = np.ones(r.shape, bool) if mask is None else np.asarray(mask, bool)
    def corr(u, v):
        u = u[m] - u[m].mean(); v = v[m] - v[m].mean()
        return float(np.sum(u * v) / np.sqrt(np.sum(u * u) * np.sum(v * v) + 1e-30))
    table = []
    for name, c in cands.items():
        for dy in range(-max_shift, max_shift + 1):
            for dx in range(-max_shift, max_shift + 1):
                table.append((corr(np.roll(c, (dy, dx), (0, 1)), r), name, (dy, dx)))
    table.sort(key=lambda z: -z[0])
    return table[0][1], table[0][2], table[0][0], table[:5]


# ------------------------------------------------------------------ readout oversampling
def remove_readout_oversampling(ksp, factor=2, axis=-1):
    """Crop a readout oversampled by 'factor' (FOV x factor) to the nominal FOV.

    Transforms along the readout axis, keeps the central 1/factor of the image and
    transforms back (centred, orthonormal along that axis). The k-space matrix along the
    readout shrinks by 'factor'; the k = 0 index stays at n//2."""
    ksp = np.asarray(ksp)
    n = ksp.shape[axis]
    m = n // factor
    img = np.fft.fftshift(np.fft.ifft(np.fft.ifftshift(ksp, axes=axis), axis=axis, norm="ortho"), axes=axis)
    s = (n - m) // 2
    img = np.take(img, np.arange(s, s + m), axis=axis)
    out = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(img, axes=axis), axis=axis, norm="ortho"), axes=axis)
    return out  # orthonormal per axis: image voxel values are unchanged by the crop


# ------------------------------------------------------------------ GRAPPA
def grappa_2d(ksp, R, acs, kernel_kx=5, lamda=1e-3):
    """GRAPPA for 2D Cartesian data undersampled by R along ky.

    ksp: [coil, ky, kx] with zeros at missing lines (acquired lines every R along ky,
    plus any acquired ACS lines); acs: [coil, n_acs, kx] fully sampled calibration
    block (contiguous lines; may be taken from ksp). Kernel: the two nearest acquired
    lines (y0, y0 + R) x kernel_kx readout neighbours from all coils, one weight set per
    missing offset 1..R-1, Tikhonov-regularized (lamda relative to the source energy).
    Acquired samples are kept unchanged (including ACS lines present in ksp).
    """
    ksp = np.asarray(ksp, complex)
    C, ny, nx = ksp.shape
    acs = np.asarray(acs, complex)
    hk = kernel_kx // 2
    acquired = np.any(np.abs(ksp) > 0, axis=(0, 2))
    # regular sampling offset: the most common residue of acquired line indices modulo R
    idx = np.nonzero(acquired)[0]
    off = np.bincount(idx % R, minlength=R).argmax()
    weights = {}
    na = acs.shape[1]
    for d in range(1, R):
        S, T = [], []
        for y0 in range(0, na - R):
            for x in range(hk, nx - hk):
                src = np.concatenate([acs[:, y0, x - hk:x + hk + 1].ravel(), acs[:, y0 + R, x - hk:x + hk + 1].ravel()])
                S.append(src)
                T.append(acs[:, y0 + d, x])
        S, T = np.array(S), np.array(T)
        G = S.conj().T @ S
        lam = lamda * np.real(np.trace(G)) / G.shape[0]
        weights[d] = np.linalg.solve(G + lam * np.eye(G.shape[0]), S.conj().T @ T)
    pad = np.zeros((C, ny + 2 * R, nx + 2 * hk), complex)
    pad[:, R:R + ny, hk:hk + nx] = ksp
    out = ksp.copy()
    for y in range(ny):
        if acquired[y]:
            continue
        d = (y - off) % R
        y0 = y - d
        if d == 0:
            continue
        rows = []
        for x in range(nx):
            rows.append(np.concatenate([pad[:, y0 + R, x:x + 2 * hk + 1].ravel(), pad[:, y0 + 2 * R, x:x + 2 * hk + 1].ravel()]))
        out[:, y, :] = (np.array(rows) @ weights[d]).T
    return out


# ------------------------------------------------------------------ partial Fourier
def pocs_partial_fourier(ksp, sampled, n_iter=30, center_lines=None, axis=-2):
    """POCS partial-Fourier reconstruction for asymmetric sampling along one axis.

    ksp: [..., ky, kx] (coil axes allowed in front) with zeros where not acquired;
    sampled: boolean mask over that axis (True for acquired lines, contiguous from one
    edge past the centre). The low-resolution phase comes from the symmetric central
    region (2 * (number of lines past centre)); the image magnitude is then iterated
    with that phase while keeping acquired data. Returns the complex image with the
    estimated phase. Compare with zero filling, which blurs along the axis."""
    ksp = np.asarray(ksp, complex)
    ax = axis % ksp.ndim
    n = ksp.shape[ax]
    sampled = np.asarray(sampled, bool)
    c = n // 2
    if center_lines is None:
        acq = np.nonzero(sampled)[0]
        half = min(c - acq.min(), acq.max() - c)
        center_lines = 2 * half
    shp = [1] * ksp.ndim
    shp[ax] = n
    win = np.zeros(n)
    h = center_lines // 2
    win[c - h:c + h] = np.hanning(2 * h) if h > 0 else 1
    lowres = ifft2c(ksp * win.reshape(shp))
    phase = np.exp(1j * np.angle(lowres))
    m = sampled.reshape(shp)
    img = ifft2c(ksp)
    for _ in range(n_iter):
        img = np.abs(img) * phase
        k = fft2c(img)
        k = np.where(m, ksp, k)
        img = ifft2c(k)
    return img


# ------------------------------------------------------------------ SENSE and SNR
def sense_cg(ksp, mask, sens, lamda=0.0, n_iter=50):
    """Cartesian CG-SENSE: solve min ||M F S x - y||^2 + lamda ||x||^2.

    ksp: [coil, ky, kx] (zeros at unsampled positions), mask: [ky, kx] or [ky] (bool),
    sens: [coil, y, x] coil maps (same orientation as ifft2c images; normalize so that
    sum |s|^2 = 1 inside the object for an unbiased magnitude scale)."""
    ksp = np.asarray(ksp, complex)
    sens = np.asarray(sens, complex)
    m = np.asarray(mask, bool)
    if m.ndim == 1:
        m = np.repeat(m[:, None], ksp.shape[-1], 1)
    def A(x):
        return fft2c(sens * x[None]) * m
    def AH(y):
        return np.sum(sens.conj() * ifft2c(y * m), axis=0)
    b = AH(ksp)
    x = np.zeros_like(b)
    r = b.copy()
    p = r.copy()
    rs = np.vdot(r, r).real
    for _ in range(n_iter):
        Ap = AH(A(p)) + lamda * p
        a = rs / np.vdot(p, Ap).real
        x = x + a * p
        r = r - a * Ap
        rn = np.vdot(r, r).real
        if rn < 1e-20 * np.vdot(b, b).real:
            break
        p = r + (rn / rs) * p
        rs = rn
    return x


def pseudo_replica(recon, ksp, psi=None, n_rep=50, seed=0, mask=None):
    """Pseudo-replica noise map (Robson et al. 2008): reconstruct n_rep copies of the data
    with added synthetic noise of covariance psi (identity if prewhitened) and return
    the per-pixel standard deviation of the reconstructed magnitude. recon: function
    k-space -> image. Noise is added only where the data were sampled (mask).
    SNR = signal / noise_std; g = std_accelerated / (std_full * sqrt(R)) when the full
    and accelerated reconstructions use the same scaling."""
    rng = np.random.default_rng(seed)
    ksp = np.asarray(ksp, complex)
    C = ksp.shape[0]
    L = np.eye(C) if psi is None else np.linalg.cholesky(psi)
    base = recon(ksp)
    reps = []
    if mask is None:
        mask = np.any(np.abs(ksp) > 0, axis=0)
    for _ in range(n_rep):
        z = (rng.normal(size=ksp.shape) + 1j * rng.normal(size=ksp.shape)) / np.sqrt(2)
        z = np.tensordot(L, z, axes=(1, 0)) * mask
        reps.append(recon(ksp + z))
    reps = np.array(reps)
    return np.std(reps - base[None], axis=0)


def coil_maps_from_acs(ksp, acs_mask, eps=1e-3):
    """Smooth coil sensitivity estimate from the calibration region: images of the Hann-windowed ACS k-space
    ([coil, ky, kx] with acs_mask [ky] or [ky, kx] marking calibration samples), normalized so that
    sum_c |s_c|^2 = 1 (then a SENSE image is in RSS-like units). Use ESPIRiT (BART/SigPy) when available; this is
    a dependable numpy fallback for CG-SENSE."""
    k = np.asarray(ksp, complex); m = np.asarray(acs_mask, bool)
    if m.ndim == 1:
        m = np.repeat(m[:, None], k.shape[-1], 1)
    rows = np.flatnonzero(m.any(1)); cols = np.flatnonzero(m.any(0))
    w = np.zeros(m.shape)
    w[np.ix_(rows, cols)] = np.outer(np.hanning(len(rows) + 2)[1:-1], np.hanning(len(cols) + 2)[1:-1])
    low = ifft2c(k * (w * m)[None])
    r = np.sqrt(np.sum(np.abs(low) ** 2, 0))
    return low / np.maximum(r, eps * r.max())[None]


def rank_reconstructions(candidates, truth, sens, mask, psi=None, n_rep=3, seed=0, region=None, noise_scale=1.0):
    """Choose a reconstruction (method, regularization, iterations) by its error on SIMULATED data with your
    sampling and your measured noise, not by data consistency: an exactly data-consistent result keeps all the
    noise. candidates: dict name -> function(ksp [coil, ky, kx] with zeros at unsampled positions) -> image;
    truth: complex or magnitude image on the output grid (e.g. a smooth phantom or a high-SNR reference);
    sens: coil maps used to simulate; mask: sampled positions [ky, kx] or [ky]; psi: noise covariance
    (prewhitened data: identity). Returns a list of (mean NRMSE, name) sorted best first (NRMSE with scale fit,
    magnitudes, inside region)."""
    rng = np.random.default_rng(seed); s = np.asarray(sens, complex); C = s.shape[0]
    m = np.asarray(mask, bool)
    if m.ndim == 1:
        m = np.repeat(m[:, None], s.shape[-1], 1)
    L = np.eye(C) if psi is None else np.linalg.cholesky(psi)
    clean = fft2c(s * np.asarray(truth)[None]) * m[None]
    reg = np.ones(m.shape, bool) if region is None else np.asarray(region, bool)
    scores = {k: [] for k in candidates}
    for _ in range(n_rep):
        z = (rng.normal(size=clean.shape) + 1j * rng.normal(size=clean.shape)) / np.sqrt(2)
        y = clean + noise_scale * np.tensordot(L, z, axes=(1, 0)) * m[None]
        for k, f in candidates.items():
            scores[k].append(nrmse(np.abs(truth), np.abs(f(y)), reg)[0])
    return sorted((float(np.mean(v)), k) for k, v in scores.items())


# ------------------------------------------------------------------ evaluation
def nrmse(ref, img, mask=None, fit_scale=True):
    """Normalized RMSE ||a*img - ref|| / ||ref|| inside mask, with the least-squares
    scale a (fit_scale=True) or a = 1. Report which one; magnitude images should be
    compared as magnitudes."""
    ref = np.asarray(ref)
    img = np.asarray(img)
    m = np.ones(ref.shape, bool) if mask is None else np.asarray(mask, bool)
    r, x = ref[m], img[m]
    a = (np.vdot(x, r) / np.vdot(x, x)) if fit_scale else 1.0
    if np.isrealobj(ref) and np.isrealobj(img):
        a = np.real(a)
    return float(np.linalg.norm(a * x - r) / np.linalg.norm(r)), a


def _print_api(namespace):
    """Signatures and one-line summaries of the public functions (python <module>.py --api)."""
    import inspect
    for name, f in sorted(namespace.items()):
        if inspect.isfunction(f) and not name.startswith('_') and f.__module__ == '__main__':
            doc = ((inspect.getdoc(f) or '').splitlines() or [''])[0]
            print(f"{name}{inspect.signature(f)}" + chr(10) + f"    {doc}")


if __name__ == '__main__' and '--api' in __import__('sys').argv:
    _print_api(dict(globals()))
