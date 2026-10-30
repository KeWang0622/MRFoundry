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
    assert set(failed(ch)) == {'realized TI (inversion centre -> excitation centre)', 'post-inversion z spoiler (cycles per slice)'}, failed(ch)
    # fallback role detection without rf.use
    path = ir_gre(P('ir_nouse.seq')); txt = open(path).read().replace(' i\n', ' u\n'); open(path, 'w').write(txt)
    rep, ch = measure(path, ti=[0.05, 0.4]); assert rep['rf_roles']['inversion'] == 32 and not failed(ch), (rep['rf_roles'], failed(ch))
    # balanced SSFP
    rep, ch = measure(bssfp(P('ssfp.seq')), tr=8e-3, flip=40, balanced=True, rf_phase_cycle=180, te_half_tr=True, matrix=(16, 16), fov=0.2, max_grad=32, max_slew=130)
    assert not failed(ch), failed(ch); print('bSSFP ok: net area/TR', rep['net_area_per_tr_cycles_m_max_abs'], 'TE', rep['te_ms'], 'TR', rep['tr_ms'], 'dummies', rep['excitations_before_first_adc'])
    rep, ch = measure(bssfp(P('ssfp_unbal.seq'), balanced=False), balanced=True); assert failed(ch) == ['balanced: zero net gradient area per TR on every axis'], failed(ch)
    rep, ch = measure(bssfp(P('ssfp_adc.seq'), adc_follows_rf=False), rf_phase_cycle=180); assert failed(ch) == ['ADC phase equals the phase of its own excitation'], failed(ch)
    rep, ch = measure(bssfp(P('ssfp_nocyc.seq'), alternate=False), rf_phase_cycle=180); assert 'RF phase cycling increment' in failed(ch), failed(ch)
    # spin echo
    rep, ch = measure(spin_echo(P('se.seq')), te=30e-3, tr=0.3, cpmg=True, slice_thickness=5e-3, matrix=(16, 16), fov=0.2)
    assert not failed(ch), failed(ch); assert rep['rf_roles']['refocusing'] == 16 and abs(rep['refocusing_after_excitation_ms'][0] - 15) < 1e-3, rep
    print('spin echo ok: TE', rep['te_ms'], 'refocusing at', rep['refocusing_after_excitation_ms'], 'ms, phase', rep['refocusing_minus_excitation_phase_deg'])
    rep, ch = measure(spin_echo(P('se_bad.seq'), cpmg=False), cpmg=True); assert failed(ch) == ['CPMG: refocusing phase = excitation phase +/- 90 deg'], failed(ch)
    print('all check_exported_seq tests passed')

if __name__ == '__main__':
    main()

