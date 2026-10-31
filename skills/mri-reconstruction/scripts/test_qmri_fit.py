"""Tests for qmri_fit (python test_qmri_fit.py, a few seconds)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qmri_fit import *

def main():
    rng = np.random.default_rng(0)
    te = np.array([5, 10, 15, 20]) * 1e-3; T2 = rng.uniform(0.01, 0.08, (8, 8)); S0 = rng.uniform(0.5, 2, (8, 8))
    s0, t2 = fit_monoexp(te, S0[..., None] * np.exp(-te / T2[..., None]))
    assert np.allclose(t2, T2, rtol=1e-6) and np.allclose(s0, S0, rtol=1e-6); print('monoexp ok')
    ti = np.array([0.05, 0.15, 0.4, 0.8, 1.6, 3.0]); T1 = rng.uniform(0.3, 2.0, (8, 8)); a = 1.0; b = -1.7   # imperfect inversion
    sig = a + b * np.exp(-ti / T1[..., None])
    t1, aa, bb = fit_inversion_recovery(ti, np.abs(sig)); assert np.allclose(t1, T1, rtol=6e-3), np.max(abs(t1 / T1 - 1)); print('IR magnitude (polarity restored) ok, max rel err %.2e' % np.max(abs(t1 / T1 - 1)))
    t1c, _, _ = fit_inversion_recovery(ti, sig * np.exp(1j * 0.7)); assert np.allclose(t1c, T1, rtol=6e-3); print('IR complex ok')
    naive = -ti / np.log(np.clip((1 - np.abs(sig) / a) / 2, 1e-9, None))   # wrong 2-parameter inversion of |1-2exp| for comparison only
    flips = np.array([3, 8, 15, 25]); tr = 0.015; m0 = 2.0
    t1v, m0v = fit_vfa(flips, tr, ernst_signal(flips, tr, T1[..., None], m0=m0)); assert np.allclose(t1v, T1, rtol=1e-6) and np.allclose(m0v, m0); print('VFA ok')
    on = bssfp_signal(40, 5e-3, 1.0, 0.1, te=0.0); e1, e2 = np.exp(-5e-3 / 1.0), np.exp(-5e-3 / 0.1); a = np.deg2rad(40)
    ref = np.sin(a) * (1 - e1) / (1 - (e1 - e2) * np.cos(a) - e1 * e2); assert abs(abs(on) - ref) < 1e-9, (abs(on), ref); print('bSSFP fixed point matches on-resonance closed form')
    assert abs(abs(bssfp_signal(40, 5e-3, 1.0, 0.1, off_resonance_hz=100.0, te=0)) - ref) > 1e-3; print('bSSFP off-resonance changes the signal (banding) ok')
    grid = np.geomspace(0.1, 3, 400); D = np.array([ir_signal(ti, t, recovery=2.0) for t in grid])
    truth = ir_signal(ti, 0.9, recovery=2.0) * 3.0; p, sc, co = fit_dictionary(truth[None], D, grid[:, None])
    assert abs(p[0, 0] - 0.9) / 0.9 < 0.01 and abs(sc[0] - 3) < 0.05 and co[0] > 0.9999; print('dictionary fit ok')
    print('all qmri_fit tests passed')


def test_extras():
    e = epg_cpmg(10, 0.01, 0.08, refocus_deg=180.0)
    assert np.allclose(e, np.exp(-np.arange(1, 11) * 0.01 / 0.08), rtol=1e-10); print('EPG with 180 deg refocusing = exp(-n ESP / T2)')
    e = epg_cpmg(10, 0.01, 0.08, refocus_deg=120.0)
    assert abs(e[0] - np.sin(np.deg2rad(60)) ** 2 * np.exp(-0.01 / 0.08)) < 1e-10 and e[1] > e[0]; print('EPG first echo sin^2(a/2) E2, stimulated echo raises echo 2')
    D, P = epg_t2_dictionary(12, 0.01, np.geomspace(0.02, 0.3, 120), np.linspace(0.5, 1.0, 26))
    sig = 2.5 * epg_cpmg(12, 0.01, 0.065, refocus_deg=180 * 0.83, excite_deg=90 * 0.83)
    p, sc, co = fit_dictionary(sig[None], D, P)
    assert abs(p[0, 0] / 0.065 - 1) < 0.03 and abs(p[0, 1] - 0.83) < 0.025; print('EPG dictionary recovers T2 %.4f and B1 %.2f' % tuple(p[0]))
    cbf = asl_cbf_pcasl(0.01, 1.0, pld=1.8, label_duration=1.8)
    ref = 6000 * 0.9 * 0.01 * np.exp(1.8 / 1.65) / (2 * 0.85 * 1.65 * (1 - np.exp(-1.8 / 1.65)))
    assert abs(cbf - ref) < 1e-9; print('ASL PCASL consensus CBF %.1f ml/100g/min for dM/M0 = 1%%' % cbf)
    t = np.arange(0, 6, 2 / 60)  # minutes
    cp = 5.0 * (t / 0.3) * np.exp(1 - t / 0.3) + 0.8 * (1 - np.exp(-t / 0.5)) * np.exp(-t / 10)
    ct = tofts_concentration(t, cp, 0.25, 0.3, 0.05)
    k, v, vp = fit_tofts_linear(t, ct[None], cp)
    assert abs(k[0] / 0.25 - 1) < 0.03 and abs(v[0] / 0.3 - 1) < 0.03 and abs(vp[0] - 0.05) < 0.005; print('extended Tofts linear fit: Ktrans %.3f ve %.3f vp %.3f' % (k[0], v[0], vp[0]))

if __name__ == '__main__':
    main()
    test_extras()
    print('all extra quantitative model tests passed')



# ---- B5 additions -------------------------------------------------------------------------------------------
rng = np.random.default_rng(5)

# DCE: exact piecewise-linear convolution vs fine-grid quadrature on NON-uniform frames
t = np.sort(np.r_[0.0, rng.uniform(0, 300, 70), 300.0]); t = np.unique(np.round(t, 3))
cp = 6.0 * (t / 30) * np.exp(1 - t / 30) * (t > 0) + 0.8 * (1 - np.exp(-t / 120))
def ref_conv(t, x, k, up=400):
    out = np.zeros_like(t)
    for n in range(1, len(t)):
        u = np.linspace(t[0], t[n], up * n + 1); xu = np.interp(u, t, x)
        out[n] = np.trapezoid(xu * np.exp(-k * (t[n] - u)), u)
    return out
for k in (1e-6, 0.002, 0.05, 0.5):
    assert np.allclose(conv_exp_pwlinear(t, cp, k), ref_conv(t, cp, k), rtol=2e-4, atol=2e-6)
print("conv_exp_pwlinear matches fine-grid quadrature on non-uniform frames (k from 1e-6 to 0.5 /s)")

# DCE: recover extended-Tofts parameters from curves simulated by quadrature (independent of the fitter)
truth = [(0.25 / 60, 0.30, 0.05), (0.08 / 60, 0.15, 0.02), (0.6 / 60, 0.45, 0.10)]
ct = np.array([kt * ref_conv(t, cp, kt / ve) + vp * cp for kt, ve, vp in truth])
res = fit_tofts(t, ct, cp)
for i, (kt, ve, vp) in enumerate(truth):
    assert abs(res['ktrans'][i] / kt - 1) < 0.01 and abs(res['ve'][i] / ve - 1) < 0.01 and abs(res['vp'][i] - vp) < 0.002, (res, truth)
print("fit_tofts recovers Ktrans, ve and vp within 1% from independently simulated, non-uniformly sampled curves")

# DCE: SPGR signal -> concentration inversion
t10 = np.array([1.4, 0.9]); tr, fa, r1 = 0.004, 15.0, 4.5
conc = np.array([[0, 0, 0.5, 1.2, 0.8], [0, 0, 0.1, 0.3, 0.2]])
r1t = 1 / t10[:, None] + r1 * conc; e1 = np.exp(-tr * r1t); a = np.deg2rad(fa)
sig = 1234.0 * np.sin(a) * (1 - e1) / (1 - np.cos(a) * e1)
c_est, m0_est = spgr_concentration(sig, t10, tr, fa, r1, n_baseline=2)
assert np.allclose(c_est, conc, atol=1e-9) and np.allclose(m0_est, 1234.0)
print("spgr_concentration inverts the SPGR equation exactly with M0 from the baseline frames")

# ASL: GKM reduces to the consensus single-delay formula when PLD >= ATT; timing-convention trap
pld = np.array([0.6, 1.1, 1.6, 2.1, 2.6]); tau = 1.8
dm = asl_gkm_pcasl(2.0, 1.2, tau, cbf=55.0, m0=900.0)
assert abs(asl_cbf_pcasl(dm, 900.0, pld=2.0, label_duration=tau) - 55.0) < 1e-9
print("asl_gkm_pcasl equals the white-paper single-delay model for PLD >= ATT")
cbf_t = rng.uniform(20, 90, 400); att_t = rng.uniform(0.7, 2.0, 400); m0v = rng.uniform(800, 1200, 400)
slice_off = rng.choice([0.0, 0.1, 0.25, 0.4], 400)
P = pld[None, :] + slice_off[:, None]
Y = asl_gkm_pcasl(P, att_t[:, None], tau, cbf_t[:, None], m0v[:, None])
cbf_e, att_e = fit_asl_multidelay(Y, m0v, P, tau)
ident = att_t > P[:, 0]                                   # ATT longer than the shortest effective delay
assert np.max(np.abs(cbf_e / cbf_t - 1)) < 0.01 and np.max(np.abs(att_e - att_t)[ident]) < 0.006
assert np.all(att_e[~ident] >= att_t[~ident] - 1e-9) and np.all(att_e[~ident] <= P[~ident, 0] + 0.006)
print("fit_asl_multidelay recovers CBF and ATT with per-voxel effective delays (PLD + slice timing);"
      " ATT below the shortest delay is reported as its upper bound, CBF stays exact")
# the frequent error: treating PLD as the time since the START of labelling (drops tau) shifts ATT and CBF
Yw = asl_gkm_pcasl(P - tau, att_t[:, None] - tau, tau, cbf_t[:, None], m0v[:, None])
assert np.allclose(Yw * np.exp(-tau / 1.65), Y)
print(f"  (a model that uses PLD as time since label start matches these curves only with ATT shifted by -{tau} s and CBF scaled by exp(-tau/T1b))")

# ASL: volume grouping by delay is independent of volume order
vols = np.zeros((2, 8)); ty = ['control', 'label'] * 4; dl = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 1.0, 1.0]
vols[:, [0, 4]] = 10; vols[:, [1, 5]] = 9; vols[:, [2, 6]] = 10; vols[:, [3, 7]] = 9.5
perm = rng.permutation(8)
u1, d1 = asl_pairs_by_delay(vols, ty, dl); u2, d2 = asl_pairs_by_delay(vols[:, perm], np.array(ty)[perm], np.array(dl)[perm])
assert np.allclose(u1, [0.5, 1.0]) and np.allclose(d1, [[1.0, 0.5]] * 2) and np.allclose(d2, d1)
assert abs(m0_finite_tr(1.0, 2.5, 1.3) - 1 / (1 - np.exp(-2.5 / 1.3))) < 1e-12
print("asl_pairs_by_delay is order independent; m0_finite_tr applies the saturation-recovery correction")

# Rician-aware dictionary matching at low SNR (EPG T2 with imperfect refocusing)
esp, ne = 0.01, 16
D, Pp = epg_t2_dictionary(ne, esp, np.geomspace(0.02, 0.3, 120), np.linspace(0.45, 1.0, 56))
t2_true, b1_true, sigma = 0.07, 0.55, 0.04
clean = epg_cpmg(ne, esp, t2_true, refocus_deg=180 * b1_true, excite_deg=90 * b1_true)
noisy = np.abs(clean[None] + sigma * (rng.normal(size=(400, ne)) + 1j * rng.normal(size=(400, ne))))
p_plain, _, _ = fit_dictionary(noisy, D, Pp)
p_rice, _, _ = fit_dictionary(noisy, D, Pp, noise_sigma=sigma)
b_plain = np.median(p_plain[:, 0]) / t2_true - 1; b_rice = np.median(p_rice[:, 0]) / t2_true - 1
assert abs(b_rice) < abs(b_plain) and abs(b_rice) < 0.05, (b_plain, b_rice)
print(f"fit_dictionary(noise_sigma=...) removes most of the noise-floor T2 bias at low SNR: {b_plain:+.1%} -> {b_rice:+.1%}")
print("all B5 quantitative model tests passed")

