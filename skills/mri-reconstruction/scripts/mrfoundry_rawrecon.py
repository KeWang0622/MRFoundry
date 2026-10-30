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


# ------------------------------------------------------------------ noise
def noise_covariance(noise):
    """Noise covariance (C x C) from noise-only samples [coil, samples] (any trailing shape)."""
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

