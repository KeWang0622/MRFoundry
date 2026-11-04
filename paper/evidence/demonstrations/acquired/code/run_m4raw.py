"""Reproducible acquired-human-MRI illustration; existing SigPy solvers only."""
from pathlib import Path
import csv, hashlib, json, platform, sys, time, xml.etree.ElementTree as ET
import h5py
import numpy as np
import scipy
import sigpy as sp
import sigpy.mri as mr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'work/mrfoundry-real-data-v19'
OUT=ROOT/'outputs/mrm-toolbox/real-data-v19/m4raw'
OUT.mkdir(parents=True,exist_ok=True)
selection=json.loads((WORK/'source/selected-acquisition.json').read_text())
inp=WORK/'data'/Path(selection['relative_path']).name
sha=hashlib.sha256(inp.read_bytes()).hexdigest()
inventory={r['relative_path']:r for r in csv.DictReader((WORK/'source/file_inventory.tsv').open(),delimiter='\t')}
assert sha==inventory[selection['relative_path']]['sha256']
z=8 # zero-based middle-lower slice, fixed before seeing any reconstruction
with h5py.File(inp,'r') as f:
    full_shape=f['kspace'].shape
    k=f['kspace'][z].astype(np.complex64)
    stored_ref=f['reconstruction_rss'][z]
    header=f['ismrmrd_header'][()].decode()
ns={'m':'http://www.ismrm.org/ISMRMRD'}
xml=ET.fromstring(header)
def xtext(name): return xml.find('.//m:'+name,ns).text.strip()
assert np.isfinite(k).all()
support=np.any(np.abs(k)>0,axis=(0,1))
assert support.sum()==195 and k.shape==(4,256,256)
coil_raw=sp.ifft(k,axes=(-2,-1))
rss_raw=np.sqrt(np.sum(np.abs(coil_raw)**2,axis=0))
source_rss_rel=float(np.linalg.norm(rss_raw-stored_ref)/np.linalg.norm(stored_ref))
scale=float(np.max(rss_raw)) # shared scalar; no fitted intensity gain
k=k/scale;coil=coil_raw/scale;reference=rss_raw/scale
window=float(np.percentile(reference,99.5))
fft_error=float(np.linalg.norm(sp.fft(coil,axes=(-2,-1))-k)/np.linalg.norm(k))
print('Input',full_shape,'slice',z,'source lines',support.sum(),'RSS match',source_rss_rel,flush=True)
t=time.monotonic()
maps,eigen=mr.app.EspiritCalib(k,calib_width=24,kernel_width=6,thresh=.02,crop=.95,max_iter=100,output_eigenvalue=True,show_pbar=False).run()
eigen=np.squeeze(eigen)
print('ESPIRiT seconds',time.monotonic()-t,flush=True)
arrays={'kspace':k,'coil_images':coil,'reference_rss':reference,'sensitivity_maps':maps,'eigenvalue':eigen,'source_pe_mask':support}
results={}
history={}
for stride in (1,2,4):
    pe=np.arange(256)
    mask=support & (((pe%stride)==0)|((pe>=116)&(pe<140)))
    weights=np.broadcast_to(mask,(256,256)).copy().astype(np.float32)
    y=k*weights
    start=time.monotonic()
    app=mr.app.SenseRecon(y,maps,lamda=.001,weights=weights,max_iter=120,tol=1e-8,save_objective_values=True,show_pbar=False)
    recon=app.run()
    pred=sp.fft(maps*recon,axes=(-2,-1))
    zero=np.sqrt(np.sum(np.abs(sp.ifft(y,axes=(-2,-1)))**2,axis=0))
    magnitude=np.abs(recon)
    data_res=float(np.linalg.norm((pred-k)*weights)/np.linalg.norm(k*weights))
    nrmse=float(np.linalg.norm(magnitude-reference)/np.linalg.norm(reference))
    zero_nrmse=float(np.linalg.norm(zero-reference)/np.linalg.norm(reference))
    holdout=support & ~mask
    holdout_res=float(np.linalg.norm((pred-k)[...,holdout])/np.linalg.norm(k[...,holdout])) if holdout.any() else None
    objective=np.asarray(app.objective_values,dtype=float)
    results[str(stride)]={'nominal_stride':stride,'acquired_source_lines':195,'retained_lines':int(mask.sum()),'effective_acceleration_vs_available_source':float(195/mask.sum()),'source_grid_fraction':float(mask.sum()/256),'all_source_rss_nrmse':nrmse,'zero_filled_rss_nrmse':zero_nrmse,'measured_data_residual':data_res,'heldout_source_data_residual':holdout_res,'iterations':int(app.alg.iter),'seconds':time.monotonic()-start,'objective_first':float(objective[0]),'objective_last':float(objective[-1])}
    arrays.update({f'recon_stride{stride}':recon,f'magnitude_stride{stride}':magnitude,f'zero_filled_stride{stride}':zero,f'error_stride{stride}':np.abs(magnitude-reference),f'pe_mask_stride{stride}':mask,f'objective_stride{stride}':objective})
    history[str(stride)]=objective.tolist()
    print(stride,results[str(stride)],flush=True)

def png(a,name,vmax,cmap='gray'):
    # Preserve source row/column ordering; no inferred anatomical flips.
    colors=plt.get_cmap(cmap)(np.clip(a/vmax,0,1))[...,:3]
    im=Image.fromarray(np.uint8(colors*255))
    im.resize((768,768),Image.Resampling.NEAREST).save(OUT/(name+'.png'))
png(reference,'reference-rss',window)
for c in range(4):
    png(np.abs(coil[c]),f'coil-{c+1}',window)
    png(np.abs(maps[c]),f'sensitivity-{c+1}',1)
png(eigen,'calibration-eigenvalue',1)
for s in (1,2,4):
    png(arrays[f'magnitude_stride{s}'],f'reconstruction-stride{s}',window)
    png(arrays[f'zero_filled_stride{s}'],f'zero-filled-stride{s}',window)
    png(arrays[f'error_stride{s}'],f'error-stride{s}',.25,'magma')
    mask=np.broadcast_to(arrays[f'pe_mask_stride{s}'],(256,256))
    png(mask.astype(float),f'sampling-stride{s}',1)
klog=np.log10(np.maximum(np.sqrt(np.sum(np.abs(k)**2,axis=0)),1e-6))
png(np.clip((klog+6)/6,0,1),'kspace-log10',1,'magma')

np.savez_compressed(OUT/'arrays.npz',**arrays)
fig,ax=plt.subplots(2,4,figsize=(12,6.4),constrained_layout=True)
images=[reference,arrays['zero_filled_stride2'],arrays['magnitude_stride2'],arrays['error_stride2'],np.abs(coil[0]),np.abs(maps[0]),arrays['magnitude_stride4'],arrays['error_stride4']]
titles=['All-source RSS reference','Zero-filled; stride 2','SENSE; stride 2','Absolute difference','Acquired coil 1','ESPIRiT map |S1|','SENSE; stride 4','Absolute difference']
for i,(axis,a,title) in enumerate(zip(ax.ravel(),images,titles)):
    im=axis.imshow(a,cmap='magma' if i in (3,7) else 'gray',vmin=0,vmax=.25 if i in (3,7) else (1 if i==5 else window),interpolation='nearest')
    axis.set_title(title,fontsize=10);axis.axis('off')
fig.suptitle('M4Raw acquired human T2w · 4 channels · slice 8 · matched image window',fontsize=12)
fig.savefig(OUT/'inspection.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(5.8,2.3),constrained_layout=True)
for y,s in enumerate((1,2,4)):
    mask=arrays[f'pe_mask_stride{s}'];ax.scatter(np.flatnonzero(mask),np.full(mask.sum(),y),s=7,marker='|',color=['#163a58','#0c8d86','#8a68bb'][y])
ax.set_yticks([0,1,2],['Source: 195 lines',f'Stride 2: {results["2"]["retained_lines"]} lines',f'Stride 4: {results["4"]["retained_lines"]} lines'])
ax.set_xlabel('Stored phase-encode index');ax.set_xlim(0,255);ax.invert_yaxis();ax.spines[['top','right']].set_visible(False)
fig.savefig(OUT/'sampling-support.png',dpi=250);fig.savefig(OUT/'sampling-support.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(5.3,2.8),constrained_layout=True)
for s,color in [(2,'#008b85'),(4,'#8263b0')]:
    o=arrays[f'objective_stride{s}'];ax.semilogy(o/o[0],label=f'Stride {s}',color=color,lw=1.8)
ax.set_xlabel('CG iteration');ax.set_ylabel('Objective / initial');ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
fig.savefig(OUT/'solver-objective.png',dpi=250);fig.savefig(OUT/'solver-objective.pdf');plt.close(fig)
report={
'task':'Reconstruct this raw human brain MRI, compare two retrospective sampling settings, and show what supports the result.',
'status':'New executed tool-based illustration; no controlled agent benchmark',
'source':{'dataset':'M4Raw Brain v1.6','doi':'https://doi.org/10.5281/zenodo.8056074','paper':'https://doi.org/10.1038/s41597-023-02181-4','author_repository':'https://github.com/mylyu/M4Raw','mirror':'https://huggingface.co/datasets/mylyu/M4Raw_brain','revision':'v1.6.0','relative_path':selection['relative_path'],'sha256':sha,'sha256_matches_author_manifest':True,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','selection':'First validation T2 repetition-1 acquisition in author manifest; fixed slice index 8 before reconstruction'},
'input':{'acquired_human_data':True,'simulation':False,'full_shape':list(full_shape),'slice_zero_based':z,'field_T':.3,'contrast':'T2w FSE','coils':4,'stored_matrix':[256,256],'available_PE_lines':195,'native_axes':'slice,coil,FE,PE per official H5_FORMAT.md; legacy XML custom PE/FE labels conflict','FOV_mm':[240,240],'display_grid_mm':[.9375,.9375],'acquired_in_plane_resolution_approx_mm':[.94,1.23],'slice_thickness_mm':5,'spacing_between_slices_mm':6,'TR_ms':5500,'TE_ms':128,'orientation':'Native source axial view retained; no anatomical side labels inferred without voxel-to-patient direction matrix','preexisting_processing':'Provider applied k-space phase modulation for global image off-centering; no new motion correction'},
'software':{'python':sys.version,'sigpy':sp.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'h5py':h5py.__version__,'platform':platform.platform()},
'parameters':{'calibration':'SigPy ESPIRiT','calibration_width':24,'kernel_width':6,'svd_threshold':.02,'eigenvalue_crop':.95,'calibration_max_iter':100,'solver':'SigPy SenseRecon (CG)','lambda_l2':.001,'solver_max_iter':120,'tolerance':1e-8,'retrospective_sampling':'Available source PE lines intersected with even/every-fourth global PE indices, plus retained central 24 lines (116:140)','fixed_parameters':'Identical calibration and L2 strength across compared masks; no per-setting tuning'},
'checks':{'source_rss_relative_L2_error':source_rss_rel,'centered_fft_roundtrip_relative_L2_error':fft_error,'finite_kspace':True,'map_nonzero_pixels':int(np.count_nonzero(np.sum(np.abs(maps)**2,axis=0)>0))},
'sampling_comparison':results,
'display':{'image_window_normalized':[0,window],'common_normalization':'All k-space/reference/recon arrays divided by source RSS maximum; no intensity matching fitted to each result','error_window_normalized':[0,.25],'sensitivity_magnitude_window':[0,1],'PNG_interpolation':'nearest-neighbor 3x; no generative enhancement','no_labels_PNG':True,'native_PNG_dimension':[768,768],'same_slice_FOV':True},
'metric_definitions':{'all_source_rss_nrmse':'L2(|recon|-RSS_source)/L2(RSS_source), entire256x256matrix, without fitted gain','measured_data_residual':'L2(P F S recon - P k)/L2(P k)','heldout_source_data_residual':'L2(Q F S recon - Q k)/L2(Q k) on source lines removed retrospectively; Q not provided to the inverse solve','source_rss_reference':'Centered inverse FFT and RSS of all available195source lines; not noise-free or complete-PE ground truth'},
'limitations':['One selected acquired human slice and four-channel low-field system; no cross-subject or clinical generalization','Retrospective masks are not new scanner acquisitions; efficiency relative to available source195PElines','Published source is already missing61storedPEcolumns; all-source RSS is a noisy reference, not anatomical ground truth','No coil-noise covariance/prewhitening, g-factor or pseudo-replica SNR estimation; acceleration-related noise cost not quantified','Residuals and iteration behavior do not establish anatomical truth','No independent patient-space orientation matrix; retain native source view without invented L/R labels','No with/without-MRFoundry control, task-success rate, speedup, or memory-benefit claim']}
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print('Saved',OUT,flush=True)
