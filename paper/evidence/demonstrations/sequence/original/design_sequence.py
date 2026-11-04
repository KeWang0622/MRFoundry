"""Simulation-only golden-angle radial spoiled GRE; no scanner approval implied."""
from pathlib import Path
import json
import numpy as np
import pypulseq as pp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
FOV, N, SLICE, FLIP, TE, TR = .220, 64, .005, 10., .005, .015
SPOKES, DUMMY = 128, 200
GA = np.pi * (np.sqrt(5) - 1) / 2  # full spokes: 111.246 degrees, modulo pi


def design():
    sys = pp.Opts(max_grad=32, grad_unit='mT/m', max_slew=130,
                  slew_unit='T/m/s', rf_dead_time=100e-6,
                  rf_ringdown_time=20e-6, adc_dead_time=10e-6)
    seq = pp.Sequence(sys)
    rf, gz, gzr = pp.make_sinc_pulse(flip_angle=np.deg2rad(FLIP),
        duration=.003, slice_thickness=SLICE, apodization=.5,
        time_bw_product=4, system=sys, return_gz=True,
        delay=sys.rf_dead_time, use='excitation')
    read = pp.make_trapezoid('x', flat_area=N/FOV, flat_time=.00256, system=sys)
    adc = pp.make_adc(N, dwell=read.flat_time/N, delay=read.rise_time, system=sys)
    # Place sample N//2 exactly at k=0 (not halfway between the central samples).
    pre = pp.make_trapezoid('x', area=-read.area/2-1/(2*FOV), duration=.001, system=sys)
    zpre = pp.make_trapezoid('z', area=gzr.area, duration=.001, system=sys)
    sx = pp.make_trapezoid('x', area=2*N/FOV, duration=.002, system=sys)
    sz = pp.make_trapezoid('z', area=4/SLICE, duration=.002, system=sys)
    rf_center = rf.delay + pp.calc_rf_center(rf)[0]
    echo_offset = adc.delay + (N//2+.5)*adc.dwell
    exc_dur, pre_dur, read_dur = pp.calc_duration(rf,gz), pp.calc_duration(pre,zpre), pp.calc_duration(read,adc)
    delay_te = TE + rf_center - exc_dur - pre_dur - echo_offset
    delay_te = round(delay_te/sys.grad_raster_time)*sys.grad_raster_time
    tail = TR-exc_dur-pre_dur-delay_te-read_dur
    assert delay_te >= 0 and tail >= pp.calc_duration(sx,sz)
    phase, inc = 0., 0.
    angles = []
    for rep in range(DUMMY+SPOKES):
        angle = ((rep-DUMMY)*GA) % np.pi
        rf.phase_offset = adc.phase_offset = np.deg2rad(phase)
        inc = (inc+117.) % 360.; phase = (phase+inc) % 360.
        seq.add_block(rf,gz)
        seq.add_block(*pp.rotate(pre,zpre,angle=angle,axis='z'))
        seq.add_block(pp.make_delay(delay_te))
        events = (read,adc) if rep >= DUMMY else (read,)
        seq.add_block(*pp.rotate(*events,angle=angle,axis='z'))
        seq.add_block(*pp.rotate(sx,sz,angle=angle,axis='z'),pp.make_delay(tail))
        if rep >= DUMMY: angles.append(angle)
    seq.set_definition('Name','ga_radial_gre_sim')
    seq.set_definition('FOV',[FOV,FOV,SLICE])
    seq.set_definition('TE',TE); seq.set_definition('TR',TR)
    seq.set_definition('NumDummy',DUMMY); seq.set_definition('GoldenAngleDeg',np.rad2deg(GA))
    seq.set_definition('SimulationOnly',1)
    return seq,sys,np.asarray(angles),exc_dur+pre_dur


def main():
    seq,sys,angles,stop=design()
    ok,errors=seq.check_timing();assert ok,errors
    # Validate the constructed sequence before export.
    k,_,texc,_,tadc=seq.calculate_kspace()
    texc=np.asarray(texc);tadc=np.asarray(tadc)
    assert k.shape==(3,N*SPOKES)
    expected=np.zeros_like(k)
    kr=(np.arange(N)-N//2)/FOV
    for j,a in enumerate(angles):expected[:2,j*N:(j+1)*N]=np.array([np.cos(a),np.sin(a)])[:,None]*kr
    trajectory_error=float(np.max(np.abs(k-expected)))
    actual_te=tadc.reshape(SPOKES,N)[:,N//2]-texc[DUMMY:]
    assert trajectory_error<1e-5,trajectory_error
    assert np.max(np.abs(actual_te-TE))<1e-8
    assert np.max(np.abs(np.diff(texc)-TR))<1e-8
    waves=seq.waveforms()
    peak_g=[float(np.max(np.abs(w[1]))/sys.gamma*1e3) for w in waves]
    peak_s=[float(np.max(np.abs(np.diff(w[1])/np.diff(w[0])))/sys.gamma) for w in waves]
    assert max(peak_g)<=32+1e-6 and max(peak_s)<=130+1e-6
    # Raster sampled RMS and simultaneous vector limits are informative, not scanner certification.
    duration=seq.duration()[0];tt=np.arange(0,duration,sys.grad_raster_time)
    gv=np.array([np.interp(tt,w[0],w[1],left=0,right=0)/sys.gamma for w in waves])
    rms=np.sqrt(np.mean(gv**2,axis=1))*1e3
    path=OUT/'golden_angle_radial_gre.seq'
    seq.write(str(path))
    readback=pp.Sequence(sys); readback.read(str(path))
    passed,problems=readback.check_timing(); assert passed,problems
    rk,*_=readback.calculate_kspace()
    roundtrip=float(np.max(np.abs(rk-k)));assert roundtrip<.01
    report=dict(pypulseq_version=pp.__version__,simulation_only=True,
      fov_mm=FOV*1000,matrix=N,resolution_mm=FOV/N*1000,slice_mm=SLICE*1000,
      flip_deg=FLIP,te_ms=float(actual_te.mean()*1000),tr_ms=TR*1000,
      spokes=SPOKES,dummy_excitations=DUMMY,duration_s=duration,
      golden_angle_deg=float(np.rad2deg(GA)),timing_pass=True,
      peak_gradient_mTm=peak_g,peak_slew_Tms=peak_s,
      rms_gradient_mTm=rms.tolist(),trajectory_error_cycles_per_m=trajectory_error,
      roundtrip_trajectory_error_cycles_per_m=roundtrip)
    (OUT/'design_report.json').write_text(json.dumps(report,indent=2))
    np.savez_compressed(OUT/'trajectory.npz',k_adc=k,t_adc=tadc,angles=angles)
    (OUT/'pulseq_test_report.txt').write_text(seq.test_report())
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
