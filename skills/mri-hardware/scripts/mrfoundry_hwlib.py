"""MRFoundry hardware and safety helpers. SI units everywhere (m, s, A, T, Hz, W/kg).

Small, dependency-light (numpy, scipy) functions for quantities that MR hardware and
safety engineers compute often. Each function is checked against analytic cases in
test_hwlib.py; run that test after installing numpy and scipy. These helpers support
research calculations; they do not replace vendor safety supervision, validated EM
simulation or a site MR safety programme.
"""
import numpy as np

MU0 = 1.25663706212e-6  # vacuum permeability, T*m/A (CODATA 2018)
GAMMA_BAR_1H = 42.577478518e6  # 1H gyromagnetic ratio / 2pi, Hz/T


# --------------------------------------------------------------------------- fields
def biot_savart(points, path, current=1.0, closed=True, chunk=4096):
    """Magnetic flux density (T) at points (..., 3) from a filamentary polyline.

    path: (M, 3) vertices in metres; closed=True joins the last vertex to the first.
    Uses the exact field of each straight segment, so a curved wire is approximated
    only by its polyline: refine the discretization until the result converges
    (for a circle the relative error falls roughly as 1/n_segments^2).
    """
    pts = np.asarray(points, float)
    shp = pts.shape
    pts = pts.reshape(-1, 3)
    path = np.asarray(path, float)
    if closed:
        path = np.vstack([path, path[:1]])
    a, b = path[:-1], path[1:]
    out = np.zeros_like(pts)
    for s in range(0, len(pts), chunk):
        p = pts[s:s + chunk, None, :]
        r1, r2 = a[None] - p, b[None] - p
        n1, n2 = np.linalg.norm(r1, axis=-1), np.linalg.norm(r2, axis=-1)
        cross = np.cross(r1, r2)
        den = n1 * n2 * (n1 * n2 + np.sum(r1 * r2, axis=-1))
        with np.errstate(divide="ignore", invalid="ignore"):
            f = np.where(den > 1e-30, (n1 + n2) / den, 0.0)
        out[s:s + chunk] = np.sum(cross * f[..., None], axis=1)
    return (MU0 * current / (4 * np.pi) * out).reshape(shp)


def circle_path(radius, n=720, center=(0.0, 0.0, 0.0), z=0.0):
    """Closed circular loop (n vertices, counter-clockwise seen from +z) at height z.

    Positive current then produces +Bz on the loop axis."""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c = np.asarray(center, float)
    return np.stack([c[0] + radius * np.cos(t), c[1] + radius * np.sin(t), np.full(n, c[2] + z)], -1)


def loop_bz_on_axis(radius, z, current=1.0):
    """Analytic on-axis Bz (T) of a circular loop centred at z=0."""
    z = np.asarray(z, float)
    return MU0 * current * radius ** 2 / (2 * (radius ** 2 + z ** 2) ** 1.5)


def finite_solenoid_bz_center(turns_per_m, current, length, radius):
    """Analytic Bz (T) at the centre of a finite thin solenoid."""
    return MU0 * turns_per_m * current * (length / 2) / np.sqrt((length / 2) ** 2 + radius ** 2)


def gradient_metrics(coords, bz, axis=0, roi=None, current=1.0):
    """Linear gradient fit and linearity of a Bz field sampled at coords (..., 3).

    Fits bz = b0 + G * coord[axis] over the ROI (least squares). Returns the gradient
    G (T/m), efficiency G/current (T/m/A and mT/m/A), the offset b0 (T), and the
    deviation from the fitted linear field: maximum and RMS absolute deviation (T),
    the maximum deviation normalized by |G| * r_max (r_max = largest |coord| along the
    axis inside the ROI), and the maximum pointwise relative error |bz-b0-Gx|/|Gx|
    for points with |x| >= 0.1 r_max. State which definition you report: published
    'linearity' figures use different normalizations and ROI shapes.
    """
    c = np.asarray(coords, float).reshape(-1, 3)
    f = np.asarray(bz, float).ravel()
    m = np.ones(len(f), bool) if roi is None else np.asarray(roi, bool).ravel()
    x = c[m, axis]
    A = np.stack([np.ones_like(x), x], 1)
    (b0, g), *_ = np.linalg.lstsq(A, f[m], rcond=None)
    dev = f[m] - (b0 + g * x)
    rmax = np.max(np.abs(x))
    far = np.abs(x) >= 0.1 * rmax
    rel = np.abs(dev[far]) / np.abs(g * x[far]) if np.any(far) and g != 0 else np.array([np.nan])
    return {"G_T_per_m": float(g), "efficiency_T_per_m_per_A": float(g / current),
            "efficiency_mT_per_m_per_A": float(1e3 * g / current), "offset_T": float(b0),
            "max_abs_dev_T": float(np.max(np.abs(dev))), "rms_dev_T": float(np.sqrt(np.mean(dev ** 2))),
            "max_dev_over_G_rmax": float(np.max(np.abs(dev)) / (abs(g) * rmax)) if g else float("nan"),
            "max_pointwise_rel_error": float(np.max(rel)), "r_max_m": float(rmax)}


# ----------------------------------------------------------------- spherical harmonics
HARMONIC_DEFINITIONS = {
    "Z0": "1", "X": "x", "Y": "y", "Z": "z",
    "Z2": "z^2 - (x^2 + y^2)/2", "ZX": "z x", "ZY": "z y", "X2-Y2": "x^2 - y^2", "XY": "x y",
    "Z3": "z^3 - 3 z (x^2 + y^2)/2", "Z2X": "x (4 z^2 - x^2 - y^2)", "Z2Y": "y (4 z^2 - x^2 - y^2)",
    "Z(X2-Y2)": "z (x^2 - y^2)", "ZXY": "x y z", "X3": "x^3 - 3 x y^2", "Y3": "3 x^2 y - y^3",
}
_ORDER = {"Z0": 0, "X": 1, "Y": 1, "Z": 1, "Z2": 2, "ZX": 2, "ZY": 2, "X2-Y2": 2, "XY": 2,
          "Z3": 3, "Z2X": 3, "Z2Y": 3, "Z(X2-Y2)": 3, "ZXY": 3, "X3": 3, "Y3": 3}


def solid_harmonics(x, y, z, order=2, r0=1.0):
    """Real solid harmonics as Cartesian polynomials (unnormalized), divided by r0**l.

    Definitions are in HARMONIC_DEFINITIONS (z = magnet bore axis). With r0 equal to a
    reference radius, a fitted coefficient is the term's field at that radius, in the
    units of the fitted map (Hz or T). Vendor shim channels use their own
    normalizations, signs and sometimes 2xy instead of xy: calibrate each channel's
    measured field map per unit current instead of assuming these polynomials."""
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    p = {"Z0": np.ones_like(x), "X": x, "Y": y, "Z": z,
         "Z2": z ** 2 - (x ** 2 + y ** 2) / 2, "ZX": z * x, "ZY": z * y, "X2-Y2": x ** 2 - y ** 2, "XY": x * y,
         "Z3": z ** 3 - 1.5 * z * (x ** 2 + y ** 2), "Z2X": x * (4 * z ** 2 - x ** 2 - y ** 2),
         "Z2Y": y * (4 * z ** 2 - x ** 2 - y ** 2), "Z(X2-Y2)": z * (x ** 2 - y ** 2), "ZXY": x * y * z,
         "X3": x ** 3 - 3 * x * y ** 2, "Y3": 3 * x ** 2 * y - y ** 3}
    return {k: v / r0 ** _ORDER[k] for k, v in p.items() if _ORDER[k] <= order}


def fit_harmonics(field, x, y, z, mask=None, order=2, r0=1.0):
    """Least-squares solid-harmonic coefficients of a field map over a mask."""
    f = np.asarray(field, float)
    m = np.isfinite(f) if mask is None else (np.asarray(mask, bool) & np.isfinite(f))
    basis = solid_harmonics(x, y, z, order, r0)
    names = list(basis)
    A = np.stack([basis[k][m] for k in names], 1)
    coef, *_ = np.linalg.lstsq(A, f[m], rcond=None)
    resid = f[m] - A @ coef
    return {"coefficients": dict(zip(names, coef.tolist())), "residual_rms": float(np.sqrt(np.mean(resid ** 2))),
            "residual_std": float(np.std(resid)), "n_voxels": int(m.sum())}


# --------------------------------------------------------------------------- shimming
def shim_currents(field, mask, channel_maps, lower=None, upper=None, total_abs_limit=None,
                  free_offset=True, weights=None):
    """Bounded least-squares shim currents.

    field: measured off-resonance map (Hz or T) to cancel; channel_maps: (C, ...) field
    per unit current of each shim channel in the SAME units and sign convention;
    lower/upper: per-channel current bounds; total_abs_limit: optional limit on
    sum(|current|) (e.g. a shared supply); free_offset: also fit a global offset (the
    centre frequency), which costs no current. Minimizes
    || w * (field + sum_i c_i map_i + offset) ||_2 over the mask.
    Returns currents, offset and std/RMS of the field before and after inside the mask.
    """
    from scipy.optimize import lsq_linear, minimize
    m = np.asarray(mask, bool)
    f = np.asarray(field, float)[m]
    A = np.stack([np.asarray(cm, float)[m] for cm in channel_maps], 1)
    C = A.shape[1]
    w = np.ones_like(f) if weights is None else np.asarray(weights, float)[m]
    lo = np.full(C, -np.inf) if lower is None else np.broadcast_to(np.asarray(lower, float), (C,)).copy()
    hi = np.full(C, np.inf) if upper is None else np.broadcast_to(np.asarray(upper, float), (C,)).copy()
    Aw = A * w[:, None]
    yw = -f * w
    if free_offset:
        Aw = np.hstack([Aw, w[:, None]])
        lo, hi = np.append(lo, -np.inf), np.append(hi, np.inf)
    if total_abs_limit is None:
        sol = lsq_linear(Aw, yw, bounds=(lo, hi), method="bvls").x
    else:
        # Reduce to a small, well-scaled problem with a QR factorization, then split the
        # currents into positive and negative parts (c = p - n, p, n >= 0) so that the
        # total-current limit is linear.
        Q, Rm = np.linalg.qr(Aw)
        q = Q.T @ yw
        scale = max(float(q @ q), 1e-30)
        k = C
        def unpack(v):
            c = v[:k] - v[k:2 * k]
            return np.append(c, v[2 * k]) if free_offset else c
        def obj(v):
            r = Rm @ unpack(v) - q
            g = Rm.T @ r / scale
            gc = g[:k]
            grad = np.concatenate([gc, -gc] + ([g[k:]] if free_offset else []))
            return 0.5 * (r @ r) / scale, grad
        bnds = [(0, max(hi[i], 0)) for i in range(k)] + [(0, max(-lo[i], 0)) for i in range(k)]
        if free_offset:
            bnds.append((None, None))
        nvar = 2 * k + (1 if free_offset else 0)
        cons = [{"type": "ineq", "fun": lambda v: total_abs_limit - np.sum(v[:2 * k]),
                 "jac": lambda v: np.concatenate([-np.ones(2 * k), np.zeros(nvar - 2 * k)])}]
        box = lsq_linear(Aw, yw, bounds=(lo, hi), method="bvls").x
        c0 = box[:C] * min(1.0, total_abs_limit / max(np.sum(np.abs(box[:C])), 1e-30))
        x0 = np.concatenate([np.maximum(c0, 0), np.maximum(-c0, 0)] + ([box[C:]] if free_offset else []))
        res = minimize(obj, x0, jac=True, bounds=bnds, constraints=cons, method="SLSQP",
                       options={"maxiter": 2000, "ftol": 1e-15})
        sol = unpack(res.x)
    cur = sol[:C]
    off = float(sol[C]) if free_offset else 0.0
    after = f + A @ cur + off
    return {"currents": cur, "offset": off, "std_before": float(np.std(f)), "std_after": float(np.std(after)),
            "rms_before": float(np.sqrt(np.mean(f ** 2))), "rms_after": float(np.sqrt(np.mean(after ** 2))),
            "at_bound": [bool(np.isclose(c, lo[i]) or np.isclose(c, hi[i])) for i, c in enumerate(cur)],
            "sum_abs_current": float(np.sum(np.abs(cur)))}


# ------------------------------------------------------------------------ RF exposure
def rf_energy(b1, dt):
    """Integral of |B1|^2 dt (T^2 s) for a uniformly sampled RF waveform (T)."""
    return float(np.sum(np.abs(np.asarray(b1)) ** 2) * dt)


def b1_rms(b1, dt, window_s=None):
    """B1 RMS (T) of a uniformly sampled waveform (include the dead time between
    pulses in the waveform, or use b1_rms_of_train). With window_s, return the maximum
    over all sliding windows of that length (e.g. 10 s, as scanners and implant
    labels report B1+rms)."""
    p = np.abs(np.asarray(b1, complex if np.iscomplexobj(b1) else float)) ** 2
    if window_s is None:
        return float(np.sqrt(np.mean(p)))
    n = max(1, int(round(window_s / dt)))
    if n >= len(p):
        return float(np.sqrt(np.mean(p)))
    cs = np.concatenate([[0.0], np.cumsum(p)])
    return float(np.sqrt(np.max(cs[n:] - cs[:-n]) / n))


def b1_rms_of_train(pulse_energies_T2s, period_s):
    """B1 RMS (T) of a periodic train given the |B1|^2 dt energy of each pulse in one period."""
    return float(np.sqrt(np.sum(pulse_energies_T2s) / period_s))


def b1_for_flip(flip_deg, duration_s, shape_integral=1.0, gamma_hz_per_t=GAMMA_BAR_1H):
    """Peak B1 (T) for a flip angle, given the pulse's normalized amplitude integral
    (1 for a rectangular pulse; e.g. ~0.27-0.5 for apodized sincs: compute it from the
    actual shape as mean(shape)/max(shape))."""
    return np.deg2rad(flip_deg) / (2 * np.pi * gamma_hz_per_t * duration_s * shape_integral)


def sar_scale(sar_ref, b1rms_ratio=1.0, b0_ratio=1.0, b0_exponent=2.0):
    """Scale a reference SAR: SAR ~ B1rms^2 * B0^p. p = 2 in the quasi-static regime
    (roughly up to 1.5-3 T); at higher fields the effective exponent is lower and
    field inhomogeneity dominates: use EM simulation there."""
    return sar_ref * b1rms_ratio ** 2 * b0_ratio ** b0_exponent


def iec_sar_limits(mode="normal", exposed_mass_fraction=None):
    """Volume-averaged SAR limits (W/kg) of IEC 60601-2-33 (edition 3.x), 6-minute average.

    mode: 'normal' or 'first'. Partial-body limit = 10 - 8*f (normal) or 10 - 6*f (first
    level), f = exposed patient mass / patient mass. Short-term rule: over any 10 s the
    SAR must not exceed twice the stated limit. Local SAR (10 g): head and trunk 10,
    extremities 20 W/kg. Check the edition and amendments your institution applies;
    whole-body limits also assume the standard's environmental conditions."""
    if mode not in ("normal", "first"):
        raise ValueError("mode must be 'normal' or 'first'")
    d = {"whole_body": 2.0 if mode == "normal" else 4.0, "head": 3.2,
         "local_head_10g": 10.0, "local_trunk_10g": 10.0, "local_extremities_10g": 20.0,
         "averaging_s": 360.0, "short_term_window_s": 10.0, "short_term_factor": 2.0}
    if exposed_mass_fraction is not None:
        f = float(np.clip(exposed_mass_fraction, 0, 1))
        d["partial_body"] = 10.0 - (8.0 if mode == "normal" else 6.0) * f
    return d


def time_averaged_sar(sar_series_w_per_kg, dt, window_s=360.0):
    """Maximum sliding-window average of a SAR time series (W/kg)."""
    s = np.asarray(sar_series_w_per_kg, float)
    n = max(1, int(round(window_s / dt)))
    if n >= len(s):
        return float(np.mean(s))
    cs = np.concatenate([[0.0], np.cumsum(s)])
    return float(np.max(cs[n:] - cs[:-n]) / n)


# ------------------------------------------------------------------ gradients and PNS
def slew_rate(g, dt):
    """Slew rate (T/m/s) of a uniformly sampled gradient waveform (T/m)."""
    return np.diff(np.asarray(g, float)) / dt


def dbdt_at_radius(slew_T_per_m_s, radius_m):
    """|dBz/dt| (T/s) at distance r from isocentre along a linear gradient axis.
    Concomitant (transverse) components and the coil's real field extent are ignored;
    IEC compliance uses the system's own dB/dt or E-field model."""
    return np.abs(slew_T_per_m_s) * radius_m


def effective_stimulus_duration(g, dt):
    """Effective stimulus durations t_s,eff (s) of each monotonic segment of a gradient
    waveform: peak-to-peak change divided by the maximum |dG/dt| within the segment
    (IEC 60601-2-33 definition applied to G; the same ratio holds for dB/dt at a fixed
    position). Returns (durations, max_slews)."""
    g = np.asarray(g, float)
    s = np.diff(g) / dt
    sign = np.sign(s)
    out, peaks, start = [], [], 0
    for i in range(1, len(s) + 1):
        if i == len(s) or (sign[i] != sign[start] and sign[i] != 0):
            seg = s[start:i]
            if np.any(seg != 0):
                pk = np.max(np.abs(seg))
                out.append(abs(np.sum(seg) * dt) / pk)
                peaks.append(pk)
            start = i
    return np.array(out), np.array(peaks)


def pns_threshold_dbdt(ts_eff_s, rheobase_T_per_s=20.0, chronaxie_s=0.36e-3):
    """Hyperbolic strength-duration threshold dB/dt = rb (1 + c / ts_eff) (T/s).

    Defaults are the IEC 60601-2-33 whole-body-gradient values (rb = 20 T/s,
    c = 0.36 ms); the E-field form uses rb = 2.2 V/m. Real PNS thresholds depend on
    the coil and body model: use measured or vendor (e.g. SAFE) models when available."""
    ts = np.asarray(ts_eff_s, float)
    return rheobase_T_per_s * (1 + chronaxie_s / ts)


def iec_dbdt_limit(ts_eff_s, mode="normal", **kw):
    """IEC operating-mode dB/dt limit: 80 % (normal) or 100 % (first level) of the threshold."""
    frac = {"normal": 0.8, "first": 1.0}[mode]
    return frac * pns_threshold_dbdt(ts_eff_s, **kw)


# ------------------------------------------------------------------ noise and SNR
def noise_covariance(noise):
    """Receiver noise covariance Psi (C x C) from noise-only samples (C, N)."""
    n = np.asarray(noise)
    n = n - n.mean(axis=1, keepdims=True)
    return (n @ n.conj().T) / n.shape[1]


def prewhitening_matrix(psi):
    """W with W Psi W^H = I (W = inverse Cholesky factor). Apply as W @ data (C, ...)."""
    L = np.linalg.cholesky(psi)
    return np.linalg.inv(L)


def rss_combine(coil_images, axis=0):
    return np.sqrt(np.sum(np.abs(coil_images) ** 2, axis=axis))


def roemer_combine(coil_images, sens, psi=None):
    """Optimal (Roemer) combination s^H Psi^-1 x / sqrt(s^H Psi^-1 s), coil axis 0.

    With Psi equal to the per-sample noise covariance of the same data, the output is in
    SNR units (Kellman & McVeigh): noise-only data then has unit standard deviation in
    the real and imaginary parts combined as complex noise with variance 1."""
    x = np.asarray(coil_images)
    s = np.asarray(sens)
    C = x.shape[0]
    P = np.eye(C) if psi is None else np.asarray(psi)
    Pi = np.linalg.inv(P)
    xs = x.reshape(C, -1)
    ss = s.reshape(C, -1)
    num = np.einsum("cn,cd,dn->n", ss.conj(), Pi, xs)
    den = np.sqrt(np.real(np.einsum("cn,cd,dn->n", ss.conj(), Pi, ss)))
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(den > 0, num / den, 0)
    return out.reshape(x.shape[1:])


def snr_scale(snr_ref, b0_ratio=1.0, voxel_volume_ratio=1.0, time_ratio=1.0, bandwidth_ratio=1.0,
              b0_exponent=1.0):
    """Scale SNR: SNR ~ B0^p * voxel volume * sqrt(total readout time), with the total
    sampling time ~ averages * phase encodes / bandwidth per pixel. p ~ 1 above ~0.5 T
    where body noise dominates; at very low field, coil noise dominates and p ~ 7/4
    (Hoult & Richards). Coil, relaxation and sequence changes are not included."""
    return snr_ref * b0_ratio ** b0_exponent * voxel_volume_ratio * np.sqrt(time_ratio / bandwidth_ratio)

