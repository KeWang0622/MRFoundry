"""Tests for check_exported_seq (python test_check_exported_seq.py, about 10 s, no simulator needed).

Each builder writes a small example of one sequence family with pypulseq; the test checks that the
measurements are right and that each deliberately broken variant FAILS the intended check.
The builders are compact family examples (spoiled GRE in test_seqlib.py; inversion-recovery GRE,
balanced SSFP and spin echo here); adapt them, then run check_exported_seq.py on your own export.
"""
import os, sys, tempfile
import numpy as np, pypulseq as pp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mrfoundry_seqlib import make_system, slice_selective_excitation, centered_readout, rf_center_time, adc_sample_time, fill_delay, RFSpoiler, spoiler_area
from check_exported_seq import measure
from test_seqlib import cartesian_gre

def ir_gre(path, n=16, fov=0.2, tis=(0.05, 0.4), te=5e-3, period=1.0, flip=20, sl=5e-3, dwell=40e-6, ti_from_block_start=False, inversion_spoiler=True):
    """Inversion-recovery spoiled GRE, one phase-encode line per inversion; TI = inversion centre -> excitation centre."""
    sysm = make_system(); seq = pp.Sequence(sysm)
    inv = pp.make_block_pulse(np.pi, duration=1e-3, delay=sysm.rf_dead_time, system=sysm, use='inversion')
    rf, gz, reph = slice_selective_excitation(sysm, flip, sl); read, adc, pre = centered_readout(sysm, n, fov, dwell)
    spz = pp.make_trapezoid('z', area=spoiler_area(4, sl), duration=2e-3, system=sysm)
    exc = pp.calc_duration(rf, gz); tpre = 1e-3; dinv = pp.calc_duration(inv)
    for ti in tis:
        for j in range(n):
            ky = (j - n // 2) / fov; t_used = 0.
            seq.add_block(inv); t_used += dinv
            if inversion_spoiler: seq.add_block(spz); t_used += pp.calc_duration(spz)
            if ti_from_block_start: d = fill_delay(ti, t_used, what='TI')          # wrong: ignores RF centres
            else: d = fill_delay(ti, (dinv - rf_center_time(inv)) + (t_used - dinv) + rf_center_time(rf), what='TI')
            if d > 0: seq.add_block(pp.make_delay(d))
            t_used += d
            seq.add_block(rf, gz)
            gx = pp.make_trapezoid('x', area=pre, duration=tpre, system=sysm); gy = pp.make_trapezoid('y', area=ky, duration=tpre, system=sysm)
            gzr = pp.make_trapezoid('z', area=reph, duration=tpre, system=sysm); seq.add_block(gx, gy, gzr)
            d2 = fill_delay(te, (exc - rf_center_time(rf)) + tpre + adc_sample_time(adc, n // 2), what='TE')
            if d2 > 0: seq.add_block(pp.make_delay(d2))
            seq.add_block(read, adc)
            used = t_used + exc + tpre + d2 + pp.calc_duration(read, adc)
            seq.add_block(spz, pp.make_trapezoid('y', area=-ky, duration=2e-3, system=sysm), pp.make_delay(fill_delay(period, used, what='inversion period')))
    ok, err = seq.check_timing(); assert ok, err[:2]; seq.write(path); return path

def bssfp(path, n=16, fov=0.2, tr=8e-3, flip=40, sl=5e-3, dwell=20e-6, dummies=20, balanced=True, alternate=True, adc_follows_rf=True):
    """2D balanced SSFP: zero net area per TR on x, y, z; TE = TR/2; 0/180 RF phase cycling with matching ADC phase."""
    sysm = make_system(); seq = pp.Sequence(sysm)
    rf, gz, reph = slice_selective_excitation(sysm, flip, sl, duration=1e-3, tbw=2); read, adc, pre = centered_readout(sysm, n, fov, dwell)
    exc = pp.calc_duration(rf, gz); tpre = 6e-4; te = tr / 2
    for i, j in enumerate([None] * dummies + list(range(n))):
        ky = 0.0 if j is None else (j - n // 2) / fov; ph = np.pi * (i % 2) if alternate else 0.0
        rf.phase_offset = ph; adc.phase_offset = ph if adc_follows_rf else 0.0
        seq.add_block(rf, gz)
        seq.add_block(pp.make_trapezoid('x', area=pre, duration=tpre, system=sysm), pp.make_trapezoid('y', area=ky, duration=tpre, system=sysm),
                      pp.make_trapezoid('z', area=reph, duration=tpre, system=sysm))
        d1 = fill_delay(te, (exc - rf_center_time(rf)) + tpre + adc_sample_time(adc, n // 2), what='TE')
        if d1 > 0: seq.add_block(pp.make_delay(d1))
        seq.add_block(read, adc) if j is not None else seq.add_block(read)
        rew = [pp.make_trapezoid('x', area=-(pre + read.area), duration=tpre, system=sysm), pp.make_trapezoid('y', area=-ky, duration=tpre, system=sysm)]
        if balanced: rew.append(pp.make_trapezoid('z', area=reph, duration=tpre, system=sysm))
        used = exc + tpre + d1 + pp.calc_duration(read) + tpre
        seq.add_block(*rew); d2 = fill_delay(tr, used, what='TR')
        if d2 > 0: seq.add_block(pp.make_delay(d2))
    ok, err = seq.check_timing(); assert ok, err[:2]; seq.write(path); return path

def spin_echo(path, n=16, fov=0.2, te=30e-3, tr=0.3, sl=5e-3, dwell=40e-6, cpmg=True):
    """2D spin echo: 90 (phase 0) -> crushed slice-selective 180 at TE/2 (phase 90 for CPMG) -> echo at TE."""
    sysm = make_system(); seq = pp.Sequence(sysm)
    rf, gz, reph = slice_selective_excitation(sysm, 90, sl)
    rf180, gz180, _ = pp.make_sinc_pulse(np.pi, duration=2e-3, slice_thickness=sl, apodization=.5, time_bw_product=4, system=sysm,
                                        return_gz=True, delay=sysm.rf_dead_time, use='refocusing', phase_offset=np.pi / 2 if cpmg else 0.0)
    read, adc, pre = centered_readout(sysm, n, fov, dwell); crush = pp.make_trapezoid('z', area=spoiler_area(2, sl), duration=1e-3, system=sysm)
    exc = pp.calc_duration(rf, gz); tpre = 1e-3; dref = pp.calc_duration(rf180, gz180)
    for j in range(n):
        ky = (j - n // 2) / fov
        seq.add_block(rf, gz); seq.add_block(pp.make_trapezoid('z', area=reph, duration=tpre, system=sysm))
        d1 = fill_delay(te / 2, (exc - rf_center_time(rf)) + tpre + pp.calc_duration(crush) + rf_center_time(rf180), what='TE/2')
        if d1 > 0: seq.add_block(pp.make_delay(d1))
        seq.add_block(crush); seq.add_block(rf180, gz180); seq.add_block(crush)
        seq.add_block(pp.make_trapezoid('x', area=pre, duration=tpre, system=sysm), pp.make_trapezoid('y', area=ky, duration=tpre, system=sysm))
        d2 = fill_delay(te / 2, (dref - rf_center_time(rf180)) + pp.calc_duration(crush) + tpre + adc_sample_time(adc, n // 2), what='TE/2 after refocusing')
        if d2 > 0: seq.add_block(pp.make_delay(d2))
        seq.add_block(read, adc)
        used = exc + tpre + d1 + 2 * pp.calc_duration(crush) + dref + tpre + d2 + pp.calc_duration(read, adc)
        seq.add_block(pp.make_trapezoid('z', area=spoiler_area(4, sl), duration=2e-3, system=sysm), pp.make_delay(fill_delay(tr, used, what='TR')))
    ok, err = seq.check_timing(); assert ok, err[:2]; seq.write(path); return path

def failed(checks): return [c['item'] for c in checks if not c['pass']]


def cpmg(path, n_echo=8, esp=12e-3, crusher_area=1000.0, rf_dur=0.5e-3, crusher_dur=1.6e-3, ramp=None, n_samples=16, dwell=20e-6):
    """Non-selective CPMG: hard 90 (phase 0), n_echo hard 180s (phase 90) at ESP/2 + (n-1) ESP, one ADC centred on
    each echo, equal z crushers (area in cycles/m) on both sides of every refocusing pulse."""
    sysm = make_system(); seq = pp.Sequence(sysm)
    ex = pp.make_block_pulse(np.pi / 2, duration=rf_dur, delay=sysm.rf_dead_time, system=sysm, use='excitation')
    rf = pp.make_block_pulse(np.pi, duration=rf_dur, delay=sysm.rf_dead_time, phase_offset=np.pi / 2, system=sysm, use='refocusing')
    kw = dict(rise_time=ramp, fall_time=ramp) if ramp else {}
    cr = pp.make_trapezoid('z', area=crusher_area, duration=crusher_dur, system=sysm, **kw)
    adc = pp.make_adc(n_samples, dwell=dwell, delay=sysm.adc_dead_time, system=sysm)
    seq.add_block(ex)
    t_exc_c = rf_center_time(ex); dex = pp.calc_duration(ex); drf = pp.calc_duration(rf); c_rf = rf_center_time(rf)
    d1 = fill_delay(esp / 2, (dex - t_exc_c) + pp.calc_duration(cr) + c_rf, what='ESP/2')
    seq.add_block(pp.make_delay(d1))
    for k in range(n_echo):
        seq.add_block(cr); seq.add_block(rf); seq.add_block(cr)
        half = adc_sample_time(adc, n_samples // 2)
        d2 = fill_delay(esp / 2, (drf - c_rf) + pp.calc_duration(cr) + half, what='to echo')
        if d2 > 0: seq.add_block(pp.make_delay(d2))
        seq.add_block(adc)
        if k < n_echo - 1:
            d3 = fill_delay(esp / 2, (pp.calc_duration(adc) - half) + pp.calc_duration(cr) + c_rf, what='echo to next refocusing')
            if d3 > 0: seq.add_block(pp.make_delay(d3))
    seq.add_block(pp.make_delay(0.1))
    ok, err = seq.check_timing(); assert ok, err[:2]; seq.write(path); return path


def test_crushers_and_safety(P):
    g = 42.576e6
    rep, ch = measure(cpmg(P('cpmg.seq')), cpmg=True, crusher_range=(600, 1500), safety=True, pns_rheobase=60, pns_chronaxie=0.4e-3,
                      b1rms_max=5.0, grms_max=35, pns_max=0.9)
    assert not failed(ch), failed(ch)
    cm = rep['crusher_moment_cycles_m']
    assert all(abs(v - 1000) < 1 for v in cm['before_refocusing'] + cm['after_refocusing']) and cm['max_relative_mismatch'] < 1e-3, cm
    # analytic B1 rms: block pulses of amplitude flip/(2 pi gamma d)
    tot = rep['duration_s']; b90 = 0.25 / 0.5e-3 / g; b180 = 0.5 / 0.5e-3 / g
    b1rms = np.sqrt((b90 ** 2 + 8 * b180 ** 2) * 0.5e-3 / tot) * 1e6
    assert abs(rep['b1_rms_whole_file_uT'] - b1rms) < 1e-3 * b1rms and abs(rep['b1_peak_whole_file_uT'] - b180 * 1e6) < 1e-6, (rep['b1_rms_whole_file_uT'], b1rms)
    # analytic ramp PNS fraction of the crusher trapezoid: P = dG / (rheobase (rise time + chronaxie))
    import pypulseq as pp_
    cr = pp_.make_trapezoid("z", area=1000.0, duration=1.6e-3, system=make_system())
    p_exp = cr.amplitude / g / (60 * (cr.rise_time + 0.4e-3))
    assert abs(max(rep['pns_max_fraction_per_axis']) - p_exp) < 1e-4, (rep['pns_max_fraction_per_axis'], p_exp)
    print('CPMG crushers %.1f cycles/m both sides; B1rms %.3f uT (analytic %.3f), peak %.2f uT; ramp PNS %.4f (analytic %.4f)'
          % (cm['before_refocusing'][0], rep['b1_rms_whole_file_uT'], b1rms, rep['b1_peak_whole_file_uT'], max(rep['pns_max_fraction_per_axis']), p_exp))
    # gradient passed in T/m where Pulseq expects Hz/m: moments near 1e-5 cycles/m
    rep, ch = measure(cpmg(P('cpmg_units.seq'), crusher_area=1000.0 / g), cpmg=True, crusher_range=(600, 1500))
    assert failed(ch) == [c['item'] for c in ch if c['item'].startswith('spin-echo crusher')], failed(ch)
    # designed exactly at the lower limit: flagged as a margin warning
    rep, ch = measure(cpmg(P('cpmg_edge.seq'), crusher_area=600.0), cpmg=True, crusher_range=(600, 1500))
    assert rep.get('margin_warnings'), rep.get('crusher_moment_cycles_m')
    print('crusher unit error (T/m given as Hz/m) FAILS; a design at the range edge gets a margin WARN')


def main():
    tmp = tempfile.mkdtemp(); P = lambda f: os.path.join(tmp, f)
    # spoiled GRE
    rep, ch = measure(cartesian_gre(P('gre.seq')), te=6e-3, tr=20e-3, flip=15, slice_thickness=5e-3, rf_spoil=117, min_spoil_cycles=2,
                      matrix=(32, 32), fov=0.2, monopolar=True, max_grad=32, max_slew=130)
    assert not failed(ch), failed(ch); assert rep['rf_roles'] == {'excitation': 42, 'inversion': 0, 'refocusing': 0}, rep['rf_roles']
    assert rep['excitations_before_first_adc'] == 10; print('spoiled GRE ok: TE', rep['te_ms'], 'TR', rep['tr_ms'], 'z spoil cyc/slice', round(rep['post_readout_z_spoiler_cycles_per_slice_min'], 2))
    # inversion recovery
    rep, ch = measure(ir_gre(P('ir.seq')), ti=[0.05, 0.4], te=5e-3, flip=20, slice_thickness=5e-3, min_inversion_spoil_cycles=2, min_spoil_cycles=2, matrix=(16, 16), fov=0.2)
    assert not failed(ch), failed(ch); assert rep['rf_roles']['inversion'] == 32 and rep['rf_roles']['excitation'] == 32, rep['rf_roles']
    print('IR-GRE ok: TI', rep['ti_ms'], 'inversion spoiler cyc/slice', round(rep['post_inversion_z_spoiler_cycles_per_slice_min'], 2))
    rep, ch = measure(ir_gre(P('ir_bad.seq'), ti_from_block_start=True, inversion_spoiler=False), ti=[0.05, 0.4], min_inversion_spoil_cycles=2, slice_thickness=5e-3)
    assert set(failed(ch)) == {'realized TI (inversion centre -> excitation centre) within 1 us', 'post-inversion z spoiler (cycles per slice)'}, failed(ch)
    # fallback role detection without rf.use
    path = ir_gre(P('ir_nouse.seq')); txt = open(path).read().replace(' i\n', ' u\n'); open(path, 'w').write(txt)
    rep, ch = measure(path, ti=[0.05, 0.4]); assert rep['rf_roles']['inversion'] == 32 and not failed(ch), (rep['rf_roles'], failed(ch))
    # balanced SSFP
    rep, ch = measure(bssfp(P('ssfp.seq')), tr=8e-3, flip=40, balanced=True, rf_phase_cycle=180, te_half_tr=True, matrix=(16, 16), fov=0.2, max_grad=32, max_slew=130)
    assert not failed(ch), failed(ch); print('bSSFP ok: net area/TR', rep['net_area_per_tr_cycles_m_max_abs'], 'TE', rep['te_ms'], 'TR', rep['tr_ms'], 'dummies', rep['excitations_before_first_adc'])
    rep, ch = measure(bssfp(P('ssfp_unbal.seq'), balanced=False), balanced=True); assert failed(ch) == ['balanced: zero net gradient area per TR on every axis'], failed(ch)
    rep, ch = measure(bssfp(P('ssfp_adc.seq'), adc_follows_rf=False), rf_phase_cycle=180); assert failed(ch) == ['ADC phase equals the phase of its own excitation'], failed(ch)
    rep, ch = measure(bssfp(P('ssfp_nocyc.seq'), alternate=False), rf_phase_cycle=180); assert 'RF phase cycling increment' in failed(ch), failed(ch)
    # CPMG crushers and safety quantities measured from the export
    test_crushers_and_safety(P)
    # spin echo
    rep, ch = measure(spin_echo(P('se.seq')), te=30e-3, tr=0.3, cpmg=True, slice_thickness=5e-3, matrix=(16, 16), fov=0.2)
    assert not failed(ch), failed(ch); assert rep['rf_roles']['refocusing'] == 16 and abs(rep['refocusing_after_excitation_ms'][0] - 15) < 1e-3, rep
    print('spin echo ok: TE', rep['te_ms'], 'refocusing at', rep['refocusing_after_excitation_ms'], 'ms, phase', rep['refocusing_minus_excitation_phase_deg'])
    rep, ch = measure(spin_echo(P('se_bad.seq'), cpmg=False), cpmg=True); assert failed(ch) == ['CPMG: refocusing phase = excitation phase +/- 90 deg'], failed(ch)
    print('all check_exported_seq tests passed')

if __name__ == '__main__':
    main()



# ---- B5/B7: single-shot EPI (add_epi_readout) and the EPI-aware checks ------------------------------------------
from mrfoundry_seqlib import add_epi_readout, split_interval, kspace_grid
def epi(path, n=16, fov=0.22, dwell=10e-6, te=0.02, odd_adc_shift=0.0, oversample=1, extra=0, exact_te=True):
    """Single-shot gradient-echo EPI. exact_te: split_interval puts the sub-raster remainder of TE into the RF delay;
    exact_te=False rounds the TE delay to the block raster only (legacy, up to 5 us off)."""
    sysm = make_system(); seq = pp.Sequence(sysm)
    rf, gz, reph = slice_selective_excitation(sysm, 90, 5e-3); gzr = pp.make_trapezoid('z', area=reph, system=sysm)
    probe = add_epi_readout(pp.Sequence(sysm), sysm, n, n, fov, dwell, extra_blocks=[gzr], oversample=oversample, extra=extra)
    fixed = (pp.calc_duration(rf, gz) - rf_center_time(rf)) + probe['t_k0']
    if exact_te:
        d, sh = split_interval(te, fixed, sysm)
        if sh:
            rf, gz, reph = slice_selective_excitation(sysm, 90, 5e-3, center_shift=sh); gzr = pp.make_trapezoid('z', area=reph, system=sysm)
    else:
        d = fill_delay(te, fixed, what='TE')
    seq.add_block(rf, gz)
    if d > 0: seq.add_block(pp.make_delay(d))
    if not odd_adc_shift:
        info = add_epi_readout(seq, sysm, n, n, fov, dwell, extra_blocks=[gzr], oversample=oversample, extra=extra)
    else:                                               # broken variant: ADC delayed on reversed lines only
        info = probe; read, adc = probe['read'], probe['adc']
        pre = -(read.area - read.flat_area) / 2 - (n // 2 + 0.5) / fov
        seq.add_block(pp.make_trapezoid('x', area=pre, system=sysm), pp.make_trapezoid('y', area=-(n // 2) / fov, system=sysm), gzr)
        blip = pp.make_trapezoid('y', area=1 / fov, system=sysm); blip.delay = read.rise_time + read.flat_time
        adc_odd = pp.make_adc(n, dwell=dwell, delay=adc.delay + odd_adc_shift, system=sysm)
        for j in range(n):
            ev = [read if j % 2 == 0 else pp.scale_grad(read, -1), adc if j % 2 == 0 else adc_odd]
            seq.add_block(*(ev + ([blip] if j < n - 1 else [])))
    ok, err = seq.check_timing(); assert ok, err[:2]; seq.write(path); return path, info


def seq_text_kx(path):
    """Independent forward calculation from the .seq TEXT (no pypulseq): integrate the exported trapezoids exactly
    from each RF centre and return kx (cycles/m) of each ADC sample; Pulseq places samples half a dwell after the ADC
    delay and one dwell apart.
    Handles the trapezoid/ADC/RF subset used by the EPI fixtures (RF centre = its delay + half its shape duration)."""
    sec = None; blocks = []; trap = {}; adc = {}; rf = {}; raster = 1e-5
    for line in open(path):
        line = line.split('#')[0].strip()
        if not line: continue
        if line.startswith('['): sec = line; continue
        f = line.split()
        if sec == '[DEFINITIONS]' and f[0] == 'BlockDurationRaster': raster = float(f[1])
        elif sec == '[BLOCKS]': blocks.append([int(v) for v in f])
        elif sec == '[TRAP]': trap[int(f[0])] = [float(v) for v in f[1:6]]          # amp Hz/m, rise, flat, fall, delay (us)
        elif sec == '[ADC]': adc[int(f[0])] = [float(v) for v in f[1:4]]            # num, dwell (ns), delay (us)
        elif sec == '[RF]': rf[int(f[0])] = f
    def area(tr, t):                                       # area of a trapezoid from its block start to time t (s)
        a, r, fl, fa, de = tr; r, fl, fa, de = r * 1e-6, fl * 1e-6, fa * 1e-6, de * 1e-6; u = t - de
        if u <= 0: return 0.0
        if u < r: return a * u * u / (2 * r)
        if u < r + fl: return a * (r / 2 + u - r)
        if u < r + fl + fa: v = u - r - fl; return a * (r / 2 + fl + v - v * v / (2 * fa))
        return a * (r / 2 + fl + fa / 2)
    k = 0.0; out = []
    for b in blocks:
        dur = b[1] * raster; gx = b[3]
        if b[2]:                                           # an RF pulse (no x gradient in these blocks): kx restarts
            k = 0.0
        samples = []
        if b[6]:
            num, dw, de = adc[b[6]]; samples = de * 1e-6 + (np.arange(int(num)) + 0.5) * dw * 1e-9
            out.append(np.array([k + (area(trap[gx], t) if gx else 0.0) for t in samples]))
        k += area(trap[gx], dur) if gx else 0.0
    return out


with tempfile.TemporaryDirectory() as d:
    p, info = epi(os.path.join(d, 'epi.seq'))
    rep, checks = measure(p, te=0.02, matrix=(16, 16), fov=0.22, epi=True, echo_spacing=info['line_period'] + 1e-9,
                          max_grad=32, max_slew=130, slice_thickness=5e-3)
    assert all(c['pass'] for c in checks), [c for c in checks if not c['pass']]
    assert len(rep['te_ms']) == 1 and abs(rep['te_ms'][0] - 20.0) < 1e-3, rep['te_ms']
    rep2, _ = measure(p, te=0.02, matrix=(16, 16), fov=0.22)
    assert len(rep2['te_ms']) == 16                     # without --epi every line counts as an echo
    print(f"EPI ok: TE {rep['te_ms']} ms at the kx = ky = 0 sample (split_interval), echo spacing {rep['echo_spacing_ms']} ms, kx grid exact on both parities")
    p0, _ = epi(os.path.join(d, 'epi_rounded.seq'), exact_te=False)
    rep0, ch0 = measure(p0, te=0.02, epi=True)
    assert [c['item'] for c in ch0 if not c['pass']] == ['realized TE (excitation centre -> k=0 sample) within 1 us'], ch0
    print(f"EPI with the TE delay rounded to the block raster: TE {rep0['te_ms']} ms FAILS the 1 us tolerance")
    p, info = epi(os.path.join(d, 'epi_bad.seq'), odd_adc_shift=10e-6)
    rep, checks = measure(p, te=0.02, matrix=(16, 16), fov=0.22, epi=True)
    kx = [c for c in checks if c['item'].startswith('Cartesian kx')][0]
    par = rep['kx_grid_max_err_by_line_parity']
    assert not kx['pass'] and par['even'] < 0.01 and par['odd'] > 1, par
    print(f"EPI with a mis-timed ADC on reversed lines: kx FAIL, error only on odd lines {par}")
    # B7: interval coverage. Exactly n samples put the end samples on the interval ends (knife edge): FAIL.
    n, fov = 20, 0.205
    pe, _ = epi(os.path.join(d, 'epi_exact.seq'), n=n, fov=fov, dwell=5e-6, te=0.027)
    rep, checks = measure(pe, te=0.027, matrix=(n, n), fov=fov, epi=True, kx_cover=(-n // 2, n - n // 2 - 1))
    cov = [c for c in checks if c['item'].startswith('readout coverage')][0]
    assert not cov['pass'], cov
    print('EPI with exactly n samples per line: coverage FAIL (margins %.2g/%.2g of 1/fov, gap %.6f)' % (
        rep['kx_coverage_units_of_1_over_fov']['min_margin_below_lo'], rep['kx_coverage_units_of_1_over_fov']['min_margin_above_hi'],
        rep['kx_coverage_units_of_1_over_fov']['max_gap']))
    po, info = epi(os.path.join(d, 'epi_os.seq'), n=n, fov=fov, dwell=2.5e-6, te=0.027, oversample=2, extra=1)
    rep, checks = measure(po, te=0.027, matrix=(n, n), fov=fov, epi=True, kx_cover=(-n // 2, n - n // 2 - 1), line_repeats=1, n_adc=n,
                          echo_spacing=info['line_period'] + 1e-9, max_grad=36, max_slew=140)
    assert all(c['pass'] for c in checks), [c for c in checks if not c['pass']]
    kc = rep['kx_coverage_units_of_1_over_fov']; assert kc['min_margin_below_lo'] > 0.4 and kc['min_margin_above_hi'] > 0.4 and kc['max_gap'] < 0.51, kc
    # independent forward calculation from the .seq text equals the documented grid on both parities
    N, c = info['n_samples'], info['k0_index_even']; u = np.arange(N)
    kx_txt = seq_text_kx(po); assert len(kx_txt) == n
    for j, kk in enumerate(kx_txt):
        want = (u - c) / (2 * fov) if j % 2 == 0 else (N - 1 - c - u) / (2 * fov)
        assert np.max(abs(kk - want)) < 2e-3, (j, np.max(abs(kk - want)))
    s_ = pp.Sequence(); s_.read(po); kpp = np.asarray(s_.calculate_kspace()[0]).T[:, 0].reshape(n, N)
    assert np.max(abs(kpp - np.array(kx_txt))) < 2e-3
    # kspace_grid keeps the samples on the 1/fov grid and drops the half-step and end samples
    kk3 = np.asarray(s_.calculate_kspace()[0]).T.reshape(n, N, 3); sig = np.exp(-2j * np.pi * (kk3[..., 0] * 0.013 - kk3[..., 1] * 0.021))
    gr = kspace_grid(sig, kk3, fov, (n, n), drop_off_grid=True)[0]
    img = np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(gr))); iy, ix = np.unravel_index(np.argmax(abs(img)), img.shape)
    assert abs((ix - n // 2) * fov / n - 0.013) <= fov / n / 2 + 1e-9 and abs((iy - n // 2) * fov / n + 0.021) <= fov / n / 2 + 1e-9, (ix, iy)
    print(f"EPI oversampled 2x with extra samples beyond each end: coverage PASS (margins {kc['min_margin_below_lo']:.2f}/{kc['min_margin_above_hi']:.2f} of 1/fov, "
          f"gap {kc['max_gap']:.3f}); .seq-text integration equals the documented grid on both parities; kspace_grid(drop_off_grid=True) places a point source")
print("all B5/B7 EPI checks passed")


# ---- B7: acquired-line bookkeeping and gradient continuity ------------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    rep, ch = measure(cartesian_gre(os.path.join(d, 'g.seq'), n=12, dummies=3), matrix=(12, 12), fov=0.2, line_repeats=1, n_adc=12)
    assert not failed(ch), failed(ch)
    assert rep['excitations_with_adc'] == 12 and rep['excitations_without_adc'] == 3, rep
    rep, ch = measure(cartesian_gre(os.path.join(d, 'g_dummy_adc.seq'), n=12, dummies=3, dummy_adc=True), matrix=(12, 12), fov=0.2, line_repeats=1, n_adc=12)
    assert set(failed(ch)) == {'every line acquired exactly 1 time(s) (an ADC in a dummy repetition adds an acquisition)', 'number of ADC events = 12'}, failed(ch)
    print('dummy repetitions with an ADC: line-count and ADC-count checks FAIL', rep['line_acquisitions'])
    sysm = make_system(); T = 0.8e-3; r = sysm.grad_raster_time; t = (np.arange(int(round(T / r))) + 0.5) * r
    for name, wave, kw, nbad in [('jump', 20e3 * np.cos(np.pi * t / (2 * T)), {}, 1),
                                 ('smooth', 20e3 * np.sin(np.pi * t / T), dict(first=0.0, last=0.0), 0)]:
        seq = pp.Sequence(sysm); seq.add_block(pp.make_delay(1e-3))
        g = pp.make_arbitrary_grad('x', wave, system=sysm, **kw); seq.add_block(g); seq.add_block(pp.make_delay(1e-3))
        p = os.path.join(d, name + '.seq'); seq.write(p)
        rep, ch = measure(p, max_slew=140)
        jumps = rep['gradient_jumps_per_axis'][0]
        assert (jumps > 0) == (nbad > 0), (name, rep['gradient_jumps_per_axis'], rep['gradient_jump_examples'])
    print('arbitrary gradient starting at a nonzero value: continuity FAIL; first=0/last=0 with a waveform that starts and ends at 0: PASS')
print("all B7 sequence checks passed")


# ---- B7: centered_readout with adc_shift (sub-raster TE) and an oversampled, extended single-line readout --------
def gre_line(path, n=14, fov=0.23, dwell=16e-6, te=5.0037e-3, oversample=1, extra=0, shift=True):
    sysm = make_system(); seq = pp.Sequence(sysm); rf, gz, reph = slice_selective_excitation(sysm, 12, 5e-3)
    read0, adc0, _ = centered_readout(sysm, n, fov, dwell, oversample=oversample, extra=extra)
    c = extra + oversample * (n // 2); exc = pp.calc_duration(rf, gz); tpre = 1e-3
    fixed = (exc - rf_center_time(rf)) + tpre + adc_sample_time(adc0, c)
    d = fill_delay(te, fixed, what='TE'); sh = round((te - fixed - d) / 1e-6) * 1e-6 if shift else 0.0
    if sh < 0: d -= 1e-5; sh += 1e-5
    read, adc, pre = centered_readout(sysm, n, fov, dwell, oversample=oversample, extra=extra, adc_shift=sh)
    for j in range(n):
        seq.add_block(rf, gz)
        seq.add_block(pp.make_trapezoid('x', area=pre, duration=tpre, system=sysm), pp.make_trapezoid('y', area=(j - n // 2) / fov, duration=tpre, system=sysm),
                      pp.make_trapezoid('z', area=reph, duration=tpre, system=sysm))
        if d > 0: seq.add_block(pp.make_delay(d))
        seq.add_block(read, adc); seq.add_block(pp.make_delay(5e-3))
    ok, err = seq.check_timing(); assert ok, err[:2]; seq.write(path); return path

with tempfile.TemporaryDirectory() as d:
    rep, ch = measure(gre_line(os.path.join(d, 'a.seq')), te=5.0037e-3, matrix=(14, 14), fov=0.23, line_repeats=1)
    assert not failed(ch), failed(ch)
    rep, ch = measure(gre_line(os.path.join(d, 'b.seq'), shift=False), te=5.0037e-3)
    assert failed(ch) == ['realized TE (excitation centre -> k=0 sample) within 1 us'], failed(ch)
    rep, ch = measure(gre_line(os.path.join(d, 'c.seq'), dwell=10e-6, oversample=2, extra=1), te=5.0037e-3, matrix=(14, 14), fov=0.23,
                      kx_cover=(-7, 6), line_repeats=1)
    assert not failed(ch), failed(ch)
    print('centered_readout: adc_shift puts the k = 0 sample on a sub-raster TE (grid exact); oversampled extended line covers with margin',
          rep['kx_coverage_units_of_1_over_fov'])
print('all B7 readout checks passed')

with tempfile.TemporaryDirectory() as d:
    sysm = make_system(); seq = pp.Sequence(sysm)
    rf = pp.make_block_pulse(np.pi / 6, duration=0.3e-3, delay=sysm.rf_dead_time, system=sysm)
    for adc_delay in (sysm.adc_dead_time, 0.0):
        seq.add_block(rf); seq.add_block(pp.make_adc(40, dwell=6.5e-6, delay=adc_delay), pp.make_delay(0.3e-3))
    p = os.path.join(d, 'dead.seq'); seq.write(p)
    rep, ch = measure(p, rf_dead_time=sysm.rf_dead_time, rf_ringdown_time=sysm.rf_ringdown_time, adc_dead_time=sysm.adc_dead_time)
    dt = [c for c in ch if c['item'].startswith('RF and ADC events keep')][0]
    assert not dt['pass'] and dt['detail']['count'] == 1 and 'ADC delay' in dt['detail']['first'][0], dt
    print('ADC without its dead time after the block start: dead-time check FAIL', dt['detail']['first'])

# ---- B8: half-pulse excitation; the slice gradient must be on at the RF centre -----------------------------------
def half_pulse(path, on_plateau=True, ramp=1e-4, flat=4e-4, g=1e5):
    """Sinc truncated at its maximum, which is the RF centre. on_plateau=False: RF continues over the ramp-down (gradient 0 at centre)."""
    sysm = make_system(); seq = pp.Sequence(sysm); dt = sysm.rf_raster_time
    dur = flat if on_plateau else flat + ramp; n = int(round(dur / dt))
    t = (np.arange(n) + 0.5) * dt; gt = np.where(t < flat, g, g * (dur - t) / ramp) if not on_plateau else np.full(n, g)
    sig = np.sinc(np.linspace(-2, 0, n)) * gt / g
    rf = pp.make_arbitrary_rf(sig, flip_angle=np.deg2rad(30), delay=ramp, system=sysm, center=dur, use='excitation')
    gz = pp.make_extended_trapezoid('z', amplitudes=np.array([0, g, g, 0]), times=np.array([0, ramp, ramp + flat, 2 * ramp + flat]), system=sysm)
    for _ in range(2):
        seq.add_block(rf, gz)
        if on_plateau: seq.add_block(pp.make_trapezoid('z', area=-g * ramp / 2, system=sysm))
        seq.add_block(pp.make_delay(2e-3))
    seq.write(path); return path

with tempfile.TemporaryDirectory() as d:
    item = 'selective RF pulses peak under their slice-select gradient (gradient at the RF centre >= 10% of its maximum during the pulse)'
    rep, ch = measure(half_pulse(os.path.join(d, 'hp.seq')))
    assert item not in failed(ch) and rep['rf_centre_slice_gradient_fraction_min'] > 0.9, (failed(ch), rep['rf_centre_slice_gradient_fraction_min'])
    rep, ch = measure(half_pulse(os.path.join(d, 'hp_ramp.seq'), on_plateau=False))
    assert item in failed(ch), (failed(ch), rep['rf_centre_slice_gradient_fraction_min'])
    print('half pulse: RF centre on the plateau PASS, at the end of the ramp-down FAIL')
