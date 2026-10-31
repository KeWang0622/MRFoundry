"""MRFoundry single-voxel MRS helpers (numpy/scipy; tested in test_mrs_lib.py).

Chain: align transients (spectral_registration) -> average -> lcm_fit with the supplied basis (frequency shift,
zero-order phase, Lorentzian and Gaussian broadening, nonnegative amplitudes, smooth baseline) -> water amplitude
(water_amplitude) -> water_referenced_concentration (tissue water content, relaxation and partial volume;
Gasparovic et al. 2006, Near et al. 2021 consensus). Before fitting, put both acquisitions in the SAME physical
units: divide each by its stored scale factor and by the number of transients if they were summed.
Frequency convention used here: a resonance at delta ppm evolves as exp(+2 pi i (delta - carrier) f0 1e-6 t) and
spectrum(fid) places it at +delta on ppm_axis. If your data use the opposite sign, pass np.conj(fid).
"""
import numpy as np


def ppm_axis(n, dwell_s, f0_hz, carrier_ppm):
    """ppm of each point of spectrum(fid) (fftshifted, increasing frequency)."""
    return carrier_ppm + np.fft.fftshift(np.fft.fftfreq(n, dwell_s)) / (f0_hz * 1e-6)


def spectrum(fid):
    """Spectrum with the first point halved (avoids a baseline offset), fftshifted."""
    f = np.array(fid, dtype=complex, copy=True); f[..., 0] *= 0.5
    return np.fft.fftshift(np.fft.fft(f, axis=-1), axes=-1)


def spectral_registration(fids, dwell_s, t_max=0.2, reference=None):
    """Frequency and phase alignment of transients [n_transients, n_points] to a reference (default: the
    median-phased mean), by least squares on the FID up to t_max (Near et al., MRM 2015). Returns
    (aligned fids, frequency shifts in Hz, phase shifts in rad) such that aligned = fid * exp(-i(2 pi df t + phi))."""
    from scipy.optimize import least_squares
    F = np.asarray(fids, complex); n = F.shape[-1]; t = np.arange(n) * dwell_s; k = t <= t_max
    ref = F.mean(0) if reference is None else np.asarray(reference, complex)
    dfs, phs, out = [], [], []
    for x in F:
        def res(p):
            d = x[k] * np.exp(-1j * (2 * np.pi * p[0] * t[k] + p[1])) - ref[k]
            return np.r_[d.real, d.imag]
        p0 = [0.0, np.angle(np.vdot(ref[k], x[k]))]
        p = least_squares(res, p0, x_scale=[1.0, 0.1]).x
        dfs.append(p[0]); phs.append(p[1]); out.append(x * np.exp(-1j * (2 * np.pi * p[0] * t + p[1])))
    return np.array(out), np.array(dfs), np.array(phs)


def water_amplitude(fid, dwell_s, t_window=(0.002, 0.15)):
    """Time-zero amplitude of an (averaged) unsuppressed water FID: fit log|s(t)| = log A - a t - b t^2 over
    t_window (Voigt decay), extrapolated to t = 0. Use the same units as the metabolite data."""
    s = np.abs(np.asarray(fid, complex)); t = np.arange(len(s)) * dwell_s
    k = (t >= t_window[0]) & (t <= t_window[1]) & (s > 0)
    A = np.stack([np.ones(k.sum()), -t[k], -t[k] ** 2], 1)
    c = np.linalg.lstsq(A, np.log(s[k]), rcond=None)[0]
    return float(np.exp(c[0]))


def relaxation_attenuation(tr, te, t1, t2):
    """Signal fraction left after relaxation: (1 - exp(-TR/T1)) exp(-TE/T2)."""
    return (1 - np.exp(-np.asarray(tr, float) / np.asarray(t1, float))) * np.exp(-np.asarray(te, float) / np.asarray(t2, float))


def water_referenced_concentration(metab_amplitude, water_amp, metab_attenuation, fractions, water_contents_mM,
                                   water_attenuations, water_protons=2, metabolite_compartments=('gm', 'wm')):
    """Water-referenced concentration (Gasparovic et al., MRM 2006).

    metab_amplitude: fitted multiple of a basis spectrum that represents 1 mmol/L of the metabolite (all its
    protons) with the same signal per proton as the water reference; water_amp: time-zero water amplitude in the
    same units (water_amplitude). fractions, water_contents_mM, water_attenuations: dicts keyed by compartment
    ('gm', 'wm', 'csf'); attenuation = relaxation_attenuation(TR, TE, T1, T2) of that acquisition.
    Water signal = water_protons * sum_c f_c W_c R_c (per proton units), so one unit of signal per proton equals
    water_amp / (water_protons * sum_c f_c W_c R_c). Returns concentration in mmol/L of the metabolite-containing
    tissue (moles in the voxel divided by the volume of the compartments in metabolite_compartments)."""
    denom = water_protons * sum(fractions[c] * water_contents_mM[c] * water_attenuations[c] for c in fractions)
    unit = water_amp / denom                                     # signal per proton per mmol/L of voxel volume
    c_voxel = np.asarray(metab_amplitude, float) / (metab_attenuation * unit)   # mmol per litre of voxel
    tissue = sum(fractions[c] for c in metabolite_compartments)
    return c_voxel / tissue


def lcm_fit(fid, basis, dwell_s, f0_hz, carrier_ppm, ppm_range=(0.2, 4.2), baseline_knots=None, free_sign=(),
            max_shift_hz=15.0, n_starts=8):
    """Linear-combination fit of a metabolite FID with basis FIDs (dict name -> FID, same dwell and length).

    Model (frequency domain, inside ppm_range): exp(i phi0) * sum_m c_m FT[B_m(t) exp(-(a + i 2 pi df) t - b t^2)]
    + smooth complex baseline (cubic B-splines, default one knot per 0.5 ppm). c_m >= 0 except names in free_sign
    (e.g. a nuisance macromolecule component scaled arbitrarily may still be constrained >= 0). Nonlinear
    parameters (df Hz, phi0 rad, a >= 0 1/s, b >= 0 1/s^2) by Nelder-Mead from several phase starts; linear ones by
    bounded least squares. Returns dict(amplitudes, df_hz, phase_rad, lorentz_1_s, gauss_1_s2, fit, baseline,
    residual, ppm, data, residual_sd, crlb_like) restricted to ppm_range. Check the fit and residual figure."""
    from scipy.optimize import lsq_linear, minimize
    names = list(basis); n = len(fid); t = np.arange(n) * dwell_s
    ppm = ppm_axis(n, dwell_s, f0_hz, carrier_ppm); sel = (ppm >= ppm_range[0]) & (ppm <= ppm_range[1])
    y = spectrum(fid)[sel]; B = np.array([np.asarray(basis[k], complex) for k in names])
    x = ppm[sel]
    if baseline_knots is None:
        baseline_knots = max(4, int(round((ppm_range[1] - ppm_range[0]) / 0.5)))
    edges = np.linspace(x.min(), x.max(), baseline_knots)
    h = edges[1] - edges[0]
    def bspline(u):                                              # cubic B-spline basis on uniform knots
        cols = []
        for c in np.r_[edges[0] - h, edges, edges[-1] + h]:
            z = np.abs((u - c) / h)
            cols.append(np.where(z < 1, 2 / 3 - z ** 2 + z ** 3 / 2, np.where(z < 2, (2 - z) ** 3 / 6, 0.0)))
        return np.stack(cols, 1)
    S = bspline(x)
    lo = np.array([-np.inf if k in free_sign else 0.0 for k in names] + [-np.inf] * (2 * S.shape[1]))
    hi = np.full(len(lo), np.inf)
    def design(p):
        df, ph, a, b = p[0], p[1], abs(p[2]), abs(p[3])
        mod = np.exp(-(a + 2j * np.pi * df) * t - b * t ** 2) * np.exp(1j * ph)
        M = spectrum(B * mod[None])[:, sel].T                  # [n_points, n_basis]
        return M
    def solve(p):
        M = design(p)
        A = np.hstack([M, S.astype(complex), 1j * S])
        Ar = np.vstack([A.real, A.imag]); yr = np.r_[y.real, y.imag]
        sol = lsq_linear(Ar, yr, bounds=(lo, hi), method='bvls' if Ar.shape[1] < 60 else 'trf')
        return sol.x, Ar, yr
    def cost(p):
        xx, Ar, yr = solve(p); r = Ar @ xx - yr; return float(r @ r)
    best = None
    for ph0 in np.linspace(-np.pi, np.pi, n_starts, endpoint=False):
        for df0 in (-max_shift_hz / 3, 0.0, max_shift_hz / 3):
            p0 = np.array([df0, ph0, 2.0, 10.0])
            c0 = cost(p0)
            if best is None or c0 < best[0]:
                best = (c0, p0)
    r = minimize(cost, best[1], method='Nelder-Mead', options=dict(maxiter=600, xatol=1e-4, fatol=1e-10))
    p = r.x; xx, Ar, yr = solve(p)
    M = design(p); nb = len(names)
    fitc = M @ xx[:nb]; base = S @ xx[nb:nb + S.shape[1]] + 1j * (S @ xx[nb + S.shape[1]:])
    resid = y - fitc - base
    sd = float(np.std(np.r_[resid.real, resid.imag]))
    J = np.vstack([M.real, M.imag])                             # crude amplitude SDs (fixed nonlinear parameters)
    try:
        cov = np.linalg.inv(J.T @ J) * sd ** 2; crlb = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        crlb = np.full(nb, np.nan)
    return dict(amplitudes=dict(zip(names, xx[:nb].tolist())), df_hz=float(p[0]), phase_rad=float(p[1]),
                lorentz_1_s=float(abs(p[2])), gauss_1_s2=float(abs(p[3])), fit=fitc, baseline=base, residual=resid,
                ppm=x, data=y, residual_sd=sd, crlb_like=dict(zip(names, crlb.tolist())))


def _print_api(namespace):
    """Signatures and one-line summaries of the public functions (python <module>.py --api)."""
    import inspect
    for name, f in sorted(namespace.items()):
        if inspect.isfunction(f) and not name.startswith('_') and f.__module__ == '__main__':
            doc = ((inspect.getdoc(f) or '').splitlines() or [''])[0]
            print(f"{name}{inspect.signature(f)}" + chr(10) + f"    {doc}")


if __name__ == '__main__' and '--api' in __import__('sys').argv:
    _print_api(dict(globals()))
