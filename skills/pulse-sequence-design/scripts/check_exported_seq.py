#!/usr/bin/env python3
"""Measure what an exported Pulseq file actually does, independent of the script that built it.

Usage:
  python check_exported_seq.py sequence.seq [--te 0.005 0.010] [--tr 0.25] [--flip 20]
      [--slice-thickness 0.005] [--rf-spoil 117] [--max-grad 32] [--max-slew 130]

Reports realized echo times (excitation RF centre -> ADC sample nearest k-space centre),
TR, flip angles, slice-selective excitation and small-tip slice FWHM, RF-spoiling phase
increments, ADC/RF phase agreement, post-readout spoiler area, gradient/slew peaks and
Pulseq timing errors. With expectations given, prints PASS/FAIL per item and exits 1 on
any FAIL. Requires pypulseq (>=1.4) and numpy.
"""
import argparse,json,sys
import numpy as np
import pypulseq as pp

def wrap_deg(x):return (np.asarray(x)+180.)%360.-180.

def small_tip_fwhm(rf,gz_t,gz_g,t0,extent):
    rt=np.asarray(rf.t);sig=np.asarray(rf.signal)
    w=np.diff(np.r_[0.,(rt[:-1]+rt[1:])/2,float(rf.shape_dur)])
    g=np.interp(t0+rf.delay+rt,gz_t,gz_g,left=0,right=0) if len(gz_t) else np.zeros_like(rt)
    if not np.any(abs(g[abs(sig)>.05*abs(sig).max()])>1.):return None   # no slice-select gradient during RF
    z=np.linspace(-extent,extent,2001);phase=np.cumsum(g*w)
    resp=abs(np.exp(2j*np.pi*np.outer(z,phase))@(sig*w));mid=np.argmin(abs(z));half=resp[mid]/2;l=r=mid
    while l>0 and resp[l]>=half:l-=1
    while r<len(z)-1 and resp[r]>=half:r+=1
    return None if l==0 or r==len(z)-1 else float(z[r]-z[l])

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('seq');ap.add_argument('--te',type=float,nargs='*');ap.add_argument('--tr',type=float)
    ap.add_argument('--flip',type=float);ap.add_argument('--slice-thickness',type=float);ap.add_argument('--rf-spoil',type=float)
    ap.add_argument('--max-grad',type=float,help='mT/m');ap.add_argument('--max-slew',type=float,help='T/m/s')
    ap.add_argument('--gamma',type=float,default=42.576e6);a=ap.parse_args()
    s=pp.Sequence();s.read(a.seq);rep={};checks=[]
    ok,err=s.check_timing();rep['timing_ok']=bool(ok);rep['timing_errors']=[str(e) for e in err][:5]
    t=0.;rfs=[];adcs=[]
    for i in s.block_events:
        b=s.get_block(i)
        if b.rf is not None:rfs.append((t,b.rf))
        if b.adc is not None:adcs.append((t,b.adc))
        t+=pp.calc_duration(b)
    rep['duration_s']=t;rep['n_rf']=len(rfs);rep['n_adc']=len(adcs)
    waves=s.waveforms()
    rep['peak_grad_mT_m']=[float(np.max(abs(w[1]))/a.gamma*1e3) if len(w[1]) else 0. for w in waves]
    rep['peak_slew_T_m_s']=[float(np.max(abs(np.diff(w[1])/np.diff(w[0])))/a.gamma) if len(w[1])>1 else 0. for w in waves]
    flips=[];fwhm=[];centers=[]
    for st,rf in rfs:
        rt=np.asarray(rf.t);sig=np.asarray(rf.signal);w=np.diff(np.r_[0.,(rt[:-1]+rt[1:])/2,float(rf.shape_dur)])
        flips.append(float(abs(np.sum(sig*w))*360.));centers.append(st+rf.delay+pp.calc_rf_center(rf)[0])
        ext=2*(a.slice_thickness or 0.01);fwhm.append(small_tip_fwhm(rf,waves[2][0],waves[2][1],st,ext) if len(waves)>2 else None)
    centers=np.array(centers);rep['flip_deg']=sorted(set(round(f,3) for f in flips))
    rep['slice_selective_all_rf']=all(f is not None for f in fwhm)
    rep['slice_fwhm_mm']=sorted(set(round(f*1e3,3) for f in fwhm if f is not None))
    if adcs:
        k,_,_,_,ta=s.calculate_kspace();kk=np.asarray(k).T;start=0;tes=[];kmin=[];prev=[]
        for st,adc in adcs:
            n=adc.num_samples;seg=kk[start:start+n];tt=np.asarray(ta)[start:start+n];start+=n
            j=int(np.argmin(np.linalg.norm(seg,axis=1)));kmin.append(float(np.linalg.norm(seg[j])))
            p=np.searchsorted(centers,tt[0],side='right')-1;prev.append(p);tes.append(float(tt[j]-centers[p]) if p>=0 else float('nan'))
        rep['echo_times_ms_unique']=sorted(set(round(x*1e3,4) for x in tes))
        rep['min_abs_k_per_adc_max_cycles_m']=max(kmin)
        rfph=np.rad2deg([r.phase_offset for _,r in rfs]);adph=np.rad2deg([d.phase_offset for _,d in adcs])
        rep['adc_minus_rf_phase_max_deg']=float(np.max(abs(wrap_deg(adph-rfph[np.clip(prev,0,None)]))))
        z=waves[2] if len(waves)>2 else [np.array([]),np.array([])];areas=[]
        last={}
        for (st,adc),p in zip(adcs,prev):last[p]=st+adc.delay+adc.num_samples*adc.dwell
        for p,tend in last.items():
            tn=centers[p+1] if p+1<len(centers) else t;g=np.linspace(tend,tn,4000)
            areas.append(float(abs(np.trapezoid(np.interp(g,z[0],z[1],left=0,right=0),g))) if len(z[0]) else 0.)
        rep['post_readout_z_area_cycles_per_m_min']=min(areas) if areas else None
    exc=centers[sorted(set(prev))] if adcs else centers
    rep['tr_ms_unique']=sorted(set(round(x*1e3,4) for x in np.diff(centers)))
    ph=np.rad2deg([r.phase_offset for _,r in rfs])
    if len(ph)>=3:rep['rf_phase_second_diff_deg_unique']=sorted(set(round(float(x)%360,3) for x in wrap_deg(np.diff(ph,2))))
    def chk(name,cond,detail):checks.append({'item':name,'pass':bool(cond),'detail':detail})
    chk('pulseq timing',rep['timing_ok'],rep['timing_errors'][:2])
    if a.max_grad:chk('peak gradient',max(rep['peak_grad_mT_m'])<=a.max_grad+1e-3,rep['peak_grad_mT_m'])
    if a.max_slew:chk('peak slew',max(rep['peak_slew_T_m_s'])<=a.max_slew+1e-3,rep['peak_slew_T_m_s'])
    if a.te and adcs:
        uniq=np.array(sorted(set(round(x,7) for x in tes)));chk('realized TE',len(uniq)==len(a.te) and np.allclose(uniq,sorted(a.te),atol=1e-5),list(uniq*1e3))
    if a.tr:chk('realized TR',len(rep['tr_ms_unique'])>0 and np.allclose(rep['tr_ms_unique'],a.tr*1e3,atol=1e-2),rep['tr_ms_unique'])
    if a.flip:chk('flip angle',np.allclose(flips,a.flip,atol=.25),rep['flip_deg'])
    if a.slice_thickness:chk('slice-selective excitation and FWHM',rep['slice_selective_all_rf'] and all(abs(f-a.slice_thickness)<=.2*a.slice_thickness for f in fwhm if f is not None),rep['slice_fwhm_mm'])
    if a.rf_spoil is not None and len(ph)>=3:
        e=wrap_deg(np.diff(ph,2)-a.rf_spoil);chk('quadratic RF spoiling increment',np.max(abs(e))<.1,{'max_error_deg':float(np.max(abs(e))),'hint':'wrap increment and phase to [0,360) each update'})
    if adcs and a.rf_spoil is not None:chk('ADC phase equals RF phase of the same TR',rep['adc_minus_rf_phase_max_deg']<.1,rep['adc_minus_rf_phase_max_deg'])
    if adcs and a.slice_thickness and rep.get('post_readout_z_area_cycles_per_m_min') is not None:
        chk('post-readout slice spoiling (cycles per slice)',True,rep['post_readout_z_area_cycles_per_m_min']*a.slice_thickness)
    rep['checks']=checks;print(json.dumps(rep,indent=1,default=float))
    sys.exit(1 if any(not c['pass'] for c in checks) else 0)
if __name__=='__main__':main()

