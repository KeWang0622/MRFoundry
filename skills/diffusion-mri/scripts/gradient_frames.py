"""Diffusion gradient-table frames (numpy only; tested in test_gradient_frames.py).

Frames
- world (scanner/RAS+ in NIfTI terms): the frame of the image affine's output coordinates.
- array: components along the image array axes i, j, k (what a voxelwise numpy fit "sees").
- FSL bvecs: array-axis components, with the x (i) component negated when the determinant of the
  affine's 3x3 part is positive (FSL's radiological voxel convention; documented by FSL and MRtrix3).
MRtrix3 gradient tables (-grad) are in world coordinates. Check what each tool expects, convert
explicitly, and verify with a forward phantom built from world-frame gradients.
"""
import numpy as np


def direction_cosines(affine):
    """3x3 matrix whose columns are the unit world directions of the array axes."""
    A = np.asarray(affine, float)[:3, :3]
    return A / np.linalg.norm(A, axis=0, keepdims=True)


def _flip_x(affine):
    return np.linalg.det(np.asarray(affine, float)[:3, :3]) > 0


def array_from_world(g_world, affine):
    """Gradient directions (n, 3) in world coordinates -> array-axis components."""
    return np.asarray(g_world, float) @ direction_cosines(affine)


def world_from_array(v_array, affine):
    return np.asarray(v_array, float) @ direction_cosines(affine).T


def fsl_from_world(g_world, affine):
    v = array_from_world(g_world, affine)
    if _flip_x(affine):
        v[:, 0] *= -1
    return v


def array_from_fsl(bvecs, affine):
    """FSL bvecs (n, 3) -> array-axis components (negate x when det(affine) > 0)."""
    v = np.array(bvecs, float).reshape(-1, 3)
    if _flip_x(affine):
        v[:, 0] *= -1
    return v


def world_from_fsl(bvecs, affine):
    return world_from_array(array_from_fsl(bvecs, affine), affine)


def read_fsl_bvecs(path):
    """Read an FSL .bvec file (3 rows x n or n x 3) as (n, 3)."""
    v = np.loadtxt(path)
    return v.T if v.shape[0] == 3 and v.shape[1] != 3 else v


def simulate_tensor_signal(D_world, g_world, bvals, s0=1.0):
    """Forward phantom: S = S0 exp(-b g^T D g) with D and g in WORLD coordinates (independent of any
    tool's internal frame). D_world (3, 3) in mm^2/s, bvals in s/mm^2."""
    g = np.asarray(g_world, float)
    return s0 * np.exp(-np.asarray(bvals, float) * np.einsum('ni,ij,nj->n', g, np.asarray(D_world, float), g))


def fit_tensor_lls(signals, bvals, g, b0_threshold=50.0):
    """Log-linear tensor fit (closed form; numpy). g must be in the frame you want D in.
    signals (..., n). Returns D (..., 3, 3), eigenvalues (descending) and principal eigenvectors."""
    S = np.asarray(signals, float)
    b = np.asarray(bvals, float)
    g = np.asarray(g, float)
    s0 = S[..., b <= b0_threshold].mean(-1, keepdims=True)
    y = -np.log(np.clip(S / s0, 1e-12, None)) / np.where(b > b0_threshold, b, np.inf)
    keep = b > b0_threshold
    gx, gy, gz = g[keep].T
    X = np.stack([gx * gx, gy * gy, gz * gz, 2 * gx * gy, 2 * gx * gz, 2 * gy * gz], 1)
    coef = np.linalg.lstsq(X, y[..., keep].reshape(-1, keep.sum()).T, rcond=None)[0].T
    dxx, dyy, dzz, dxy, dxz, dyz = coef.T
    D = np.stack([np.stack([dxx, dxy, dxz], -1), np.stack([dxy, dyy, dyz], -1), np.stack([dxz, dyz, dzz], -1)], -2)
    w, V = np.linalg.eigh(D)
    order = np.argsort(w, axis=-1)[..., ::-1]
    w = np.take_along_axis(w, order, -1)
    V = np.take_along_axis(V, order[..., None, :], -1)
    shape = S.shape[:-1]
    return D.reshape(shape + (3, 3)), w.reshape(shape + (3,)), V[..., :, 0].reshape(shape + (3,))

