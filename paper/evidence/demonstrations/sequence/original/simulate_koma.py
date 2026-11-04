"""Use official KomaMRI for Bloch simulation; no custom physics solver.

API pattern: JuliaHealth/komamripy examples/basic_simulation.py and
examples/pypulseq_composability.py. Built-in brain phantom subsampled for a
small CPU prototype; replicated through z to represent slice selection.
"""
from pathlib import Path
import json,time
import numpy as np
import komamripy as km
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
scanner=km.Scanner(limits=km.HardwareLimits(Gmax=.032,Smax=130.))
params={'return_type':'mat','gpu':False,'precision':'f64','Δt_rf':10e-6,'Δt':10e-6}
print('Running built-in EPI smoke test',flush=True)
base=km.brain_phantom2D(ss=16)
smoke=np.asarray(km.simulate(base,km.PulseDesigner.EPI_example(),scanner,sim_params=params))
assert smoke.size>0 and np.isfinite(smoke).all() and np.max(np.abs(smoke))>0
print('Official example passed:',smoke.shape,flush=True)

# Phantom construction is configuration of KomaMRI, not a new simulator.
zpos=np.linspace(-.004,.004,33)
fields={name:np.asarray(getattr(base,name),dtype=float).copy() for name in ['x','y','ρ','T1','T2','T2s','Δw']}
count=len(fields['x'])
kwargs={name:np.tile(arr,len(zpos)) for name,arr in fields.items()}
kwargs['ρ']/=len(zpos)
kwargs['z']=np.repeat(zpos,count)
obj=km.Phantom(name='Koma_brain_coarse_slice',**kwargs)
print('Spins:',count*len(zpos),flush=True)
seq=km.files.read_seq(str(OUT/'golden_angle_radial_gre.seq'))
print('Read exported Pulseq sequence; starting full train',flush=True)
start=time.time()
raw=np.asarray(km.simulate(obj,seq,scanner,sim_params=params)).copy()
signal=raw.reshape(-1,order='F')
assert signal.size==128*64,(raw.shape,signal.size)
assert np.isfinite(signal).all() and np.max(np.abs(signal))>0
elapsed=time.time()-start
print('Full sequence simulation finished:',elapsed,'s',flush=True)
# Repeat with twice as fine RF stepping to test temporal convergence.
fine=dict(params);fine['Δt_rf']=5e-6
raw2=np.asarray(km.simulate(obj,seq,scanner,sim_params=fine)).copy()
signal2=raw2.reshape(-1,order='F')
rel=float(np.linalg.norm(signal2-signal)/np.linalg.norm(signal2))
np.savez_compressed(OUT/'koma_signal.npz',signal=signal2.reshape(128,64),signal_rf10us=signal.reshape(128,64),**kwargs)
report={'engine':'KomaMRI via komamripy','official_epi_smoke_test_pass':True,
 'full_exported_sequence_simulated':True,'spins':len(kwargs['x']),
 'phantom':'KomaMRI built-in brain2D ss=16 replicated at 33 z positions from -4 to +4 mm',
 'adc_samples':signal.size,'finite_nonzero_signal':True,'cpu_seconds_rf10us':elapsed,
 'rf_step_us':[10,5],'gradient_max_step_us':10,
 'relative_signal_change_rf_step_halving':rel,
 'limitations':['Coarse phantom; spatial convergence not established.',
 'Uniform receive and transmit sensitivity; no gradient delays/eddy currents or motion.',
 'Phantom default relaxation and chemical-shift parameters retained.',
 'No PNS, SAR, gradient heating or vendor interpreter validation.']}
(OUT/'koma_report.json').write_text(json.dumps(report,indent=2)+'\n')
traj=np.load(OUT/'trajectory.npz');k=traj['k_adc']
fig,ax=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
ax[0].scatter(fields['x']*1e3,fields['y']*1e3,c=fields['ρ'],s=20,cmap='gray')
ax[0].set(title='KomaMRI phantom · coarse in-plane grid',xlabel='x (mm)',ylabel='y (mm)',aspect='equal')
for j in range(128):ax[1].plot(k[0,j*64:(j+1)*64],k[1,j*64:(j+1)*64],lw=.4,alpha=.6)
ax[1].set(title='128 golden-angle spokes',xlabel='kx (cycles/m)',ylabel='ky (cycles/m)',aspect='equal')
im=ax[2].imshow(np.log10(np.maximum(np.abs(signal2.reshape(128,64)),1e-8)),aspect='auto',origin='lower',cmap='magma')
ax[2].set(title='KomaMRI Bloch signal',xlabel='ADC sample',ylabel='Acquired spoke')
fig.colorbar(im,ax=ax[2],label='log10 |signal| (a.u.)')
fig.suptitle('PyPulseq → exported .seq → KomaMRI · simulation-only prototype')
fig.savefig(OUT/'koma_summary.png',dpi=160)
print(json.dumps(report,indent=2),flush=True)
