"""Frame tests (python test_gradient_frames.py): a forward phantom built from WORLD-frame gradients
must give a principal eigenvector along the known world direction after converting FSL bvecs, for
oblique affines with positive and negative determinants; skipping the FSL x-negation fails when
det > 0."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gradient_frames import *

rng = np.random.default_rng(0)
def rot(a, b, c):
    ca, sa, cb, sb, cc, sc = np.cos(a), np.sin(a), np.cos(b), np.sin(b), np.cos(c), np.sin(c)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]); Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
g = rng.normal(size=(30, 3)); g /= np.linalg.norm(g, axis=1, keepdims=True)
g_world = np.vstack([np.zeros((2, 3)), g, g])
bvals = np.r_[0, 0, np.full(30, 1000.0), np.full(30, 2000.0)]
fiber = np.array([1.0, 0.3, -0.2]); fiber /= np.linalg.norm(fiber)
D = 1.7e-3 * np.outer(fiber, fiber) + 0.3e-3 * (np.eye(3) - np.outer(fiber, fiber))
S = simulate_tensor_signal(D, g_world, bvals)
for sign in (+1, -1):
    A = np.eye(4); A[:3, :3] = rot(0.3, -0.2, 0.5) @ np.diag([2.0 * sign, 2.0, 2.5])
    assert np.sign(np.linalg.det(A[:3, :3])) == sign
    bvec = fsl_from_world(g_world, A)
    assert np.allclose(world_from_fsl(bvec, A), g_world)
    _, ev, v1 = fit_tensor_lls(S, bvals, array_from_fsl(bvec, A))
    v1w = world_from_array(v1[None], A)[0]
    assert abs(abs(v1w @ fiber) - 1) < 1e-8, (sign, v1w)
    _, _, v_wrong = fit_tensor_lls(S, bvals, bvec)
    wrong = abs(world_from_array(v_wrong[None], A)[0] @ fiber)
    if sign > 0:
        assert wrong < 0.99, wrong
    print('det %+d: FSL round trip ok; eigenvector in world frame matches the phantom; using FSL bvecs as array frame gives |cos| %.3f' % (sign, wrong))
print('all gradient-frame tests passed')


# B5: vendor vectors in LPS with b encoded in the squared norm
vec = np.array([[0, 0, 0], [0.6, 0, 0.8], [0, -0.5 ** 0.5, 0]])
b, u = bvals_bvecs_from_vectors(vec, 2000.0)
assert np.allclose(b, [0, 2000, 1000]) and np.allclose(np.linalg.norm(u[1:], axis=1), 1) and np.allclose(u[0], 0)
assert np.allclose(world_from_lps([1.0, 2.0, 3.0]), [-1.0, -2.0, 3.0])
print("vendor vectors: b from the squared norm, LPS -> RAS world")
