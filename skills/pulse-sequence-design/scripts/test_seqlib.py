"""Tests for mrfoundry_seqlib (python test_seqlib.py). Builds small single-echo Cartesian and radial
spoiled-GRE examples from the helpers, measures the exported files and, if komamripy is installed,
simulates a small object and checks the centred-FFT image orientation."""
import os,sys,tempfile
import numpy as np, pypulseq as pp
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from mrfoundry_seqlib import *
from check_exported_seq import measure

def cartesian_gre(path, n=32, fov=0.2, te=6e-3, tr=20e-3, flip=15, sl=5e-3, dwell=40e-6, dummies=10, dummy_adc=False):
    """Example: single-echo 2D Cartesian spoiled GRE, one phase-encode line per TR after dummy excitations."""
    sysm=make_system();seq=pp.Sequence(sysm)
    rf,gz,reph=slice_selective_excitation(sysm,flip,sl);read,adc,pre=centered_readout(sysm,n,fov,dwell)
    spoil=RFSpoiler();exc=pp.calc_duration(rf,gz);tpre=1e-3
    for j in [None]*dummies+list(range(n)):
        ph=spoil.next();rf.phase_offset=ph;adc.phase_offset=ph
        ky=0.0 if j is None else (j-n//2)/fov
        gx=pp.make_trapezoid('x',area=pre,duration=tpre,system=sysm)
        gy=pp.make_trapezoid('y',area=ky,duration=tpre,system=sysm)
        gzr=pp.make_trapezoid('z',area=reph,duration=tpre,system=sysm)
        d=fill_delay(te,(exc-rf_center_time(rf))+tpre+adc_sample_time(adc,n//2),what='TE')
        seq.add_block(rf,gz);seq.add_block(gx,gy,gzr)
        if d>0:seq.add_block(pp.make_delay(d))
        seq.add_block(read,adc) if (j is not None or dummy_adc) else seq.add_block(read)
        gyr=pp.make_trapezoid('y',area=-ky,duration=1.5e-3,system=sysm)
        gzs=pp.make_trapezoid('z',area=spoiler_area(4,sl),duration=1.5e-3,system=sysm)
        used=exc+tpre+d+pp.calc_duration(read,adc)
        seq.add_block(gyr,gzs,pp.make_delay(fill_delay(tr,used,what='TR')))
    ok,err=seq.check_timing();assert ok,err[:2];seq.write(path);return path

def radial_gre(path, n=32, spokes=24, fov=0.2, te=4e-3, tr=15e-3, flip=12, sl=5e-3, dwell=40e-6):
    """Example: single-echo 2D golden-angle radial spoiled GRE."""
    sysm=make_system();seq=pp.Sequence(sysm);rf,gz,reph=slice_selective_excitation(sysm,flip,sl)
    read,adc,pre=centered_readout(sysm,n,fov,dwell);spoil=RFSpoiler();exc=pp.calc_duration(rf,gz);ga=np.deg2rad(111.246117975);tpre=1e-3
    for i in range(spokes):
        ph=spoil.next();rf.phase_offset=ph;adc.phase_offset=ph;a=(i*ga)%np.pi
        gx=pp.make_trapezoid('x',area=pre,duration=tpre,system=sysm);gzr=pp.make_trapezoid('z',area=reph,duration=tpre,system=sysm)
        d=fill_delay(te,(exc-rf_center_time(rf))+tpre+adc_sample_time(adc,n//2),what='TE')
        seq.add_block(rf,gz);seq.add_block(*pp.rotate(gx,gzr,angle=a,axis='z'))
        if d>0:seq.add_block(pp.make_delay(d))
        seq.add_block(*pp.rotate(read,adc,angle=a,axis='z'))
        gzs=pp.make_trapezoid('z',area=spoiler_area(4,sl),duration=1.5e-3,system=sysm)
        seq.add_block(gzs,pp.make_delay(fill_delay(tr,exc+tpre+d+pp.calc_duration(read,adc),what='TR')))
    ok,err=seq.check_timing();assert ok,err[:2];seq.write(path);return path

def main():
    tmp=tempfile.mkdtemp()
    import subprocess;o=subprocess.run(['sh',os.path.join(HERE,'setup_koma_julia.sh'),os.path.join(tmp,'kj'),'--dry-run'],capture_output=True,text=True)
    assert o.returncode in (0,2) and ('julialang-s3.julialang.org' in o.stdout or 'unsupported' in o.stderr) and not os.path.exists(os.path.join(tmp,'kj')),(o.stdout,o.stderr)
    print('setup_koma_julia.sh dry run:',(o.stdout.split()[2] if o.stdout else o.stderr.strip()))
    c=cartesian_gre(os.path.join(tmp,'cart.seq'));rep,checks=measure(c,te=[6e-3],tr=20e-3,flip=15,slice_thickness=5e-3,rf_spoil=117,max_grad=32,max_slew=130)
    bad=[x for x in checks if not x['pass']];assert not bad,bad;print('cartesian: exported checks pass; TE ms',rep.get('te_ms'),'slice FWHM mm',rep.get('excitation_slice_fwhm_mm'))
    r=radial_gre(os.path.join(tmp,'rad.seq'));rep,checks=measure(r,te=[4e-3],tr=15e-3,flip=12,slice_thickness=5e-3,rf_spoil=117)
    bad=[x for x in checks if not x['pass']];assert not bad,bad;print('radial: exported checks pass; TE ms',rep.get('te_ms'))
    try:import komamripy  # noqa
    except ImportError:print('komamripy not installed: simulation test skipped');return
    n=32;fov=0.2;yy,xx=np.mgrid[0:n,0:n];rho=((xx-12)**2+(yy-18)**2<=36)*1.0+((xx-22)**2+(yy-10)**2<=9)*0.5
    x=(xx-n//2)*fov/n;y=(yy-n//2)*fov/n
    out=simulate_with_koma(c,x,y,np.zeros_like(x),rho,np.full(rho.shape,0.3),np.full(rho.shape,0.005))  # T2 << TR: point isochromats cannot be gradient-spoiled
    sys.path.insert(0,os.path.join(HERE,'..','..','mri-reconstruction','scripts'))
    from mrfoundry_reconlib import cartesian_image
    img=abs(cartesian_image(out['samples']));corr=np.corrcoef(img.ravel(),rho.ravel())[0,1]
    print('KomaMRI + centred FFT: image/object correlation %.4f, samples %s'%(corr,out['samples'].shape))
    assert corr>0.98,'orientation or centring mismatch'
    # B7: KomaMRI's sign convention, the replay comparison and the Julia backend
    x0,y0=0.035,-0.02
    one=simulate_with_koma(c,[x0],[y0],[0.0],[1.0],[1.0],[0.005]);kk=one['k']  # T2 << TR: no echoes from earlier TRs
    pred=np.exp(-2j*np.pi*(kk[...,0]*x0+kk[...,1]*y0));ph=one['samples']/abs(one['samples'])
    d_ok=relative_difference_after_global_phase(ph,pred);d_conj=relative_difference_after_global_phase(np.conj(ph),pred)
    print('one off-centre spin: samples follow exp(-2 pi i k.r) (difference %.1e); conjugated %.2f'%(d_ok,d_conj))
    assert d_ok<0.05 and d_conj>0.5
    s0=out['samples'];assert relative_difference_after_global_phase(s0*np.exp(0.7j),s0)<1e-12
    args=(x,y,np.zeros_like(x),rho,np.full(rho.shape,0.3),np.full(rho.shape,0.005))
    replay_check(c,s0*np.exp(-1.1j),*args)
    for bad,name in [(np.conj(s0),'conjugated'),(2*s0,'rescaled'),(s0[::-1],'reversed ADC order')]:
        try:replay_check(c,bad,*args);raise RuntimeError(name+' passed')
        except AssertionError:print('replay check FAILS a '+name+' delivery')
    J,P=os.environ.get('MRFOUNDRY_JULIA'),os.environ.get('MRFOUNDRY_KOMA_PROJECT')
    if J and P:
        oj=simulate_with_koma(c,*args,backend='julia',julia=J,julia_project=P)
        dj=relative_difference_after_global_phase(oj['samples'],s0);print('Julia backend (koma_sim.jl) vs komamripy: %.1e'%dj);assert dj<1e-9
    else:print('MRFOUNDRY_JULIA/MRFOUNDRY_KOMA_PROJECT not set: Julia backend test skipped')
if __name__=='__main__':main()

