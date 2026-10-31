"""MRFoundry reconstruction helpers with explicit, tested conventions.

Signal model: s(k) = sum_r m(r) exp(-2*pi*i*k.r). Image arrays are [y, x] with the object
position r = (index - n//2) * fov / n, so the k-space sample at index n//2 is k = 0.
Tested with numpy 2.x and sigpy 0.1.27 against a direct DFT.
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

def cartesian_image(kspace):
    """Centred inverse FFT over the last two axes ([..., ky, kx] -> [..., y, x]).
    kspace[..., j, i] must hold the sample at ky = (j - ny//2)/fov, kx = (i - nx//2)/fov."""
    ny, nx = kspace.shape[-2:]
    return np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(kspace, axes=(-2, -1)), axes=(-2, -1)), axes=(-2, -1))

def direct_dft(image, kxy_cycles_per_m, fov_m):
    """Forward model for checks: image [y, x] -> samples at kxy[..., (kx, ky)] in cycles/m."""
    ny, nx = image.shape
    x = (np.arange(nx) - nx // 2) * fov_m / nx; y = (np.arange(ny) - ny // 2) * fov_m / ny
    yy, xx = np.meshgrid(y, x, indexing='ij'); k = np.asarray(kxy_cycles_per_m).reshape(-1, 2)
    out = np.empty(len(k), complex)
    for s in range(0, len(k), 256):
        c = k[s:s+256]; out[s:s+256] = np.exp(-2j*np.pi*(c[:, :1]*xx.ravel() + c[:, 1:]*yy.ravel())) @ image.ravel()
    return out.reshape(np.shape(kxy_cycles_per_m)[:-1])

def nufft_least_squares(samples, kxy_cycles_per_m, fov_m, shape, lamda=1e-5, max_iter=200, weights=None):
    """Non-Cartesian least-squares reconstruction with SigPy (NUFFT + conjugate gradient).
    kxy in cycles/m with last axis (kx, ky). SigPy wants coordinates in grid units, ordered like the
    image axes (y, x): coord = kxy[..., [1, 0]] * fov. Returns image [y, x] in the direct_dft
    scaling and the relative data residual."""
    import sigpy as sp
    coord = np.asarray(kxy_cycles_per_m)[..., [1, 0]] * fov_m
    A = sp.linop.NUFFT(tuple(shape), coord, oversamp=2, width=6)
    if weights is not None:
        W = sp.linop.Multiply(A.oshape, np.sqrt(weights)); A = W * A; samples = np.sqrt(weights) * samples
    img = sp.app.LinearLeastSquares(A, samples, lamda=lamda, max_iter=max_iter, tol=1e-10, show_pbar=False).run()
    res = float(np.linalg.norm(A(img) - samples) / np.linalg.norm(samples))
    # SigPy's NUFFT is orthonormally scaled (1/sqrt(n_pixels)); rescale to the direct-sum model above.
    return img / np.sqrt(np.prod(shape)), res


def offres_encoding(kxy_cycles_per_m, t_s, fieldmap_hz, fov_m, phase_sign=-1, dtype=np.complex64):
    """Explicit encoding matrix with off-resonance: E[s, r] = exp(-2 pi i k_s.r) exp(phase_sign 2 pi i f(r) t_s).
    kxy [Ns, 2] in cycles/m (kx, ky), t_s [Ns] sample times from the excitation centre (the same reference the
    field map phase uses), fieldmap_hz [ny, nx] on the image grid. phase_sign: sign of the off-resonance phase in
    the demodulated signal (-1 if an isochromat at +f accrues exp(-i 2 pi f t)); confirm it on a simulated point.
    Memory Ns x ny x nx complex64 (8 bytes each): fine up to ~5e7 entries; beyond that use time segmentation."""
    f = np.asarray(fieldmap_hz, float); ny, nx = f.shape
    x = (np.arange(nx) - nx // 2) * fov_m / nx; y = (np.arange(ny) - ny // 2) * fov_m / ny
    yy, xx = np.meshgrid(y, x, indexing='ij'); k = np.asarray(kxy_cycles_per_m, float).reshape(-1, 2)
    t = np.asarray(t_s, float).reshape(-1)
    if len(t) != len(k):
        raise ValueError('one time per k-space sample is needed')
    if len(k) * f.size > 6e7:
        raise MemoryError(f'{len(k)} x {f.size} entries: use time segmentation or a NUFFT-based model')
    E = np.empty((len(k), f.size), dtype)
    for s in range(0, len(k), 512):
        ph = -2 * np.pi * (k[s:s + 512, :1] * xx.ravel() + k[s:s + 512, 1:] * yy.ravel()) + phase_sign * 2 * np.pi * t[s:s + 512, None] * f.ravel()
        E[s:s + 512] = np.exp(1j * ph)
    return E


def offres_least_squares(samples, kxy_cycles_per_m, t_s, fieldmap_hz, fov_m, phase_sign=-1, lamda=1e-3, n_iter=100, tol=1e-6, weights=None):
    """Off-resonance-corrected non-Cartesian reconstruction: CG on (E^H W E + lamda s I) x = E^H W y with the exact
    encoding (offres_encoding) and s = mean diagonal of E^H W E. Returns (image [ny, nx] in the direct_dft
    scaling, relative data residual). Choose lamda by simulated error, not by the residual alone."""
    E = offres_encoding(kxy_cycles_per_m, t_s, fieldmap_hz, fov_m, phase_sign)
    y = np.asarray(samples, complex).reshape(-1); w = np.ones(len(y)) if weights is None else np.asarray(weights, float).reshape(-1)
    b = E.conj().T @ (w * y); scale = float(np.mean(w) * E.shape[0]); lam = lamda * scale
    A = lambda v: E.conj().T @ (w * (E @ v)) + lam * v
    x = np.zeros(E.shape[1], complex); r = b - A(x); p = r.copy(); rs = np.vdot(r, r).real; b2 = np.vdot(b, b).real
    for _ in range(n_iter):
        Ap = A(p); al = rs / np.vdot(p, Ap).real; x = x + al * p; r = r - al * Ap; rn = np.vdot(r, r).real
        if rn < tol ** 2 * b2:
            break
        p = r + (rn / rs) * p; rs = rn
    res = float(np.linalg.norm(E @ x - y) / np.linalg.norm(y))
    return x.reshape(np.shape(fieldmap_hz)), res


def smooth_field(values, weights, sigma_vox, order=1):
    """Weighted Gaussian smoothing of a field map by normalized convolution (Knutsson & Westin 1993).
    order=1 (default) fits a local plane a + b x + c y with weights w(r') G(r - r'), so a linear field is kept
    exactly, also at object edges and across empty voxels (order=0, the plain weighted mean, pulls edge values
    toward the interior). Use magnitude^2 or a mask as weights; extrapolates into the background. Choose sigma
    (about 0.5-1.5 voxels for two-echo maps) by simulated error of the final image or endpoint."""
    from numpy.fft import fft2, ifft2
    v = np.asarray(values, float); w = np.asarray(weights, float); ny, nx = v.shape; p = int(3 * sigma_vox) + 1
    sh = (ny + 2 * p, nx + 2 * p)
    gy = np.exp(-0.5 * (np.fft.fftfreq(sh[0]) * sh[0] / sigma_vox) ** 2); gx = np.exp(-0.5 * (np.fft.fftfreq(sh[1]) * sh[1] / sigma_vox) ** 2)
    K = fft2(np.outer(gy, gx))
    def conv(a):
        z = np.zeros(sh); z[p:p + ny, p:p + nx] = a
        return np.real(ifft2(fft2(z) * K))[p:p + ny, p:p + nx]
    if order == 0:
        return conv(w * v) / np.maximum(conv(w), 1e-12 * max(w.max(), 1e-30))
    yy, xx = np.mgrid[0:ny, 0:nx].astype(float)
    basis = [np.ones_like(v), xx, yy]
    G = np.empty((ny, nx, 3, 3)); r = np.empty((ny, nx, 3))
    for i in range(3):
        r[..., i] = conv(w * v * basis[i])
        for j in range(i, 3):
            G[..., i, j] = G[..., j, i] = conv(w * basis[i] * basis[j])
    G = G + 1e-9 * np.max(G[..., 0, 0]) * np.eye(3)
    coef = np.linalg.solve(G, r[..., None])[..., 0]
    out = coef[..., 0] + coef[..., 1] * xx + coef[..., 2] * yy
    low = conv(w) < 1e-6 * max(conv(w).max(), 1e-30)
    out[low] = 0.0
    return out
