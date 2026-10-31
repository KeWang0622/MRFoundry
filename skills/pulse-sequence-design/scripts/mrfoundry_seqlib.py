"""MRFoundry sequence helpers: small, tested building blocks for PyPulseq + KomaMRI work.

Tested with pypulseq 1.5.0.post1, komamripy 0.0.11-0.0.14 (KomaMRI 0.14, KomaMRICore 0.13), Julia 1.10, numpy 2.x.
Copy the functions you need into your own script, or import this file. Each helper
encodes a convention that is easy to get wrong; read its docstring.
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
import pypulseq as pp

def make_system(max_grad_mT_m=32, max_slew_T_m_s=130, rf_dead_time=100e-6, rf_ringdown_time=20e-6,
                adc_dead_time=10e-6, grad_raster=10e-6, rf_raster=1e-6, adc_raster=1e-7, block_raster=10e-6):
    """pp.Opts with explicit units (mT/m, T/m/s, seconds)."""
    return pp.Opts(max_grad=max_grad_mT_m, grad_unit='mT/m', max_slew=max_slew_T_m_s, slew_unit='T/m/s',
                   rf_dead_time=rf_dead_time, rf_ringdown_time=rf_ringdown_time, adc_dead_time=adc_dead_time,
                   grad_raster_time=grad_raster, rf_raster_time=rf_raster, adc_raster_time=adc_raster,
                   block_duration_raster=block_raster)

def slice_selective_excitation(system, flip_deg, slice_thickness_m, duration=2e-3, tbw=4, apodization=0.5, center_shift=0.0,
                               use='excitation', phase_offset=0.0):
    """Sinc pulse played WITH its slice-select gradient: seq.add_block(rf, gz).
    Returns (rf, gz, rephase_area); play a z trapezoid of rephase_area (cycles/m) after it.
    center_shift (s, multiple of the RF raster, >= 0) moves the RF later inside the block and lengthens the flat top
    of gz to keep the whole pulse on it: use it for sub-raster timing (TE, TI, TR, spin-echo symmetry), since block
    boundaries sit on the 10 us block raster but the RF delay has the 1 us RF raster. rephase_area always refocuses
    from the RF centre. A short hard (block) pulse is non-selective and is wrong for a 2D slice prescription."""
    rf, gz, gzr = pp.make_sinc_pulse(np.deg2rad(flip_deg), duration=duration, slice_thickness=slice_thickness_m,
                                     apodization=apodization, time_bw_product=tbw, system=system, return_gz=True,
                                     delay=system.rf_dead_time, use=use, phase_offset=phase_offset)
    if center_shift:
        r = system.rf_raster_time; k = round(center_shift / r)
        if abs(k * r - center_shift) > 1e-9 or center_shift < 0:
            raise ValueError('center_shift must be a non-negative multiple of the RF raster')
        ext = np.ceil(center_shift / system.grad_raster_time - 1e-9) * system.grad_raster_time
        gz = pp.make_trapezoid('z', amplitude=gz.amplitude, flat_time=gz.flat_time + ext, rise_time=gz.rise_time,
                               fall_time=gz.fall_time, delay=gz.delay, system=system)
        rf.delay = rf.delay + k * r
    tc = rf.delay + pp.calc_rf_center(rf)[0]                     # RF centre, from the block start
    flat_end = gz.delay + gz.rise_time + gz.flat_time
    return rf, gz, -(gz.amplitude * (flat_end - tc) + 0.5 * gz.amplitude * gz.fall_time)

def centered_readout(system, n, fov_m, dwell_s, axis='x', center_index=None, oversample=1, extra=0, adc_shift=0.0):
    """Readout trapezoid + ADC + prephaser area for a Cartesian line. Returns (read, adc, pre_area).
    The ADC has N = oversample*n + 2*extra samples; sample i sits at k = (i - c) / (oversample*fov) with
    c = extra + oversample*(n//2) (or center_index), so k = 0 is sample c. Play a prephaser of area pre_area on the same
    axis before the readout block.
    Choose by the sampling requirement:
      * each sample index has a required k position: oversample=1, extra=0 (the default).
      * an interval of k must be covered with a bounded spacing between samples: oversample=2, extra>=1, so samples
        lie beyond both ends and the spacing is below the bound. Exactly n samples put the end samples ON the interval
        ends with spacing exactly at the bound; .seq files store gradient amplitudes with 6 significant digits, so
        such designs fail coverage checks about half the time.
    adc_shift (s, multiple of the RF raster, on which Pulseq checks ADC delays) delays the ADC inside the flat top and
    moves the prephaser so sample c stays at k = 0: it moves the k = 0 sample by sub-raster amounts (exact TE).
    dwell_s must be on the ADC raster."""
    if abs(adc_shift / system.rf_raster_time - round(adc_shift / system.rf_raster_time)) > 1e-6 or adc_shift < 0:
        raise ValueError('adc_shift must be a non-negative multiple of the RF raster (Pulseq checks ADC delays on it)')
    N = oversample * n + 2 * extra
    c = (extra + oversample * (n // 2)) if center_index is None else center_index
    g = 1.0 / (oversample * fov_m * dwell_s)                   # Hz/m: sample spacing 1/(oversample*fov)
    rast = system.grad_raster_time
    flat = np.ceil((N * dwell_s + adc_shift) / rast - 1e-9) * rast
    read = pp.make_trapezoid(axis, amplitude=g, flat_time=flat, system=system)
    adc = pp.make_adc(N, dwell=dwell_s, delay=read.delay + read.rise_time + adc_shift, system=system)
    pre_area = -0.5 * g * read.rise_time - g * (adc_shift + (c + 0.5) * dwell_s)
    return read, adc, pre_area

def add_epi_readout(seq, system, nx, ny, fov_m, dwell_s, extra_blocks=(), read_axis='x', blip_axis='y', fov_y=None,
                    oversample=1, extra=0):
    """Single-shot EPI train: prephaser block (plus any extra_blocks events, e.g. the slice rephaser) then ny lines
    of alternating readout polarity, ADC on the flat top only (no ramp sampling), phase-encode blips during the
    ramp-down. Each line has N = oversample*nx + 2*extra samples; on even lines sample s sits at
    kx = (s - c)/(oversample*fov) with c = extra + oversample*(nx//2), on odd lines the same grid is traversed
    backwards (k = 0 at sample N-1-c); line j sits at ky = (j - ny//2)/fov_y. N*dwell_s must be a multiple of the
    gradient raster (with extra > 0, extra is raised until it is; the value used is returned). Required k position per sample -> oversample=1, extra=0; interval coverage with a spacing
    bound -> oversample=2, extra>=1 (see centered_readout). The line period is constant. Returns timing:
    line_period, prephaser_duration, n_samples, k0_index_even/odd and t_k0 = time from the start of the prephaser
    block to the sample at kx = ky = 0 (TE = excitation centre -> that sample).
    Verify the export with check_exported_seq.py --epi --matrix nx ny --fov F --te TE --echo-spacing ES
    (and --kx-cover LO HI for interval coverage)."""
    fov_y = fov_m if fov_y is None else fov_y
    r = system.grad_raster_time
    on = lambda N: abs(N * dwell_s / r - round(N * dwell_s / r)) < 1e-6
    if extra == 0 and not on(oversample * nx):
        raise ValueError(f'EPI: {oversample * nx} samples x dwell {dwell_s:g} s is not on the {r:g} s gradient raster: change the dwell')
    while extra and not on(oversample * nx + 2 * extra) and extra < 64:
        extra += 1                                         # extra is a minimum: pad until the flat top is on the raster
    if not on(oversample * nx + 2 * extra):
        raise ValueError(f'EPI: no sample count near {oversample * nx} puts dwell {dwell_s:g} s on the {r:g} s raster: change the dwell')
    N = oversample * nx + 2 * extra; c = extra + oversample * (nx // 2)
    blip = pp.make_trapezoid(blip_axis, area=1.0 / fov_y, system=system)
    ramp = max(np.ceil(pp.calc_duration(blip) / r - 1e-9) * r, 0)
    g = 1.0 / (oversample * fov_m * dwell_s)
    probe = pp.make_trapezoid(read_axis, amplitude=g, flat_time=N * dwell_s, system=system)
    ramp = max(ramp, probe.rise_time)
    read = pp.make_trapezoid(read_axis, amplitude=g, flat_time=N * dwell_s, rise_time=ramp, fall_time=ramp, system=system)
    adc = pp.make_adc(N, dwell=dwell_s, delay=read.rise_time, system=system)
    pre_area = -0.5 * g * read.rise_time - g * (c + 0.5) * dwell_s
    gx_pre = pp.make_trapezoid(read_axis, area=pre_area, system=system)
    gy_pre = pp.make_trapezoid(blip_axis, area=-(ny // 2) / fov_y, system=system)
    pre_events = [gx_pre, gy_pre] + list(extra_blocks)
    seq.add_block(*pre_events); t_pre = pp.calc_duration(*pre_events)
    blip.delay = read.rise_time + read.flat_time
    neg = pp.scale_grad(read, -1)
    for j in range(ny):
        g_ = read if j % 2 == 0 else neg
        if j < ny - 1:
            seq.add_block(g_, adc, blip)
        else:
            seq.add_block(g_, adc)
    period = pp.calc_duration(read)
    k0_odd = N - 1 - c
    t_k0 = t_pre + (ny // 2) * period + adc_sample_time(adc, c if (ny // 2) % 2 == 0 else k0_odd)
    return dict(line_period=period, prephaser_duration=t_pre, t_k0=t_k0, read=read, adc=adc, n_samples=N, extra=extra,
                k0_index_even=c, k0_index_odd=k0_odd)

def rf_center_time(rf):
    """Time from the start of the block containing rf to the RF centre (s)."""
    return rf.delay + pp.calc_rf_center(rf)[0]

def adc_sample_time(adc, index):
    """Time from the start of the ADC's block to the centre of sample 'index' (Pulseq convention)."""
    return adc.delay + (index + 0.5) * adc.dwell

def fill_delay(target_s, elapsed_s, raster=1e-5, what='interval'):
    """Delay to insert so an interval equals target_s exactly on the block raster.
    Raises instead of silently returning the minimum achievable interval."""
    d = round((target_s - elapsed_s) / raster) * raster
    if d < -1e-12:
        raise ValueError(f'{what}: requested {target_s*1e3:.3f} ms but blocks already take {elapsed_s*1e3:.3f} ms')
    return max(d, 0.0)

def split_interval(interval_s, fixed_s, system):
    """Hit an RF-centre -> event interval (TE, TI, TR, ESP/2) to within the RF raster when the gap is not a multiple of
    the block raster. fixed_s = the interval the blocks give with zero delay and an unshifted excitation built by
    slice_selective_excitation. Returns (delay_s, center_shift_s): add a delay block of delay_s and rebuild that
    excitation with center_shift=center_shift_s (the RF moves later by the shift and the block grows by one raster,
    so the interval grows by raster - shift). fill_delay alone rounds to the block raster, which can leave the
    interval up to half a raster (5 us) off: often outside a task tolerance."""
    r = system.block_duration_raster; fr = system.rf_raster_time
    wanted = interval_s - fixed_s
    if wanted < -1e-12:
        raise ValueError(f'interval {interval_s*1e3:.4f} ms is shorter than the blocks ({fixed_s*1e3:.4f} ms)')
    d = np.floor(wanted / r + 1e-9) * r; frac = wanted - d
    shift = round((r - frac) / fr) * fr
    if frac < fr / 2 or shift >= r - 1e-12:
        return float(max(d, 0.0)), 0.0
    return float(d), float(shift)

class RFSpoiler:
    """Quadratic RF spoiling. next() returns the phase (rad) for this TR; set it on the RF AND its ADCs.
    Increment and phase are wrapped every update so the exported text keeps full precision."""
    def __init__(self, increment_deg=117.0):
        self.step, self.inc, self.phase = increment_deg, 0.0, 0.0
    def next(self):
        p = self.phase
        self.inc = (self.inc + self.step) % 360.0
        self.phase = (self.phase + self.inc) % 360.0
        return np.deg2rad(p)

def spoiler_area(cycles, length_m):
    """Gradient area (cycles/m) giving 'cycles' of phase across length_m (voxel or slice)."""
    return cycles / length_m

def simulate_with_koma(seq_file, x, y, z, rho, T1, T2, T2s=None, B0_Hz=None, rf_step_s=5e-6, dt_s=1e-5,
                       gmax_T_m=0.032, smax_T_m_s=130.0, backend='komamripy', julia=None, julia_project=None):
    """Bloch-simulate an exported .seq with KomaMRI. Inputs are flat arrays (m, s, Hz). Zero-density spins are dropped.
    Returns dict with
      samples  complex (n_adc_events, n_samples) in chronological ADC order (ADC phase offsets applied); KomaMRI with
               pypulseq's k gives samples = sum(rho * exp(-2 pi i k.r)): deliver them as they are (never conjugate,
               rescale or reorder; reconstruct with exp(+2 pi i k.r)),
      k        (n_adc_events, n_samples, 3) cycles/m from pypulseq calculate_kspace,
      t        (n_adc_events, n_samples) absolute ADC sample times (s).
    backend='komamripy' (pip install komamripy; the first call installs Julia + KomaMRI, several minutes: start it
    early). backend='julia' runs scripts/koma_sim.jl with a Julia you installed (julia: executable, julia_project:
    folder with KomaMRICore + KomaMRIFiles, e.g. from scripts/setup_koma_julia.sh; or MRFOUNDRY_JULIA and
    MRFOUNDRY_KOMA_PROJECT); both backends give the same signal (tested).
    Each spin is a point isochromat: gradient spoiling cannot dephase within a voxel."""
    x, y, z, rho, T1, T2 = map(lambda a: np.asarray(a, float).ravel(), (x, y, z, rho, T1, T2))
    T2s = T2 if T2s is None else np.asarray(T2s, float).ravel()
    dw = np.zeros_like(x) if B0_Hz is None else 2 * np.pi * np.asarray(B0_Hz, float).ravel()
    m = rho > 0
    if backend == 'julia':
        raw = _koma_julia(seq_file, [x[m], y[m], z[m], rho[m], T1[m], T2[m], T2s[m], dw[m]], rf_step_s, dt_s,
                          gmax_T_m, smax_T_m_s, julia, julia_project)
    else:
        import komamripy as km
        obj = km.Phantom(name='object', x=x[m], y=y[m], z=z[m], ρ=rho[m], T1=T1[m], T2=T2[m], T2s=T2s[m], Δw=dw[m])
        scanner = km.Scanner(limits=km.HardwareLimits(Gmax=gmax_T_m, Smax=smax_T_m_s))
        params = {'return_type': 'mat', 'gpu': False, 'precision': 'f64', 'Δt_rf': rf_step_s, 'Δt': dt_s}
        raw = np.asarray(km.simulate(obj, km.files.read_seq(str(seq_file)), scanner, sim_params=params)).copy().ravel()
    s = pp.Sequence(); s.read(str(seq_file)); k, _, _, _, ta = s.calculate_kspace()
    ns = [s.get_block(i).adc.num_samples for i in s.block_events if s.get_block(i).adc is not None]
    assert len(set(ns)) == 1 and raw.size == sum(ns), 'unequal ADC lengths: reshape per event yourself'
    n = ns[0]
    return {'samples': raw.reshape(len(ns), n), 'k': np.asarray(k).T.reshape(len(ns), n, 3), 't': np.asarray(ta).reshape(len(ns), n)}

def _koma_julia(seq_file, arrays, rf_step_s, dt_s, gmax, smax, julia=None, project=None):
    """Run koma_sim.jl in a subprocess: phantom as raw float64 (n, then 8 arrays), signal back as raw complex128."""
    import os, subprocess, tempfile, shutil
    julia = julia or os.environ.get('MRFOUNDRY_JULIA') or shutil.which('julia')
    project = project or os.environ.get('MRFOUNDRY_KOMA_PROJECT')
    if not julia or not project:
        raise RuntimeError('backend=julia needs julia= (or MRFOUNDRY_JULIA) and julia_project= (or MRFOUNDRY_KOMA_PROJECT)')
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'koma_sim.jl')
    with tempfile.TemporaryDirectory(dir='.') as d:
        fin, fout = os.path.join(d, 'phantom.bin'), os.path.join(d, 'signal.bin')
        with open(fin, 'wb') as f:
            np.array([arrays[0].size], np.int64).tofile(f)
            for a in arrays: np.ascontiguousarray(a, np.float64).tofile(f)
        cmd = [julia, f'--project={project}', script, str(seq_file), fin, fout, repr(dt_s), repr(rf_step_s), repr(gmax), repr(smax)]
        env = dict(os.environ)
        depot = os.path.join(os.path.dirname(os.path.abspath(project)), 'depot')
        if 'JULIA_DEPOT_PATH' not in env and os.path.isdir(depot): env['JULIA_DEPOT_PATH'] = depot   # setup_koma_julia.sh layout
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if r.returncode != 0:
            raise RuntimeError('koma_sim.jl failed: ' + (r.stderr or r.stdout)[-2000:])
        return np.fromfile(fout, np.complex128)

def relative_difference_up_to_phase(a, b):
    """Relative difference ||a e^{i phi} - b|| / ||b|| at the constant phase phi that minimizes it: compares a
    delivered simulated signal (a) with a fresh simulation of the same exported file (b) while ignoring a constant
    receiver phase. Shapes must match."""
    a = np.asarray(a, complex).ravel(); b = np.asarray(b, complex).ravel()
    if a.shape != b.shape:
        raise ValueError(f'shapes differ: {a.shape} vs {b.shape} (number of ADC events, their order or their length)')
    phi = np.angle(np.vdot(a, b))                         # minimizing phase (0 when a and b are orthogonal)
    return float(np.linalg.norm(a * np.exp(1j * phi) - b) / np.linalg.norm(b))

def replay_check(seq_file, delivered, x, y, z, rho, T1, T2, T2s=None, B0_Hz=None, tol=0.01, post=None, **kw):
    """Self-check before delivering: re-simulate the exported file with KomaMRI from scratch and compare.
    delivered: the raw signal you deliver (n_adc, n_samples), chronological. post: optional function applied to the
    fresh samples exactly as your pipeline does after simulation (a weighting of the whole object); it must not
    conjugate, rescale, reorder or demodulate again. A signal combined from several simulations (for example one per
    tissue, each weighted) is checked the same way: simulate each part with simulate_with_koma from scratch, combine as
    your pipeline does and compare with relative_difference_up_to_phase. Prints and returns that difference (a constant
    phase removed); raises if it exceeds tol. Catches simulating another file, MRzero or homemade output, conjugation,
    Julia column-major reshapes, dropped spins and scale changes."""
    fresh = simulate_with_koma(seq_file, x, y, z, rho, T1, T2, T2s=T2s, B0_Hz=B0_Hz, **kw)['samples']
    if post is not None:
        fresh = post(fresh)
    d = relative_difference_up_to_phase(delivered, fresh)
    print(f"replay check: difference to a fresh KomaMRI simulation {d:.2e}, constant phase removed ({'PASS' if d <= tol else 'FAIL'}, tol {tol:g})")
    if d > tol:
        raise AssertionError(f'delivered signal differs from a KomaMRI replay of {seq_file} by {d:.3g}')
    return d


def kspace_grid(samples, k, fov_m, n, group=None, drop_off_grid=False):
    """Place simulated samples on a Cartesian grid using the EXPORTED trajectory (not the build script).
    samples, k: per-ADC arrays from simulate_with_koma ((n_adc, ns) and (n_adc, ns, 3), cycles/m).
    n: (ny, nx). group: optional int per ADC (echo index, TI index, ...). Returns (n_groups, ny, nx) with
    grid[g, j, i] = sample at ky = (j - ny//2)/fov, kx = (i - nx//2)/fov; raises if a sample is off-grid,
    duplicated or missing, so line order and readout polarity are handled automatically.
    drop_off_grid=True (oversampled or extended readouts): samples between grid points or outside the matrix are
    ignored; every grid point must still be sampled exactly once per group. ADC events whose ky is not on the grid
    (navigators) must be removed before the call."""
    ny, nx = n; fx, fy = (fov_m, fov_m) if np.isscalar(fov_m) else fov_m
    group = np.zeros(len(samples), int) if group is None else np.asarray(group, int)
    G = group.max() + 1; out = np.zeros((G, ny, nx), complex); seen = np.zeros((G, ny, nx), int)
    for a in range(len(samples)):
        ix = np.asarray(k[a])[:, 0] * fx + nx // 2; iy = np.asarray(k[a])[:, 1] * fy + ny // 2
        ri, rj = np.rint(ix).astype(int), np.rint(iy).astype(int)
        ok = (abs(ix - ri) <= 1e-3) & (abs(iy - rj) <= 1e-3) & (ri >= 0) & (ri < nx) & (rj >= 0) & (rj < ny)
        if not drop_off_grid and not ok.all():
            raise ValueError(f'ADC {a}: samples are not on the Cartesian grid (check prephaser area, dwell, FOV; '
                             f'oversampled or extended readouts need drop_off_grid=True)')
        sa = np.asarray(samples[a])
        out[group[a], rj[ok], ri[ok]] = sa[ok]; np.add.at(seen[group[a]], (rj[ok], ri[ok]), 1)
    if seen.max() > 1 or seen.min() < 1:
        raise ValueError(f'grid coverage: duplicated {int((seen > 1).sum())}, missing {int((seen < 1).sum())} samples')
    return out

def plot_waveforms(seq_file, png, t_window=None):
    """Plot RF magnitude/phase, Gx/Gy/Gz and ADC sampling times read back from an exported .seq (headless)."""
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    s = pp.Sequence(); s.read(str(seq_file)); w = list(s.waveforms())[:3]; t = 0.; rf_t, rf_a, adc_t = [], [], []
    for i in s.block_events:
        b = s.get_block(i)
        if b.rf is not None: rf_t.append(t + b.rf.delay + np.asarray(b.rf.t)); rf_a.append(np.asarray(b.rf.signal) * np.exp(1j * b.rf.phase_offset))
        if b.adc is not None: adc_t.append(t + b.adc.delay + (np.arange(b.adc.num_samples) + .5) * b.adc.dwell)
        t += pp.calc_duration(b)
    t0, t1 = t_window or (0, t)
    fig, ax = plt.subplots(5, 1, sharex=True, figsize=(10, 8))
    for x, a in zip(rf_t, rf_a):
        m = (x >= t0) & (x <= t1); ax[0].plot(x[m] * 1e3, abs(a[m]), 'k'); ax[1].plot(x[m] * 1e3, np.angle(a[m]), 'k.', ms=1)
    for x in adc_t:
        m = (x >= t0) & (x <= t1); ax[0].plot(x[m] * 1e3, np.zeros(m.sum()), 'r|', ms=4)
    for j, name in enumerate(['Gx', 'Gy', 'Gz']):
        if j < len(w) and len(w[j][0]): m = (w[j][0] >= t0) & (w[j][0] <= t1); ax[j + 2].plot(w[j][0][m] * 1e3, w[j][1][m] / 42.576e6 * 1e3)
        ax[j + 2].set_ylabel(name + ' mT/m')
    ax[0].set_ylabel('|RF| Hz, ADC red'); ax[1].set_ylabel('RF phase'); ax[-1].set_xlabel('time (ms)')
    fig.tight_layout(); fig.savefig(png, dpi=110); plt.close(fig); return png


