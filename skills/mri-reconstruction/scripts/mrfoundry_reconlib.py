"""MRFoundry reconstruction helpers with explicit, tested conventions.

Signal model: s(k) = sum_r m(r) exp(-2*pi*i*k.r). Image arrays are [y, x] with the object
position r = (index - n//2) * fov / n, so the k-space sample at index n//2 is k = 0.
Tested with numpy 2.x and sigpy 0.1.27 against a direct DFT.
"""
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


def _print_api(namespace):
    """Signatures and one-line summaries of the public functions (python <module>.py --api)."""
    import inspect
    for name, f in sorted(namespace.items()):
        if inspect.isfunction(f) and not name.startswith('_') and f.__module__ == '__main__':
            doc = ((inspect.getdoc(f) or '').splitlines() or [''])[0]
            print(f"{name}{inspect.signature(f)}" + chr(10) + f"    {doc}")


if __name__ == '__main__' and '--api' in __import__('sys').argv:
    _print_api(dict(globals()))
