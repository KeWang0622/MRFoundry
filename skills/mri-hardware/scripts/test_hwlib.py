"""Analytic checks for mrfoundry_hwlib (python test_hwlib.py)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrfoundry_hwlib import *

R = 0.1
z = np.linspace(-0.2, 0.2, 21)
pts = np.stack([np.zeros_like(z), np.zeros_like(z), z], -1)
b = biot_savart(pts, circle_path(R, 720), current=2.0)
ref = loop_bz_on_axis(R, z, current=2.0)
assert np.max(np.abs(b[:, 2] - ref) / ref) < 1e-4 and np.max(np.abs(b[:, :2])) < 1e-12 * ref.max() + 1e-15
print("loop on-axis Bz matches analytic (max rel err %.1e)" % np.max(np.abs(b[:, 2] - ref) / ref))

d = 0.01
wire = np.array([[0, 0, -100.0], [0, 0, 100.0]])
bw = biot_savart([[d, 0, 0]], wire, current=3.0, closed=False)[0]
assert abs(bw[1] - MU0 * 3.0 / (2 * np.pi * d)) / bw[1] < 1e-6 and abs(bw[0]) < 1e-15
print("long straight wire: B = mu0 I / (2 pi d), direction +y for +z current")

N = 25
bh = (biot_savart(pts, circle_path(R, 720, z=-R / 2), N) + biot_savart(pts, circle_path(R, 720, z=R / 2), N))[:, 2]
b_center = (4 / 5) ** 1.5 * MU0 * N / R
assert abs(bh[10] - b_center) / b_center < 1e-4
inner = np.abs(z) <= 0.02 * 1.0001
assert np.max(np.abs(bh[inner] - bh[10]) / bh[10]) < 2e-3
print("Helmholtz pair: centre field (4/5)^1.5 mu0 N I / R; uniform within 0.2% over +/-0.2R")

sep = np.sqrt(3) * R
xs = np.linspace(-0.01, 0.01, 11)
gp = np.stack([np.zeros_like(xs), np.zeros_like(xs), xs], -1)
bm = (biot_savart(gp, circle_path(R, 720, z=sep / 2), 1.0) - biot_savart(gp, circle_path(R, 720, z=-sep / 2), 1.0))[:, 2]
h = sep / 2
g_an = 3 * MU0 * R ** 2 * h / (R ** 2 + h ** 2) ** 2.5
met = gradient_metrics(gp, bm, axis=2)
assert abs(met["efficiency_T_per_m_per_A"] - g_an) / g_an < 2e-3, (met, g_an)
print("Maxwell pair gradient efficiency %.4f mT/m/A matches analytic; max dev/(G r) %.1e" % (met["efficiency_mT_per_m_per_A"], met["max_dev_over_G_rmax"]))
lin = gradient_metrics(gp, 0.01 * xs + 1e-3, axis=2)
assert abs(lin["G_T_per_m"] - 0.01) < 1e-12 and lin["max_abs_dev_T"] < 1e-15

L, n_loops = 0.5, 400
zs = np.linspace(-L / 2, L / 2, n_loops)
paths = [circle_path(0.05, 240, z=zz) for zz in zs]
bs = sum(biot_savart([[0, 0, 0]], p, 1.0)[0, 2] for p in paths)
ref = finite_solenoid_bz_center(n_loops / L, 1.0, L, 0.05)
assert abs(bs - ref) / ref < 5e-3, (bs, ref)
print("finite solenoid centre field matches mu0 n I L/2 / sqrt((L/2)^2 + R^2) (rel err %.1e)" % (abs(bs - ref) / ref))

g = np.linspace(-0.1, 0.1, 21)
X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
H = solid_harmonics(X, Y, Z, order=3)
hstep = g[1] - g[0]
for k, v in H.items():
    lap = sum(np.diff(v, 2, axis=a)[tuple(slice(1, -1) if b != a else slice(None) for b in range(3))] for a in range(3)) / hstep ** 2
    assert np.max(np.abs(lap)) < 1e-8, k
rng = np.random.default_rng(1)
true = {k: rng.normal() for k in solid_harmonics(0, 0, 0, 2)}
field = sum(c * solid_harmonics(X, Y, Z, 2, r0=0.1)[k] for k, c in true.items())
fit = fit_harmonics(field, X, Y, Z, order=2, r0=0.1)
assert all(abs(fit["coefficients"][k] - true[k]) < 1e-9 for k in true)
print("solid harmonics are harmonic (order <= 3) and fits recover coefficients")

ball = X ** 2 + Y ** 2 + Z ** 2 <= 0.08 ** 2
basis = solid_harmonics(X, Y, Z, order=2, r0=0.1)
maps = [basis[k] * 50.0 for k in ["X", "Y", "Z", "Z2", "ZX", "ZY", "X2-Y2", "XY"]]  # Hz per A at r0
c_true = rng.uniform(-1, 1, len(maps))
dist = -sum(c * m for c, m in zip(c_true, maps)) + 30.0
sol = shim_currents(dist, ball, maps, lower=-2, upper=2)
assert np.allclose(sol["currents"], c_true, atol=1e-8) and sol["std_after"] < 1e-8 and abs(sol["offset"] + 30.0) < 1e-8
tight = shim_currents(dist, ball, maps, lower=-0.3, upper=0.3)
assert np.all(np.abs(tight["currents"]) <= 0.3 + 1e-9) and tight["std_after"] > 0
tot = shim_currents(dist, ball, maps, lower=-2, upper=2, total_abs_limit=1.5)
assert tot["sum_abs_current"] <= 1.5 + 1e-6 and tot["std_after"] >= sol["std_after"] and tot["std_after"] < tot["std_before"]
print("shim currents: exact recovery within bounds; per-channel and total limits respected")

dt, A = 1e-5, 5e-6
train = np.zeros(10000)
for k0 in range(0, 10000, 1000):
    train[k0:k0 + 100] = A
assert abs(b1_rms(train, dt) - A * np.sqrt(0.1)) < 1e-12
assert abs(b1_rms_of_train([A ** 2 * 100 * dt], 1000 * dt) - A * np.sqrt(0.1)) < 1e-12
assert b1_rms(train, dt, window_s=0.005) >= b1_rms(train, dt)
assert abs(np.deg2rad(90) - 2 * np.pi * GAMMA_BAR_1H * b1_for_flip(90, 1e-3) * 1e-3) < 1e-12
print("B1rms of a rectangular train = A sqrt(duty); flip-angle B1 consistent")

lim = iec_sar_limits("normal", 0.0)
assert lim["whole_body"] == 2.0 and lim["partial_body"] == 10.0 and iec_sar_limits("normal", 1.0)["partial_body"] == 2.0
assert iec_sar_limits("first", 1.0)["partial_body"] == 4.0 and lim["head"] == 3.2
assert abs(time_averaged_sar(np.r_[np.full(360, 4.0), np.zeros(360)], 1.0) - 4.0) < 1e-12
assert abs(sar_scale(1.0, 2.0, 2.0) - 16.0) < 1e-12
print("IEC SAR limits and time averaging")

gr = np.r_[np.linspace(0, 0.04, 201), np.full(300, 0.04), np.linspace(0.04, 0, 201)]
ts, pk = effective_stimulus_duration(gr, 1e-6)
assert np.allclose(ts, 200e-6) and np.allclose(pk, 200.0)
assert abs(pns_threshold_dbdt(0.36e-3) - 40.0) < 1e-12 and abs(iec_dbdt_limit(0.36e-3) - 32.0) < 1e-12
assert abs(dbdt_at_radius(200.0, 0.2) - 40.0) < 1e-12
print("PNS: ts_eff of a linear ramp equals the ramp time; hyperbolic threshold and IEC fractions")

C, Ns = 4, 200000
Lc = rng.normal(size=(C, C)) + 1j * rng.normal(size=(C, C))
psi_true = Lc @ Lc.conj().T / C + np.eye(C)
noise = np.linalg.cholesky(psi_true) @ ((rng.normal(size=(C, Ns)) + 1j * rng.normal(size=(C, Ns))) / np.sqrt(2))
psi = noise_covariance(noise)
W = prewhitening_matrix(psi)
assert np.allclose(noise_covariance(W @ noise), np.eye(C), atol=1e-10)
sens = rng.normal(size=(C, 50)) + 1j * rng.normal(size=(C, 50))
comb = roemer_combine(noise.reshape(C, 4000, 50), np.repeat(sens[:, None, :], 4000, 1), psi)
assert abs(np.var(comb) - 1.0) < 0.02
print("noise covariance, prewhitening and Roemer combination in SNR units (noise variance %.3f)" % np.var(comb))
assert abs(snr_scale(10.0, b0_ratio=2.0, time_ratio=4.0) - 40.0) < 1e-12
print("core hardware helper tests passed")



# ---- B5: absolute currents with acquisition currents, KKT optimality check, world coordinates, field map
I_acq = np.array([0.4, -0.2, 0.1, 0.0, 0.3, -0.1, 0.2, 0.05])[:len(maps)]
lim = 0.8
I_true = np.clip(c_true, -lim, lim)
measured = dist + np.tensordot(I_acq, np.array(maps), axes=(0, 0))          # field map acquired with I_acq switched on
sa = shim_currents(measured, ball, maps, lower=-lim, upper=lim, current_during_acquisition=I_acq)
sb = shim_currents(dist, ball, maps, lower=-lim, upper=lim)
assert np.allclose(sa["absolute_currents"], sb["currents"], atol=1e-8) and abs(sa["frequency_adjust"] + sb["offset"]) < 1e-8
assert sa["kkt"]["ok"] and abs(sa["std_before"] - np.std(measured[ball])) < 1e-9
print("shim with acquisition currents: absolute currents and centre-frequency change match the zero-current problem; KKT ok")
# a classic hand-written bug: scale columns for conditioning and forget to unscale the solution
from scipy.optimize import lsq_linear
Ab = np.stack([m_[ball] for m_ in maps], 1); bb = -dist[ball]
sc = np.linalg.norm(Ab, axis=0)
x_bug = lsq_linear(Ab * sc, bb, bounds=(-lim, lim)).x                 # bounds and solution in scaled units
assert not bounded_lsq_kkt(Ab, bb, x_bug, -lim, lim)["ok"]
x_fix = lsq_linear(Ab, bb, bounds=(-lim, lim), method="bvls").x
assert bounded_lsq_kkt(Ab, bb, x_fix, -lim, lim)["ok"]
print("bounded_lsq_kkt flags an unscaled column-scaled solution and accepts the true constrained optimum")

aff = np.array([[1.8, 0.3, 0.0, -50.0], [-0.2, 1.9, 0.4, 20.0], [0.1, -0.3, 2.5, -10.0], [0, 0, 0, 1]])
X, Y, Z = voxel_world_coords(aff, (4, 5, 6))
assert np.allclose([X[1, 2, 3], Y[1, 2, 3], Z[1, 2, 3]], (aff @ [1, 2, 3, 1])[:3] * 1e-3)
print("voxel_world_coords applies the full affine (oblique, off-centre) and converts mm to m")

te_m = np.array([0.0021, 0.0034, 0.0057, 0.0081])
f_true = rng.uniform(-300, 300, size=500); phi0 = rng.uniform(-np.pi, np.pi, size=500)
ph = np.angle(np.exp(1j * (phi0[:, None] + 2 * np.pi * f_true[:, None] * te_m[None])))
ph = ph + 0.01 * rng.normal(size=ph.shape)
fm = fieldmap_multiecho(ph, te_m)
assert np.max(np.abs(fm - f_true)) < 3.0
print(f"fieldmap_multiecho: wrapped phase with nonzero phi0 and uneven TEs, max error {np.max(np.abs(fm - f_true)):.2f} Hz")
print("all B5 hardware helper tests passed")

