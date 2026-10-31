"""MRFoundry sequence helpers: small, tested building blocks for PyPulseq + KomaMRI work.

Tested with pypulseq 1.5.0.post1, komamripy 0.0.11 (KomaMRI 0.13-0.14), numpy 2.x.
Copy the functions you need into your own script, or import this file. Each helper
encodes a convention that is easy to get wrong; read its docstring.
"""
import numpy as np
import pypulseq as pp

def make_system(max_grad_mT_m=32, max_slew_T_m_s=130, rf_dead_time=100e-6, rf_ringdown_time=20e-6,
                adc_dead_time=10e-6, grad_raster=10e-6, rf_raster=1e-6, adc_raster=1e-7, block_raster=10e-6):
    """pp.Opts with explicit units (mT/m, T/m/s, seconds)."""
    return pp.Opts(max_grad=max_grad_mT_m, grad_unit='mT/m', max_slew=max_slew_T_m_s, slew_unit='T/m/s',
                   rf_dead_time=rf_dead_time, rf_ringdown_time=rf_ringdown_time, adc_dead_time=adc_dead_time,
                   grad_raster_time=grad_raster, rf_raster_time=rf_raster, adc_raster_time=adc_raster,
                   block_duration_raster=block_raster)

def slice_selective_excitation(system, flip_deg, slice_thickness_m, duration=2e-3, tbw=4, apodization=0.5):
    """Sinc pulse played WITH its slice-select gradient: seq.add_block(rf, gz).
    Returns (rf, gz, rephase_area); play a z trapezoid of rephase_area (cycles/m) after it.
    A short hard (block) pulse is non-selective and is wrong for a 2D slice prescription."""
    rf, gz, gzr = pp.make_sinc_pulse(np.deg2rad(flip_deg), duration=duration, slice_thickness=slice_thickness_m,
                                     apodization=apodization, time_bw_product=tbw, system=system, return_gz=True,
                                     delay=system.rf_dead_time, use='excitation')
    return rf, gz, gzr.area

def centered_readout(system, n, fov_m, dwell_s, axis='x', center_index=None):
    """Readout trapezoid + ADC with sample i at k = (i - center_index)/fov (default center_index = n//2).
    Play a prephaser of area pre_area on the same axis before the readout block.
    Choose dwell_s on the ADC raster (n*dwell_s becomes the flat time)."""
    c = n // 2 if center_index is None else center_index
    read = pp.make_trapezoid(axis, flat_area=n / fov_m, flat_time=n * dwell_s, system=system)
    adc = pp.make_adc(n, dwell=dwell_s, delay=read.rise_time, system=system)
    pre_area = -(read.area - read.flat_area) / 2 - (c + 0.5) / fov_m
    return read, adc, pre_area

def add_epi_readout(seq, system, nx, ny, fov_m, dwell_s, extra_blocks=(), read_axis='x', blip_axis='y', fov_y=None):
    """Single-shot EPI train: prephaser block (plus any extra_blocks events, e.g. the slice rephaser) then ny lines
    of alternating readout polarity, ADC on the flat top only (no ramp sampling), phase-encode blips during the
    ramp-down. Chronological sample s of an even line j sits at kx = (s - nx//2)/fov, of an odd line at
    kx = (nx//2 - 1 - s)/fov (the same grid traversed backwards); line j sits at ky = (j - ny//2)/fov_y.
    The line period is constant. Returns timing: line_period, prephaser_duration and t_k0 = time from the start
    of the prephaser block to the sample at kx = ky = 0 (TE = excitation centre -> that sample).
    Verify the export with check_exported_seq.py --epi --matrix nx ny --fov F --te TE --echo-spacing ES."""
    fov_y = fov_m if fov_y is None else fov_y
    blip = pp.make_trapezoid(blip_axis, area=1.0 / fov_y, system=system)
    ramp = max(np.ceil(pp.calc_duration(blip) / system.grad_raster_time - 1e-9) * system.grad_raster_time, 0)
    read0, adc, _ = centered_readout(system, nx, fov_m, dwell_s, axis=read_axis)
    ramp = max(ramp, read0.rise_time)
    read = pp.make_trapezoid(read_axis, flat_area=nx / fov_m, flat_time=nx * dwell_s, rise_time=ramp, fall_time=ramp, system=system)
    adc = pp.make_adc(nx, dwell=dwell_s, delay=read.rise_time, system=system)
    pre_area = -(read.area - read.flat_area) / 2 - (nx // 2 + 0.5) / fov_m
    gx_pre = pp.make_trapezoid(read_axis, area=pre_area, system=system)
    gy_pre = pp.make_trapezoid(blip_axis, area=-(ny // 2) / fov_y, system=system)
    pre_events = [gx_pre, gy_pre] + list(extra_blocks)
    seq.add_block(*pre_events); t_pre = pp.calc_duration(*pre_events)
    blip.delay = read.rise_time + read.flat_time
    neg = pp.scale_grad(read, -1)
    for j in range(ny):
        g = read if j % 2 == 0 else neg
        if j < ny - 1:
            seq.add_block(g, adc, blip)
        else:
            seq.add_block(g, adc)
    period = pp.calc_duration(read)
    t_k0 = t_pre + (ny // 2) * period + adc_sample_time(adc, nx // 2 if (ny // 2) % 2 == 0 else nx // 2 - 1)
    return dict(line_period=period, prephaser_duration=t_pre, t_k0=t_k0, read=read, adc=adc)

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
                       gmax_T_m=0.032, smax_T_m_s=130.0):
    """Bloch-simulate an exported .seq with KomaMRI through komamripy.
    Inputs are flat arrays (m, s). Zero-density spins are dropped. Returns dict with
      samples  complex (n_adc_events, n_samples) in chronological ADC order (ADC phase offsets applied),
      k        (n_adc_events, n_samples, 3) cycles/m from pypulseq calculate_kspace,
      t        (n_adc_events, n_samples) absolute ADC sample times (s).
    First call installs/compiles Julia + KomaMRI (several minutes): start it early in the background.
    Set PYTHON_JULIACALL_HANDLE_SIGNALS=yes and JULIA_NUM_THREADS before importing komamripy.
    Each spin is a point isochromat: gradient spoiling cannot dephase within a voxel."""
    import komamripy as km
    x, y, z, rho, T1, T2 = map(lambda a: np.asarray(a, float).ravel(), (x, y, z, rho, T1, T2))
    T2s = T2 if T2s is None else np.asarray(T2s, float).ravel()
    dw = np.zeros_like(x) if B0_Hz is None else 2 * np.pi * np.asarray(B0_Hz, float).ravel()
    m = rho > 0
    obj = km.Phantom(name='object', x=x[m], y=y[m], z=z[m], ρ=rho[m], T1=T1[m], T2=T2[m], T2s=T2s[m], Δw=dw[m])
    scanner = km.Scanner(limits=km.HardwareLimits(Gmax=gmax_T_m, Smax=smax_T_m_s))
    params = {'return_type': 'mat', 'gpu': False, 'precision': 'f64', 'Δt_rf': rf_step_s, 'Δt': dt_s}
    raw = np.asarray(km.simulate(obj, km.files.read_seq(str(seq_file)), scanner, sim_params=params)).copy().ravel()
    s = pp.Sequence(); s.read(str(seq_file)); k, _, _, _, ta = s.calculate_kspace()
    ns = [s.get_block(i).adc.num_samples for i in s.block_events if s.get_block(i).adc is not None]
    assert len(set(ns)) == 1 and raw.size == sum(ns), 'unequal ADC lengths: reshape per event yourself'
    n = ns[0]
    return {'samples': raw.reshape(len(ns), n), 'k': np.asarray(k).T.reshape(len(ns), n, 3), 't': np.asarray(ta).reshape(len(ns), n)}


def kspace_grid(samples, k, fov_m, n, group=None):
    """Place simulated samples on a Cartesian grid using the EXPORTED trajectory (not the build script).
    samples, k: per-ADC arrays from simulate_with_koma ((n_adc, ns) and (n_adc, ns, 3), cycles/m).
    n: (ny, nx). group: optional int per ADC (echo index, TI index, ...). Returns (n_groups, ny, nx) with
    grid[g, j, i] = sample at ky = (j - ny//2)/fov, kx = (i - nx//2)/fov; raises if a sample is off-grid,
    duplicated or missing, so line order and readout polarity are handled automatically."""
    ny, nx = n; fx, fy = (fov_m, fov_m) if np.isscalar(fov_m) else fov_m
    group = np.zeros(len(samples), int) if group is None else np.asarray(group, int)
    G = group.max() + 1; out = np.zeros((G, ny, nx), complex); seen = np.zeros((G, ny, nx), int)
    for a in range(len(samples)):
        ix = np.asarray(k[a])[:, 0] * fx + nx // 2; iy = np.asarray(k[a])[:, 1] * fy + ny // 2
        ri, rj = np.rint(ix).astype(int), np.rint(iy).astype(int)
        if np.max(abs(ix - ri)) > 1e-3 or np.max(abs(iy - rj)) > 1e-3 or ri.min() < 0 or ri.max() >= nx or rj.min() < 0 or rj.max() >= ny:
            raise ValueError(f'ADC {a}: samples are not on the Cartesian grid (check prephaser area, dwell, FOV)')
        out[group[a], rj, ri] = samples[a]; seen[group[a], rj, ri] += 1
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


def _print_api(namespace):
    """Signatures and one-line summaries of the public functions (python <module>.py --api)."""
    import inspect
    for name, f in sorted(namespace.items()):
        if inspect.isfunction(f) and not name.startswith('_') and f.__module__ == '__main__':
            doc = ((inspect.getdoc(f) or '').splitlines() or [''])[0]
            print(f"{name}{inspect.signature(f)}" + chr(10) + f"    {doc}")


if __name__ == '__main__' and '--api' in __import__('sys').argv:
    _print_api(dict(globals()))
