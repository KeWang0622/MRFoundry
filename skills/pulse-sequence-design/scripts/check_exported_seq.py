#!/usr/bin/env python3
"""Measure what an exported Pulseq file actually does, independent of the script that built it.

Usage (all expectations optional; SI units, gradients in mT/m, slew in T/m/s):
  python check_exported_seq.py sequence.seq --te 0.005 --tr 0.02 --flip 15 --slice-thickness 0.005 \
      --rf-spoil 117 --min-spoil-cycles 2 --matrix 64 64 --fov 0.2 --monopolar --max-grad 32 --max-slew 130
  inversion recovery:  --ti 0.1 0.5 1.5 --min-inversion-spoil-cycles 2
  balanced SSFP:       --balanced --rf-phase-cycle 180 --te-half-tr
  spin echo / CPMG:    --te 0.08 --cpmg
  EPI (one or more lines per excitation): --epi --te 0.03 --echo-spacing 0.0008 --matrix 64 64 --fov 0.22
  crushers and safety: --crusher-range LOW HIGH --safety --b1rms-max UT --b1peak-max UT --grms-max MT_PER_M \\
                       --pns-rheobase T_PER_M_PER_S --pns-chronaxie S --pns-max FRACTION   (limits from the task)
  sampling contract:   exact positions 'sample i at (i - n/2)/fov': --matrix NX NY [NZ] --fov F [FY FZ];
                       coverage 'cover [lo, hi]/fov, gaps <= g/fov': add --kx-cover LO HI --max-gap G (units of 1/fov);
                       acquired lines: --line-repeats R (each ky[,kz] line R times) and/or --n-adc N
  timing tolerance:    --time-tol S (default 1e-6 s; TE/TR/TI must match within it; --tr takes several intervals)

What is measured from the read-back file (fresh pp.Sequence().read):
  * RF roles: excitation (< 135 deg), inversion (large pulse not followed by an ADC before the next
    excitation) and refocusing (large pulse after an excitation and before its ADCs). An explicit
    rf.use ('excitation'/'inversion'/'refocusing') in the file takes precedence.
  * TE: excitation RF centre -> ADC sample closest to k = 0, per ADC. TR: spacing of excitation centres.
  * TI: inversion RF centre -> next excitation RF centre. Refocusing: time after excitation centre,
    and its phase relative to the excitation (CPMG: +/-90 deg).
  * RF phase pattern of excitations (second difference for quadratic spoiling, first difference for
    phase cycling) and ADC phase minus the phase of its own excitation (receive phase).
  * Net gradient area per axis between consecutive excitation centres (balanced sequences: ~0).
  * Spoiler area after each inversion (to the next excitation) and after the last ADC of each TR
    (to the next RF), per axis, in cycles/m; with --slice-thickness also cycles per slice.
  * Cartesian sampling: per ADC, kx grid (i - n//2)/fov, readout polarity, ky line set and order; the kx error
    is also reported separately for even and odd lines (EPI: an odd-only error means the ADC is not centred on the
    flat top of reversed lines, or the ramp/prephaser area differs by polarity).
  * --epi: TE per EXCITATION = its centre -> the sample closest to kx = ky = 0 over the whole echo train (without
    --epi every ADC line counts as its own echo); echo spacing = start-to-start time of consecutive lines.
  * Peak gradient/slew per axis and Pulseq timing errors. Number of excitations before the first ADC, with and
    without ADC, and how often each (ky[, kz]) line is acquired (dummy repetitions must not carry an ADC).
  * Gradient continuity: arbitrary gradients whose first/last values jump against the neighbouring block (always checked).
  * Coverage contracts (--kx-cover): samples must reach at least 0.05/fov beyond both ends and gaps must stay 1 % below
    the limit, because the .seq stores amplitudes with 6 significant digits and a grader integrates them its own way.
  * Spin-echo trains: gradient moment (cycles/m) on each side of every refocusing pulse, between its centre and the
    spin-echo times around it (the excitation centre before the first pulse; echo = 2 x refocusing centre - previous
    echo). Pulseq gradients are in Hz/m and areas in 1/m: a value near 1e-5 means T/m was passed where Hz/m was expected.
  * --safety: B1+rms over the whole file, B1 peak, gradient rms per axis and the ramp PNS fraction; a WARN line marks
    any value within 2 % of its limit (raster rounding can cross it: design with a margin).
Prints a compact summary and one PASS/FAIL line per expectation (add --json for every measurement);
exits 1 on any FAIL. From Python: rep, checks = measure('sequence.seq', te=..., ...).
Use the measured values in your report. Requires pypulseq >= 1.4 and numpy.
"""
import argparse, json, sys
import numpy as np
import pypulseq as pp

LARGE_FLIP_DEG = 135.0
ROLES = {'excitation', 'inversion', 'refocusing'}

def wrap_deg(x):
    return (np.asarray(x, float) + 180.0) % 360.0 - 180.0

def _area(w, t0, t1):
    """Exact integral of a piecewise-linear waveform (t, g) between t0 and t1 (cycles/m if g in Hz/m)."""
    t, g = w
    if len(t) == 0 or t1 <= t0:
        return 0.0
    tt = np.r_[t0, t[(t > t0) & (t < t1)], t1]
    return float(np.trapezoid(np.interp(tt, t, g, left=0, right=0), tt))

def _sq_integral(w, t0=None, t1=None):
    """Exact integral of g^2 dt for a piecewise-linear waveform (t, g)."""
    t, g = w
    if len(t) < 2:
        return 0.0
    dt = np.diff(t); g0, g1 = g[:-1], g[1:]
    return float(np.sum(dt * (g0 * g0 + g0 * g1 + g1 * g1) / 3.0))

def pns_ramps(w, rheobase, chronaxie, gamma):
    """PNS fraction of a piecewise-linear gradient waveform (t s, g Hz/m) under the hyperbolic strength-duration model:
    the waveform is cut into runs of one slope sign (zero-slope samples separate runs), and a run whose gradient moves
    by dG (T/m) within tau (s) gives P = |dG| / (rheobase (tau + chronaxie)). Returns (max P, worst run)."""
    t, g = w
    if len(t) < 2:
        return 0.0, None
    g = g / gamma; dt = np.diff(t); dg = np.diff(g); ok = dt > 1e-12
    t0, dt, dg = t[:-1][ok], dt[ok], dg[ok]
    tol = 1e-9 * max(np.max(np.abs(g)), 1e-12)
    sgn = np.where(np.abs(dg) <= tol * np.maximum(dt / 1e-5, 1), 0, np.sign(dg))
    best, worst = 0.0, None; i = 0
    while i < len(sgn):
        if sgn[i] == 0:
            i += 1; continue
        j = i; tau = 0.0; dG = 0.0
        while j < len(sgn) and sgn[j] == sgn[i] and (j == i or abs(t0[j] - (t0[j - 1] + dt[j - 1])) < 1e-9):
            tau += dt[j]; dG += dg[j]; j += 1
        P = abs(dG) / (rheobase * (tau + chronaxie))
        if P > best:
            best, worst = P, {'t_begin_s': float(t0[i]), 'run_s': float(tau), 'dG_mT_m': float(dG * 1e3)}
        i = j
    return float(best), worst

def _rf(rf, block_start):
    rt = np.asarray(rf.t); sig = np.asarray(rf.signal)
    w = np.diff(np.r_[0., (rt[:-1] + rt[1:]) / 2, float(rf.shape_dur)])
    use = str(getattr(rf, 'use', '') or '').lower()
    use = {'e': 'excitation', 'r': 'refocusing', 'i': 'inversion'}.get(use, use)
    return dict(start=block_start + rf.delay, end=block_start + rf.delay + float(rf.shape_dur),
                center=block_start + rf.delay + pp.calc_rf_center(rf)[0], flip=float(abs(np.sum(sig * w)) * 360.0),
                phase=float(np.rad2deg(rf.phase_offset)), use=use if use in ROLES else None, rf=rf, block_start=block_start)

def small_tip_fwhm(r, wz, extent):
    rf = r['rf']; rt = np.asarray(rf.t); sig = np.asarray(rf.signal)
    w = np.diff(np.r_[0., (rt[:-1] + rt[1:]) / 2, float(rf.shape_dur)])
    g = np.interp(r['block_start'] + rf.delay + rt, wz[0], wz[1], left=0, right=0) if len(wz[0]) else np.zeros_like(rt)
    if not np.any(abs(g[abs(sig) > .05 * abs(sig).max()]) > 1.):
        return None                      # no slice-select gradient during the RF: non-selective
    z = np.linspace(-extent, extent, 2001)
    resp = abs(np.exp(2j * np.pi * np.outer(z, np.cumsum(g * w))) @ (sig * w)); mid = np.argmin(abs(z)); half = resp[mid] / 2; lo = hi = mid
    while lo > 0 and resp[lo] >= half: lo -= 1
    while hi < len(z) - 1 and resp[hi] >= half: hi += 1
    return None if lo == 0 or hi == len(z) - 1 else float(z[hi] - z[lo])

COVER_MARGIN = 0.05     # in units of 1/fov: samples must lie at least this far beyond each end of a coverage interval
GAP_MARGIN = 0.01       # fractional margin below a maximum gap

def _err_us(measured, requested):
    m, r = np.sort(np.atleast_1d(measured)), np.sort(np.atleast_1d(requested))
    return float(np.max(abs(m - r)) * 1e6) if len(m) == len(r) and len(m) else None

def gradient_jumps(gblocks, gamma=42.576e6, max_slew=None):
    """Count discontinuities of each axis gradient: an arbitrary gradient whose first value is nonzero but starts
    after a delay or after a block ending at another value, or whose last value is nonzero but ends before the block
    end or before a block starting at another value. Trapezoids start and end at 0. Tolerance: 5 % of one raster step at
    the maximum slew (max_slew T/m/s) or 1e-3 of the peak."""
    peak = 1.0
    for _, _, gs in gblocks:
        for g in gs:
            if g is not None: peak = max(peak, abs(getattr(g, 'amplitude', 0.0)), abs(getattr(g, 'first', 0.0)), abs(getattr(g, 'last', 0.0)))
    tol = 0.05 * max_slew * gamma * 1e-5 if max_slew else 1e-3 * peak
    jumps = [0, 0, 0]; ex = []
    for ax in range(3):
        prev_end = 0.0
        for t0, dur, gs in gblocks:
            g = gs[ax]
            if g is None or g.type == 'trap':
                start = end = 0.0; ends_at_boundary = False; inner = []
            else:
                first, last = float(g.first), float(g.last); gd = float(g.delay); gend = gd + float(g.shape_dur)
                start = first if gd < 1e-9 else 0.0; ends_at_boundary = abs(gend - dur) < 1e-9; end = last if ends_at_boundary else 0.0
                inner = []
                if gd >= 1e-9 and abs(first) > tol: inner.append(('first value after a delay', first))
                if not ends_at_boundary and abs(last) > tol: inner.append(('last value before the block end', last))
            if abs(start - prev_end) > tol:
                jumps[ax] += 1; len(ex) < 4 and ex.append({'axis': 'xyz'[ax], 't_s': round(t0, 7), 'from_Hz_m': prev_end, 'to_Hz_m': start})
            for what, v in inner:
                jumps[ax] += 1; len(ex) < 4 and ex.append({'axis': 'xyz'[ax], 't_s': round(t0, 7), what: v})
            prev_end = end
        if abs(prev_end) > tol:
            jumps[ax] += 1
    return jumps, ex

def _uniq(x, nd=4):
    return sorted(set(round(float(v), nd) for v in x if np.isfinite(v)))

def measure(seq_path, te=None, tr=None, flip=None, slice_thickness=None, rf_spoil=None, max_grad=None, max_slew=None,
            gamma=42.576e6, ti=None, balanced=False, rf_phase_cycle=None, te_half_tr=False, cpmg=False,
            min_spoil_cycles=None, min_inversion_spoil_cycles=None, matrix=None, fov=None, monopolar=False,
            balanced_tol=0.05, epi=False, echo_spacing=None, crusher_range=None, crusher_axis='z', safety=False,
            pns_rheobase=None, pns_chronaxie=None, b1rms_max=None, b1peak_max=None, grms_max=None, pns_max=None,
            time_tol=1e-6, kx_cover=None, max_gap=1.0, line_repeats=None, n_adc=None):
    """Return (report, checks). te/ti: list or float (s); tr (s); flip (deg, excitations); matrix (nx, ny); fov m or (fx, fy).
    crusher_range (lo, hi) cycles/m: spin-echo crusher moments on crusher_axis; safety: B1 rms/peak (uT), gradient rms
    (mT/m) and, with pns_rheobase (T/m/s) and pns_chronaxie (s), the ramp PNS fraction, all from the exported file.
    time_tol (s): TE/TR/TI tolerance (default 1 us; use the task's tolerance if it is tighter). kx_cover (lo, hi) in units
    of 1/fov: every ADC must sample beyond both ends with no gap above max_gap/fov. line_repeats: expected number of
    acquisitions of every (ky[, kz]) line. n_adc: expected number of ADC events."""
    te = None if te is None else list(np.atleast_1d(te)); ti = None if ti is None else list(np.atleast_1d(ti))
    tr = None if tr is None else list(np.atleast_1d(tr))
    s = pp.Sequence(); s.read(str(seq_path)); rep = {}; checks = []
    ok, err = s.check_timing(); rep['timing_ok'] = bool(ok); rep['timing_errors'] = [str(e) for e in err][:5]
    t = 0.; rfs = []; adcs = []; gblocks = []
    for i in s.block_events:
        b = s.get_block(i); gblocks.append((t, s.block_durations[i] if hasattr(s, 'block_durations') else pp.calc_duration(b),
                                            [getattr(b, 'g' + a, None) for a in 'xyz']))
        if b.rf is not None: rfs.append(_rf(b.rf, t))
        if b.adc is not None: adcs.append(dict(start=t + b.adc.delay, adc=b.adc,
                                               end=t + b.adc.delay + b.adc.num_samples * b.adc.dwell))
        t += s.block_durations[i] if hasattr(s, 'block_durations') else pp.calc_duration(b)
    total = t; rep['duration_s'] = total; rep['n_rf'] = len(rfs); rep['n_adc'] = len(adcs)
    waves = list(s.waveforms())[:3]
    while len(waves) < 3: waves.append((np.array([]), np.array([])))
    waves = [(np.asarray(w[0], float), np.asarray(w[1], float)) for w in waves]
    rep['peak_grad_mT_m'] = [float(np.max(abs(w[1])) / gamma * 1e3) if len(w[1]) else 0. for w in waves]
    rep['gradient_jumps_per_axis'], rep['gradient_jump_examples'] = gradient_jumps(gblocks, gamma, max_slew)
    rep['peak_slew_T_m_s'] = [float(np.max(abs(np.diff(w[1]) / np.maximum(np.diff(w[0]), 1e-12))) / gamma) if len(w[1]) > 1 else 0. for w in waves]
    # --- RF roles
    adc_starts = np.array([a['start'] for a in adcs])
    small = [q for q in rfs if (q['use'] or ('excitation' if q['flip'] < LARGE_FLIP_DEG else '')) == 'excitation']
    for r in rfs:
        if r['use']: r['role'] = r['use']; continue
        if r['flip'] < LARGE_FLIP_DEG: r['role'] = 'excitation'; continue
        nxt = next((q['start'] for q in small if q['start'] > r['center']), total)
        prev_exc = any(q['center'] < r['center'] for q in small)
        has_adc = bool(np.any((adc_starts > r['end']) & (adc_starts < nxt)))
        r['role'] = 'refocusing' if (prev_exc and has_adc) else 'inversion'
    exc = [r for r in rfs if r['role'] == 'excitation']; inv = [r for r in rfs if r['role'] == 'inversion']
    ref = [r for r in rfs if r['role'] == 'refocusing']
    rep['rf_roles'] = {'excitation': len(exc), 'inversion': len(inv), 'refocusing': len(ref)}
    ec = np.array([r['center'] for r in exc])
    rep['excitation_flip_deg'] = _uniq([r['flip'] for r in exc], 3)
    rep['first_excitation_flips_deg'] = [round(r['flip'], 3) for r in exc[:3]]
    if inv: rep['inversion_flip_deg'] = _uniq([r['flip'] for r in inv], 2)
    if ref: rep['refocusing_flip_deg'] = _uniq([r['flip'] for r in ref], 2)
    fw = [small_tip_fwhm(r, waves[2], 2 * (slice_thickness or 0.01)) for r in exc]
    rep['excitation_slice_selective_all'] = bool(exc) and all(f is not None for f in fw)
    rep['excitation_slice_fwhm_mm'] = _uniq([f * 1e3 for f in fw if f is not None], 3)
    rep['tr_ms'] = _uniq(np.diff(ec) * 1e3, 4)
    # --- ADC timing, TE, receive phase, sampling
    tes = []; owner = []
    if adcs:
        k, _, _, _, ta = s.calculate_kspace(); kk = np.asarray(k).T; ta = np.asarray(ta); pos = 0
        rep_adc = []
        for a in adcs:
            n = a['adc'].num_samples; seg = kk[pos:pos + n]; tt = ta[pos:pos + n]; pos += n
            j = int(np.argmin(np.linalg.norm(seg, axis=1))); p = int(np.searchsorted(ec, tt[0], side='right') - 1)
            owner.append(p); tes.append(float(tt[j] - ec[p]) if p >= 0 else float('nan'))
            a.update(k=seg, t=tt, kmin_index=j, kmin=float(np.linalg.norm(seg[j])), owner=p)
        if epi:                                       # TE per excitation: the k = 0 sample of the whole train
            tes = []
            for p in sorted(set(owner)):
                if p < 0: continue
                own = [a for a in adcs if a['owner'] == p]
                kmins = [a['kmin'] for a in own]; a0 = own[int(np.argmin(kmins))]
                tes.append(float(a0['t'][a0['kmin_index']] - ec[p]))
            sp = []
            for p in sorted(set(owner)):
                st = np.array([a['t'][0] for a in adcs if a['owner'] == p])
                if len(st) > 1: sp.extend(np.diff(st))
            rep['echo_spacing_ms'] = _uniq(np.array(sp) * 1e3, 4)
        rep['adc_samples'] = _uniq([a['adc'].num_samples for a in adcs], 0)
        rep['excitations_before_first_adc'] = int(adcs[0]['owner'])   # unacquired (dummy/preparation) excitations
        per = {}
        for a in adcs: per[a['owner']] = per.get(a['owner'], 0) + 1
        rep['excitations_with_adc'] = len(per); rep['excitations_without_adc'] = len(exc) - len([p for p in per if p >= 0])
        rep['adc_events_per_excitation'] = _uniq(list(per.values()), 0)
        rep['te_ms'] = _uniq(np.array(tes) * 1e3, 4)
        rep['k_center_sample_index'] = _uniq([a['kmin_index'] for a in adcs], 0)
        rep['max_abs_k_at_center_sample_cycles_m'] = max(a['kmin'] for a in adcs)
        rx = [wrap_deg(np.rad2deg(a['adc'].phase_offset) - exc[a['owner']]['phase']) if a['owner'] >= 0 else np.nan for a in adcs]
        rep['adc_minus_excitation_phase_max_deg'] = float(np.nanmax(np.abs(rx)))
        # spoiler after the last ADC of each excitation interval, to the next RF start
        last = {}
        for a in adcs: last[a['owner']] = max(last.get(a['owner'], -1), a['end'])
        rf_starts = np.array([r['start'] for r in rfs]); post = []
        for p, tend in last.items():
            nxt = rf_starts[rf_starts > tend]; t1 = nxt[0] if len(nxt) else total
            post.append([_area(w, tend, t1) for w in waves])
        post = np.abs(np.array(post)); rep['post_readout_spoiler_cycles_m_min_per_axis'] = post.min(0).round(3).tolist()
        if slice_thickness: rep['post_readout_z_spoiler_cycles_per_slice_min'] = float(post[:, 2].min() * slice_thickness)
        if te_half_tr and len(ec) > 1:
            rep['te_minus_half_tr_ms'] = _uniq((np.array(tes) - np.median(np.diff(ec)) / 2) * 1e3, 4)
    # --- excitation phase pattern
    ph = np.array([r['phase'] for r in exc])
    if len(ph) >= 2: rep['excitation_phase_first_diff_deg'] = _uniq(wrap_deg(np.diff(ph)) % 360, 3)[:8]
    if len(ph) >= 3: rep['excitation_phase_second_diff_deg'] = _uniq(wrap_deg(np.diff(ph, 2)) % 360, 3)[:8]
    rep['max_abs_excitation_phase_deg'] = float(np.max(np.abs(ph))) if len(ph) else 0.
    # --- balanced moments between consecutive excitation centres
    if len(ec) > 1:
        net = np.array([[_area(w, a, b) for w in waves] for a, b in zip(ec[:-1], ec[1:])])
        rep['net_area_per_tr_cycles_m_max_abs'] = np.abs(net).max(0).round(4).tolist()
    # --- inversion recovery
    if inv:
        tis = []; inv_sp = []
        for r in inv:
            nx = [q for q in exc if q['center'] > r['center']]
            if nx:
                tis.append(nx[0]['center'] - r['center'])
                inv_sp.append([_area(w, r['end'], nx[0]['start']) for w in waves])   # up to the next excitation START
        rep['ti_ms'] = _uniq(np.array(tis) * 1e3, 4)
        if inv_sp:
            sp = np.abs(np.array(inv_sp)); rep['post_inversion_spoiler_cycles_m_min_per_axis'] = sp.min(0).round(3).tolist()
            if slice_thickness: rep['post_inversion_z_spoiler_cycles_per_slice_min'] = float(sp[:, 2].min() * slice_thickness)
    # --- spin echo
    if ref:
        tau = []; rel = []
        for r in ref:
            p = int(np.searchsorted(ec, r['center'], side='right') - 1)
            if p >= 0: tau.append(r['center'] - ec[p]); rel.append(wrap_deg(r['phase'] - exc[p]['phase']))
        rep['refocusing_after_excitation_ms'] = _uniq(np.array(tau) * 1e3, 4)[:12]
        rep['refocusing_minus_excitation_phase_deg'] = _uniq(rel, 2)
        ax = {'x': 0, 'y': 1, 'z': 2}[crusher_axis]; pre, post = [], []
        for p, e0 in enumerate(ec):
            nxt = ec[p + 1] if p + 1 < len(ec) else total
            echo = e0
            for r in sorted([r for r in ref if e0 < r['center'] < nxt], key=lambda q: q['center']):
                e_n = 2 * r['center'] - echo                      # ideal echo time after this refocusing pulse
                pre.append(_area(waves[ax], echo, r['center'])); post.append(_area(waves[ax], r['center'], e_n)); echo = e_n
        if pre:
            pre, post = np.abs(pre), np.abs(post)
            rep['crusher_moment_cycles_m'] = {'axis': crusher_axis, 'before_refocusing': [float(pre.min()), float(pre.max())],
                                              'after_refocusing': [float(post.min()), float(post.max())],
                                              'max_relative_mismatch': float(np.max(np.abs(pre - post) / np.maximum(np.maximum(pre, post), 1e-12)))}
    # --- Cartesian sampling
    if matrix is not None and fov is not None and adcs:
        mt = [int(v) for v in np.atleast_1d(matrix)]; nx = mt[0]; ny = mt[1] if len(mt) > 1 else mt[0]; nz = mt[2] if len(mt) > 2 else None
        fv = list(np.atleast_1d(fov)); fx = fv[0]; fy = fv[1] if len(fv) > 1 else fv[0]; fz = fv[2] if len(fv) > 2 else fv[-1]
        exp_kx = (np.arange(nx) - nx // 2) / fx; errs = []; pol = []; kys = []; kzs = []; par = {0: [], 1: []}; line = {}
        for a in adcs:
            kx = a['k'][:, 0]; ns = len(kx)
            if ns < nx: errs.append(np.inf); continue
            pol.append(np.sign(np.median(np.diff(kx))))
            if ns == nx:
                e = float(min(np.max(abs(kx - exp_kx)), np.max(abs(kx[::-1] - exp_kx))))
            else:                                        # oversampled or extended readout: every grid point is sampled
                e = float(np.max(np.min(abs(kx[None, :] - exp_kx[:, None]), axis=1)))
            errs.append(e); j = line.get(a['owner'], 0); line[a['owner']] = j + 1; par[j % 2].append(e)
            kys.append(float(np.median(a['k'][:, 1]))); kzs.append(float(np.median(a['k'][:, 2])))
        rep['kx_grid_max_err_cycles_m'] = float(max(errs)); rep['readout_polarities'] = _uniq(pol, 0)
        rep['samples_per_adc_vs_matrix'] = f"{_uniq([a['adc'].num_samples for a in adcs], 0)} for nx = {nx}"
        rep['kx_grid_max_err_by_line_parity'] = {'even': max(par[0]) if par[0] else None, 'odd': max(par[1]) if par[1] else None}
        rep['ky_lines'] = len(_uniq(kys, 3)); exp_ky = (np.arange(ny) - ny // 2) / fy
        rep['ky_set_max_err_cycles_m'] = float(max(min(abs(exp_ky - v)) for v in kys)) if kys else None
        rep['ky_order_first_lines'] = [round(v * fy, 3) for v in kys[:6]]
        keys = [(int(np.rint(v * fy)), int(np.rint(w * fz)) if nz else 0) for v, w in zip(kys, kzs)]
        if nz:
            exp_kz = (np.arange(nz) - nz // 2) / fz
            rep['kz_set_max_err_cycles_m'] = float(max(min(abs(exp_kz - w)) for w in kzs))
        cnt = {}
        for kk in keys: cnt[kk] = cnt.get(kk, 0) + 1
        rep['line_acquisitions'] = {'lines': len(cnt), 'expected_lines': ny * (nz or 1), 'min': min(cnt.values()), 'max': max(cnt.values()),
                                    'lines_acquired_most': [k for k, v in cnt.items() if v == max(cnt.values())][:4]}
        if kx_cover is not None:
            lo, hi = kx_cover; cov = []; bad = 0
            for a in adcs:
                u = np.sort(a['k'][:, 0] * fx)
                inside = u[(u >= lo - 1) & (u <= hi + 1)]
                gaps = np.diff(inside) if len(inside) > 1 else np.array([np.inf])
                m_lo, m_hi = lo - u[0], u[-1] - hi; g = float(np.max(gaps))
                cov.append((m_lo, m_hi, g)); bad += not (m_lo >= COVER_MARGIN and m_hi >= COVER_MARGIN and g <= max_gap * (1 - GAP_MARGIN))
            cv = np.array(cov)
            rep['kx_coverage_units_of_1_over_fov'] = {'min_margin_below_lo': float(cv[:, 0].min()), 'min_margin_above_hi': float(cv[:, 1].min()),
                                                      'max_gap': float(cv[:, 2].max()), 'adc_events_failing': int(bad)}
    # --- safety quantities of the whole exported file (nominal RF amplitude)
    if safety or b1rms_max or b1peak_max or grms_max or pns_max:
        e_rf = 0.0; peak = 0.0
        for r in rfs:
            rf = r['rf']; rt = np.asarray(rf.t); sig = np.abs(np.asarray(rf.signal)) / gamma
            w = np.diff(np.r_[0., (rt[:-1] + rt[1:]) / 2, float(rf.shape_dur)]); e_rf += float(np.sum(sig ** 2 * w)); peak = max(peak, float(sig.max()))
        rep['b1_rms_whole_file_uT'] = float(np.sqrt(e_rf / total) * 1e6); rep['b1_peak_whole_file_uT'] = peak * 1e6
        rep['grad_rms_mT_m'] = [float(np.sqrt(_sq_integral(w) / total) / gamma * 1e3) for w in waves]
        if pns_rheobase and pns_chronaxie:
            pn = [pns_ramps(w, pns_rheobase, pns_chronaxie, gamma) for w in waves]
            rep['pns_max_fraction_per_axis'] = [round(v[0], 5) for v in pn]
            rep['pns_worst_run'] = pn[int(np.argmax([v[0] for v in pn]))][1]
    # --- checks
    def chk(name, cond, detail): checks.append({'item': name, 'pass': bool(cond), 'detail': detail})
    def near(value, limit, upper=True):
        """WARN when a measured value sits within 2 % of a limit: raster rounding can cross it."""
        if limit and value is not None and (abs(value - limit) <= 0.02 * abs(limit)):
            rep.setdefault('margin_warnings', []).append(f"{value:.6g} is within 2% of the limit {limit:g}: design inside the limit with a margin")
    chk('pulseq timing', rep['timing_ok'], rep['timing_errors'][:2])
    if max_grad: chk('peak gradient', max(rep['peak_grad_mT_m']) <= max_grad + 1e-3, rep['peak_grad_mT_m'])
    if max_slew: chk('peak slew', max(rep['peak_slew_T_m_s']) <= max_slew + 1e-3, rep['peak_slew_T_m_s'])
    if te is not None and adcs:
        u = np.array(_uniq(np.array(tes), 7))
        chk(f'realized TE (excitation centre -> k=0 sample) within {time_tol * 1e6:g} us', len(u) == len(te) and np.allclose(u, sorted(te), atol=time_tol),
            {'te_ms': rep['te_ms'], 'max_error_us': _err_us(u, te)})
    if tr is not None:
        u = np.array(rep['tr_ms']) / 1e3
        chk(f'realized TR (excitation centres) within {time_tol * 1e6:g} us', len(u) == len(tr) and np.allclose(u, sorted(tr), atol=time_tol),
            {'tr_ms': rep['tr_ms'], 'max_error_us': _err_us(u, tr), 'hint': 'several values: pass every interval (e.g. --tr TRAIN_TR CYCLE_GAP)'})
    if ti is not None:
        u = np.array(rep.get('ti_ms', [])) / 1e3
        chk(f'realized TI (inversion centre -> excitation centre) within {time_tol * 1e6:g} us', len(u) == len(ti) and np.allclose(u, np.sort(ti), atol=time_tol),
            {'ti_ms': rep.get('ti_ms'), 'max_error_us': _err_us(u, ti)})
    if flip is not None:
        acq = sorted(set(owner)) if adcs else range(len(exc))
        chk('excitation flip angle (acquired TRs)', len(exc) > 0 and np.allclose([exc[p]['flip'] for p in acq if p >= 0], flip, atol=.25), rep['excitation_flip_deg'])
    if slice_thickness:
        chk('slice-selective excitation with small-tip FWHM within 20%', rep['excitation_slice_selective_all'] and all(abs(f - slice_thickness) <= .2 * slice_thickness for f in fw if f is not None), rep['excitation_slice_fwhm_mm'])
    if rf_spoil is not None and len(ph) >= 3:
        e = wrap_deg(np.diff(ph, 2) - rf_spoil); chk('quadratic RF spoiling increment', np.max(abs(e)) < .1, {'max_error_deg': float(np.max(abs(e))), 'hint': 'wrap increment and phase to [0,360) each update'})
    if rf_phase_cycle is not None and len(ph) >= 2:
        e = wrap_deg(np.diff(ph) - rf_phase_cycle); chk('RF phase cycling increment', np.max(abs(e)) < .1, rep['excitation_phase_first_diff_deg'])
    if adcs and (rf_spoil is not None or rf_phase_cycle is not None):
        chk('ADC phase equals the phase of its own excitation', rep['adc_minus_excitation_phase_max_deg'] < .1, rep['adc_minus_excitation_phase_max_deg'])
    if balanced: chk('balanced: zero net gradient area per TR on every axis', 'net_area_per_tr_cycles_m_max_abs' in rep and max(rep['net_area_per_tr_cycles_m_max_abs']) <= balanced_tol, rep.get('net_area_per_tr_cycles_m_max_abs'))
    if te_half_tr and adcs and 'te_minus_half_tr_ms' in rep: chk('TE = TR/2', max(abs(np.array(rep['te_minus_half_tr_ms']))) <= 1e-2, rep['te_minus_half_tr_ms'])
    if cpmg: chk('CPMG: refocusing phase = excitation phase +/- 90 deg', ref and all(abs(abs(x) - 90) < .1 for x in rep['refocusing_minus_excitation_phase_deg']), rep.get('refocusing_minus_excitation_phase_deg'))
    if min_spoil_cycles is not None and adcs and slice_thickness:
        chk('post-readout z spoiler (cycles per slice)', rep['post_readout_z_spoiler_cycles_per_slice_min'] >= min_spoil_cycles - 1e-3, rep['post_readout_z_spoiler_cycles_per_slice_min'])
    if min_inversion_spoil_cycles is not None and slice_thickness:
        chk('post-inversion z spoiler (cycles per slice)', inv and rep.get('post_inversion_z_spoiler_cycles_per_slice_min', 0) >= min_inversion_spoil_cycles - 1e-3, rep.get('post_inversion_z_spoiler_cycles_per_slice_min'))
    if echo_spacing is not None and adcs:
        es = rep.get('echo_spacing_ms', [])
        chk('EPI echo spacing: constant and <= requested', len(es) == 1 and es[0] <= echo_spacing * 1e3 + 1e-3, es)
    if matrix is not None and fov is not None and adcs:
        chk('Cartesian kx grid (i - n//2)/fov sampled', rep['kx_grid_max_err_cycles_m'] <= .01,
            {'max': rep['kx_grid_max_err_cycles_m'], 'by_line_parity': rep['kx_grid_max_err_by_line_parity'], 'samples': rep['samples_per_adc_vs_matrix'],
             'hint': 'odd-only error: ADC not centred on reversed flat tops; both: prephaser or k=0 sample index'})
        chk('Cartesian ky line set', rep['ky_set_max_err_cycles_m'] is not None and rep['ky_set_max_err_cycles_m'] <= .01, rep['ky_set_max_err_cycles_m'])
        if 'kz_set_max_err_cycles_m' in rep: chk('Cartesian kz partition set', rep['kz_set_max_err_cycles_m'] <= .01, rep['kz_set_max_err_cycles_m'])
        if monopolar: chk('monopolar readout', rep['readout_polarities'] == [1.0], rep['readout_polarities'])
        la = rep['line_acquisitions']
        if line_repeats is not None:
            chk(f'every line acquired exactly {line_repeats} time(s) (dummy repetitions must have no ADC)',
                la['lines'] == la['expected_lines'] and la['min'] == la['max'] == line_repeats, la)
        elif la['min'] != la['max']:
            rep.setdefault('margin_warnings', []).append(f"lines are acquired unequally often {la}: dummies with ADC, navigators or a wrong partition/line loop?")
        if kx_cover is not None:
            kc = rep['kx_coverage_units_of_1_over_fov']
            chk(f'readout coverage of [{kx_cover[0]:g}, {kx_cover[1]:g}]/fov with margin {COVER_MARGIN}/fov beyond each end, gaps <= {max_gap:g}/fov (less {GAP_MARGIN:.0%})',
                kc['adc_events_failing'] == 0, dict(kc, hint='samples exactly on an end or spaced exactly at the limit fail after export rounding: '
                                                              'oversample the readout (2x) and add samples beyond both ends (centered_readout/add_epi_readout oversample=2, extra=1)'))
    if n_adc is not None: chk(f'number of ADC events = {n_adc}', len(adcs) == n_adc, {'n_adc': len(adcs), 'excitations_with_adc': rep.get('excitations_with_adc')})
    njump = sum(rep['gradient_jumps_per_axis'])
    chk('gradients continuous at block and event boundaries (arbitrary gradients: first/last values match the neighbours)', njump == 0,
        {'jumps_per_axis_xyz': rep['gradient_jumps_per_axis'], 'examples': rep['gradient_jump_examples'],
         'hint': 'pass first= and last= to make_arbitrary_grad (0 when the neighbouring block has no gradient on that axis)'})
    if crusher_range is not None:
        cm = rep.get('crusher_moment_cycles_m'); lo, hi = crusher_range
        okc = cm is not None and lo <= min(cm['before_refocusing'][0], cm['after_refocusing'][0]) and max(cm['before_refocusing'][1], cm['after_refocusing'][1]) <= hi
        chk(f'spin-echo crusher moments on {crusher_axis} within [{lo:g}, {hi:g}] cycles/m (Pulseq areas: Hz/m * s = 1/m)', okc,
            cm if cm else 'no refocusing pulses found')
        if cm:
            for v in cm['before_refocusing'] + cm['after_refocusing']:
                near(v, lo); near(v, hi)
    if b1rms_max: chk('B1+rms over the whole file (uT)', rep['b1_rms_whole_file_uT'] <= b1rms_max, rep['b1_rms_whole_file_uT']); near(rep['b1_rms_whole_file_uT'], b1rms_max)
    if b1peak_max: chk('B1 peak (uT)', rep['b1_peak_whole_file_uT'] <= b1peak_max, rep['b1_peak_whole_file_uT']); near(rep['b1_peak_whole_file_uT'], b1peak_max)
    if grms_max: chk('gradient rms per axis (mT/m)', max(rep['grad_rms_mT_m']) <= grms_max, rep['grad_rms_mT_m']); near(max(rep['grad_rms_mT_m']), grms_max)
    if pns_max and 'pns_max_fraction_per_axis' in rep:
        chk('ramp PNS fraction', max(rep['pns_max_fraction_per_axis']) <= pns_max, rep['pns_max_fraction_per_axis']); near(max(rep['pns_max_fraction_per_axis']), pns_max)
    if max_grad: near(max(rep['peak_grad_mT_m']), max_grad)
    if max_slew: near(max(rep['peak_slew_T_m_s']), max_slew)
    supplied = {'max_grad': max_grad, 'max_slew': max_slew, 'te': te, 'tr': tr, 'ti': ti, 'flip': flip,
                'slice_thickness': slice_thickness, 'rf_spoil or rf_phase_cycle': rf_spoil if rf_spoil is not None else rf_phase_cycle,
                'min_spoil_cycles': min_spoil_cycles, 'matrix and fov': matrix if fov is not None else None,
                'n_adc or line_repeats (acquired ADC count)': n_adc if n_adc is not None else line_repeats}
    if ti is not None:
        supplied['min_inversion_spoil_cycles'] = min_inversion_spoil_cycles
    if epi:
        supplied['echo_spacing'] = echo_spacing
    rep['not_checked'] = [k for k, v in supplied.items() if v is None]
    rep['never_checked_here'] = ['steady state before the first acquired line (count and convergence of preparation repetitions)',
                                 'inversion or preparation cycle period and recovery between cycles',
                                 'that the delivered simulation is KomaMRI output of this exact file (mrfoundry_seqlib.replay_check)',
                                 'any protocol requirement not listed in the checks above']
    rep['checks'] = checks
    return rep, checks

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('seq'); ap.add_argument('--te', type=float, nargs='*'); ap.add_argument('--tr', type=float, nargs='*')
    ap.add_argument('--ti', type=float, nargs='*'); ap.add_argument('--flip', type=float); ap.add_argument('--slice-thickness', type=float)
    ap.add_argument('--rf-spoil', type=float); ap.add_argument('--rf-phase-cycle', type=float)
    ap.add_argument('--balanced', action='store_true'); ap.add_argument('--te-half-tr', action='store_true'); ap.add_argument('--cpmg', action='store_true')
    ap.add_argument('--min-spoil-cycles', type=float); ap.add_argument('--min-inversion-spoil-cycles', type=float)
    ap.add_argument('--matrix', type=int, nargs='+'); ap.add_argument('--fov', type=float, nargs='+'); ap.add_argument('--monopolar', action='store_true')
    ap.add_argument('--max-grad', type=float, help='mT/m'); ap.add_argument('--max-slew', type=float, help='T/m/s')
    ap.add_argument('--epi', action='store_true', help='several lines per excitation: TE to the k=0 sample of the train')
    ap.add_argument('--echo-spacing', type=float, help='EPI: maximum line period (s); must be constant')
    ap.add_argument('--crusher-range', type=float, nargs=2, metavar=('LOW', 'HIGH'), help='spin-echo crusher moment range, cycles/m')
    ap.add_argument('--crusher-axis', default='z', choices=['x', 'y', 'z'])
    ap.add_argument('--safety', action='store_true', help='report B1 rms/peak (uT), gradient rms (mT/m) of the whole file')
    ap.add_argument('--pns-rheobase', type=float, help='T/m/s (ramp model P = dG / (rheobase (tau + chronaxie)))')
    ap.add_argument('--pns-chronaxie', type=float, help='s')
    ap.add_argument('--b1rms-max', type=float); ap.add_argument('--b1peak-max', type=float)
    ap.add_argument('--grms-max', type=float, help='mT/m'); ap.add_argument('--pns-max', type=float)
    ap.add_argument('--time-tol', type=float, default=1e-6, help='TE/TR/TI tolerance in s (default 1 us)')
    ap.add_argument('--kx-cover', type=float, nargs=2, metavar=('LO', 'HI'), help='coverage contract in units of 1/fov, e.g. -N/2 N/2-1')
    ap.add_argument('--max-gap', type=float, default=1.0, help='largest allowed kx gap inside the coverage interval, units of 1/fov')
    ap.add_argument('--line-repeats', type=int, help='times every (ky[, kz]) line is acquired (1 for single-image Cartesian)')
    ap.add_argument('--n-adc', type=int, help='expected number of ADC events')
    ap.add_argument('--gamma', type=float, default=42.576e6); ap.add_argument('--json', action='store_true', help='print all measurements')
    a = ap.parse_args()
    fov = None if a.fov is None else (a.fov[0] if len(a.fov) == 1 else a.fov)
    rep, checks = measure(a.seq, a.te, a.tr, a.flip, a.slice_thickness, a.rf_spoil, a.max_grad, a.max_slew, a.gamma, a.ti,
                          a.balanced, a.rf_phase_cycle, a.te_half_tr, a.cpmg, a.min_spoil_cycles, a.min_inversion_spoil_cycles,
                          a.matrix, fov, a.monopolar, epi=a.epi, echo_spacing=a.echo_spacing, crusher_range=a.crusher_range,
                          crusher_axis=a.crusher_axis, safety=a.safety, pns_rheobase=a.pns_rheobase, pns_chronaxie=a.pns_chronaxie,
                          b1rms_max=a.b1rms_max, b1peak_max=a.b1peak_max, grms_max=a.grms_max, pns_max=a.pns_max,
                          time_tol=a.time_tol, kx_cover=a.kx_cover, max_gap=a.max_gap, line_repeats=a.line_repeats, n_adc=a.n_adc)
    keys = ['rf_roles', 'excitation_flip_deg', 'te_ms', 'echo_spacing_ms', 'tr_ms', 'ti_ms', 'refocusing_after_excitation_ms', 'excitations_before_first_adc',
            'excitations_with_adc', 'excitations_without_adc', 'adc_samples', 'line_acquisitions', 'kx_coverage_units_of_1_over_fov', 'gradient_jumps_per_axis', 'excitation_slice_fwhm_mm', 'peak_grad_mT_m', 'peak_slew_T_m_s', 'crusher_moment_cycles_m',
            'b1_rms_whole_file_uT', 'b1_peak_whole_file_uT', 'grad_rms_mT_m', 'pns_max_fraction_per_axis']
    out = rep if a.json else {k: rep[k] for k in keys if k in rep}
    print(json.dumps({k: v for k, v in out.items() if k != 'checks'}, default=float))
    for c in checks: print(('PASS ' if c['pass'] else 'FAIL ') + c['item'] + ': ' + json.dumps(c['detail'], default=float))
    for w_ in rep.get('margin_warnings', []): print('WARN ' + w_)
    if rep['not_checked']: print('NOT CHECKED (no expectation supplied): ' + ', '.join(rep['not_checked']))
    print('VERIFY SEPARATELY: ' + '; '.join(rep['never_checked_here']))
    sys.exit(1 if any(not c['pass'] for c in checks) else 0)

if __name__ == '__main__':
    main()

