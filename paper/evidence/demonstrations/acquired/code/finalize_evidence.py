"""Keep initial findings and package fixed-parameter L1 comparison and provenance."""
from pathlib import Path
import hashlib,json,platform,sys,time,datetime,shutil
import numpy as np
import sigpy as sp
import sigpy.mri as mr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import binary_fill_holes,binary_erosion
from dipy.segment.mask import median_otsu
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'work/mrfoundry-real-data-v19';OUT=ROOT/'outputs/mrm-toolbox/real-data-v19';P=OUT/'m4raw'
initial=json.loads((P/'report.json').read_text())
if not (P/'initial-sense-report.json').exists():
    (P/'initial-sense-report.json').write_text(json.dumps(initial,indent=2))
else: initial=json.loads((P/'initial-sense-report.json').read_text())
a=dict(np.load(P/'arrays.npz'));k=a['kspace'];maps=a['sensitivity_maps'];ref=a['reference_rss'];source=a['source_pe_mask']
_,roi=median_otsu(ref,median_radius=3,numpass=2)
roi=binary_erosion(binary_fill_holes(roi),iterations=2)
co=a['coil_images'];projected=np.sum(maps.conj()*co,axis=0)
projection_residual_full=float(np.linalg.norm(maps*projected-co)/np.linalg.norm(co))
projection_residual_roi=float(np.linalg.norm((maps*projected-co)[:,roi])/np.linalg.norm(co[:,roi]))
results={};final={'reference_rss':ref,'image_intensity_roi':roi,'source_pe_mask':source}
for s in (2,4):
    mask=a[f'pe_mask_stride{s}'];w=np.broadcast_to(mask,ref.shape).astype(np.float32);y=k*w
    np.random.seed(0)
    start=time.monotonic()
    app=mr.app.L1WaveletRecon(y,maps,lamda=.01,weights=w,max_iter=200,show_pbar=False,save_objective_values=True)
    r=app.run()
    np.random.seed(0)
    check=mr.app.L1WaveletRecon(y,maps,lamda=.01,weights=w,max_iter=400,show_pbar=False)
    r400=check.run()
    iteration_change=float(np.linalg.norm(r400-r)/np.linalg.norm(r400))
    pred=sp.fft(maps*r,axes=(-2,-1));hold=source & ~mask
    rec={'nominal_stride':s,'retained_lines':int(mask.sum()),'effective_acceleration_vs_available_source':float(source.sum()/mask.sum()),
         'all_source_rss_nrmse':float(np.linalg.norm(abs(r)-ref)/np.linalg.norm(ref)),
         'image_intensity_roi_nrmse':float(np.linalg.norm((abs(r)-ref)[roi])/np.linalg.norm(ref[roi])),
         'measured_data_residual':float(np.linalg.norm((pred-k)*w)/np.linalg.norm(k*w)),
         'heldout_source_data_residual':float(np.linalg.norm((pred-k)[...,hold])/np.linalg.norm(k[...,hold])),
         'zero_filled_rss_nrmse':initial['sampling_comparison'][str(s)]['zero_filled_rss_nrmse'],
         'complex_image_change_200_to_400_iterations':iteration_change,'objective_first':float(app.objective_values[0]),'objective_last':float(app.objective_values[-1]),'elapsed_seconds_with_iteration_check':time.monotonic()-start}
    results[str(s)]=rec
    final.update({f'recon_stride{s}':r,f'magnitude_stride{s}':abs(r),f'error_stride{s}':abs(abs(r)-ref),f'pe_mask_stride{s}':mask,f'objective_stride{s}':np.asarray(app.objective_values),f'recon400_stride{s}':r400})
    print(rec,flush=True)
np.savez_compressed(P/'final-arrays.npz',**final)
window=initial['display']['image_window_normalized'][1]
def png(a,name,vmax,cmap='gray'):
    rgb=plt.get_cmap(cmap)(np.clip(a/vmax,0,1))[...,:3]
    Image.fromarray(np.uint8(rgb*255)).resize((768,768),Image.Resampling.NEAREST).save(P/(name+'.png'))
for s in (2,4):
    png(final[f'magnitude_stride{s}'],f'final-reconstruction-stride{s}',window)
    png(final[f'error_stride{s}'],f'final-error-stride{s}',.25,'magma')
png(roi.astype(float),'diagnostic-intensity-roi',1)
fig,axes=plt.subplots(2,3,figsize=(9,6.7),constrained_layout=True)
seq=[ref,final['magnitude_stride2'],final['magnitude_stride4'],roi,final['error_stride2'],final['error_stride4']]
titles=['All-source RSS reference','L1-wavelet; R_eff 1.77','L1-wavelet; R_eff 2.91','Image-intensity diagnostic ROI','Absolute difference; R_eff 1.77','Absolute difference; R_eff 2.91']
for i,(ax,im,title) in enumerate(zip(axes.ravel(),seq,titles)):
    ax.imshow(im,cmap='magma' if i>3 else 'gray',vmin=0,vmax=.25 if i>3 else (1 if i==3 else window),interpolation='nearest')
    ax.set_title(title,fontsize=10);ax.axis('off')
fig.suptitle('Same acquired human slice · fixed SigPy parameters · differences include source noise',fontsize=11)
fig.savefig(P/'final-inspection.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(5.3,2.8),constrained_layout=True)
for s,c in [(2,'#008b85'),(4,'#8263b0')]:
    ob=final[f'objective_stride{s}'];ax.semilogy(ob/ob[0],label=f'R_eff {results[str(s)]["effective_acceleration_vs_available_source"]:.2f}',color=c,lw=1.7)
ax.set_xlabel('Iteration');ax.set_ylabel('Objective / initial');ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False)
fig.savefig(P/'final-solver-objective.png',dpi=250);fig.savefig(P/'final-solver-objective.pdf');plt.close(fig)
report=initial.copy()
report['status']='Completed illustrative comparison with qualified findings; accelerated reconstructions are not asserted to meet a quality threshold'
report['initial_solver_diagnostic']='initial-sense-report.json; initial weakly L2-regularized SENSE outputs retained, not presented as validated success'
report['parameters']=dict(initial['parameters'],solver='SigPy L1WaveletRecon',wavelet='db4 (upstream default)',lambda_l1=.01,solver_max_iter=200,iteration_check_max_iter=400,random_seed=0,
    fixed_parameters='Original ESPIRiT map parameters retained. One fixed skill-example L1 weight .01 applied identically to both masks; no reference-driven per-mask parameter tuning. Additional400iterations assess convergence, not quality tuning.')
report['parameters'].pop('lambda_l2',None)
report['parameters'].pop('tolerance',None)
report['sampling_comparison']=results
report['checks']=dict(initial['checks'],source_PE_first=int(np.flatnonzero(source)[0]),source_PE_last=int(np.flatnonzero(source)[-1]),map_projection_residual_full_FOV=projection_residual_full,map_projection_residual_image_intensity_ROI=projection_residual_roi,
    ROI_description='Post-hoc diagnostic after reviewing the first SENSE results: DIPY median_otsu of source RSS (radius3,two passes), hole fill and2pixelerosion; same ROI for all methods. Not a prespecified endpoint or independently validated brain segmentation; full-FOV metrics remain primary descriptive results.',ROI_pixels=int(roi.sum()),
    calibration_exploration='source/calibration-diagnostic.json; larger SVD thresholds/widths did not justify a change to original parameters')
report['interpretation']='The higher retrospective acceleration has larger source-reference discrepancy for this fixed solver and slice. Full-FOV metrics include substantial low-field background noise and RSS bias; image-intensity-ROI metrics are post-hoc descriptive sensitivity analyses. The L1 reconstructions have larger full-FOV RSS discrepancy than zero-filled RSS baselines, so no reconstruction improvement is claimed. Measured/heldout residuals are not anatomical truth. No clinical, prospective acquisition or agent-superiority conclusion.'
report['outputs']={'scientific_arrays':'final-arrays.npz','reference':'reference-rss.png','compared_reconstructions':['final-reconstruction-stride2.png','final-reconstruction-stride4.png'],'differences':['final-error-stride2.png','final-error-stride4.png'],'review':'final-inspection.png'}
report['limitations'].append('Source-reference error and data residual include low-field noise, coil-model mismatch and regularization; root cause is not isolated by this single case')
(P/'report.json').write_text(json.dumps(report,indent=2))
source_dir=OUT/'source';source_dir.mkdir(exist_ok=True)
source_hashes={}
for name in ['README.md','DATA_CARD.md','H5_FORMAT.md','selected-acquisition.json','zenodo_record_8056074.json','selected-header.xml','file_inventory.tsv']:
    src=WORK/'source'/name;shutil.copy2(src,source_dir/name);source_hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest()
for name in ['calibration-diagnostic.json','l1-diagnostic.json']:
    if (WORK/name).exists():shutil.copy2(WORK/name,source_dir/name)
skills={}
for name in ['mri-reconstruction','mri-hardware','diffusion-mri','mri-research-workflow']:
    path=Path('/Users/kewang/.agents/skills')/name/'SKILL.md';skills[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'version':'0.8.0','actually_read_this_run':True}
trace=[
 {'stage':'Frame the request','action':'Prepare actual acquired-human-MRI materials for an MRFoundry paper; compare two retrospective sampling settings and return inspectable evidence.','status':'Current delegated execution; task wording is a concise summary, not an invented historical user quotation.'},
 {'stage':'Retrieve guidance','action':'Read installed reconstruction, hardware and diffusion skills plus scoped memory; inspect official SigPy and DIPY APIs. The research-workflow skill was consulted later during review and packaging.','evidence':'skill hashes in evidence.json; current conversation tool records'},
 {'stage':'Check reuse and inputs','action':'Exclude earlier acquired example with unresolved reuse rights. Select author-maintained M4Raw CC BY4.0 acquisition; verify SHA256 against manifest.','evidence':'source/zenodo_record_8056074.json and m4raw/report.json'},
 {'stage':'Resolve format and support','action':'Read official H5_FORMAT.md; use final-axis PE convention despite legacy XML reversal. Derive195acquired lines from actual nonzero support; report acceleration relative to195.','evidence':'source/H5_FORMAT.md; source/selected-header.xml; m4raw/arrays.npz'},
 {'stage':'Execute established tools','action':'SigPy centered FFT/RSS, ESPIRiT calibration and SENSE comparisons. Inspect actual outputs and high residuals; retain initial findings.','evidence':'m4raw/initial-sense-report.json and arrays.npz'},
 {'stage':'Bounded revision','action':'Retain original map parameters after calibration diagnostic. Apply one fixed SigPy L1-wavelet example weight to both masks, then check extra iterations, source-reference discrepancy and data consistency.','evidence':'m4raw/report.json; final-arrays.npz; source/calibration-diagnostic.json'},
 {'stage':'Interpret and document','action':'Separate noisy source reference, descriptive ROI and data-fit checks. No global pass, clinical claim or agent comparison. Save evidence-linked lesson.','evidence':'memory-note.md and evidence.json'},
 {'stage':'Cross-domain example','action':'Recompute DIPY tensor maps/residuals on three predetermined slices of licensed Stanford acquired HARDI; preserve source gradient and preprocessing limits.','evidence':'dwi/report.json and arrays.npz'}]
evidence={'date':'2026-10-27','host':'Codex desktop, local tool execution','model_version':'Not independently recorded; no specific model identifier claimed','benchmark':False,
'execution_scope':'Current agent-assisted, human-directed figure-material run; not a recovered historical transcript or fully autonomous efficacy evaluation',
'skills_read':skills,'source_document_hashes':source_hashes,'observable_stage_summary':trace,'primary_report':'m4raw/report.json','secondary_report':'dwi/report.json',
'commands':['OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 work/radial-gre-venv/bin/python -u work/mrfoundry-real-data-v19/run_m4raw.py','OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 work/radial-gre-venv/bin/python -u work/mrfoundry-real-data-v19/run_dwi.py','OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 work/radial-gre-venv/bin/python -u work/mrfoundry-real-data-v19/finalize_evidence.py'],
'failures_and_corrections':['First plotting attempt treated the ESPIRiT eigenvalue map as2D; upstream returned a leading singleton axis. Fixed with squeeze; numerical parameters unchanged.','One exploratory ROI command had a Python syntax typo; corrected before output.','DIPY median_otsu with explicit dilate=0 on a2D input triggered a3Dstructure mismatch; omitted dilation and documented subsequent2D erosion.','Initial weak-L2 SENSE outputs had high source discrepancy; retained and not treated as successful validated reconstruction.'],
'unexecuted':['Prospective scanner acquisition','Noise prewhitening/g-factor/pseudo-replica validation','Independent biological/clinical validation','Full preprocessing/gradient-frame validation of Stanford DWI','A later task actually retrieving/revalidating the saved lesson','With/without-skills agent benchmark']}
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2))
(OUT/'observable-stages.json').write_text(json.dumps(trace,indent=2))
note='''# Evidence-linked project lesson — acquired support is not stored matrix size

Status: observed in M4Raw Brain v1.6, validation acquisition2022061203_T201.h5, slice8; not a universal data-format rule.

## Evidence
- [Source contract](source/H5_FORMAT.md): native order is slice,coil,FE,PE; legacy custom XML reverses FE/PE for this contrast.
- [Actual checks](m4raw/report.json):256stored PE columns;195acquired nonzero columns. The retained110and67lines imply effective acceleration1.7727and2.9104 relative to available source lines.
- [Saved arrays](m4raw/final-arrays.npz) contain exact support and retrospective masks. The source RSS is noisy and uses available source support, not fully sampled/noise-free truth.

## Rule to reuse
Before comparing retrospective sampling settings, verify the source axis contract, derive or read actual acquisition support, define the denominator, preserve provenance, and label the reference accurately. Check both image differences and measured/heldout data agreement; do not promote a low residual or a pleasing picture to general validation.

## Revalidate on the next task
Dataset/release and file hash; header-to-array axis contract; nonzero/acquisition mask; whether data were preprocessed; metric reference; noise/coil assumptions. No later-task memory retrieval has been executed in this run.

## Limits
One low-field subject/slice, one4channel coil and fixed settings. Source-derived image-intensity ROI is a descriptive diagnostic. No scanner, biological or agent-performance validation. Keep initial SENSE diagnostics in the linked record.
'''
(OUT/'memory-note.md').write_text(note)
print('Evidence package written',OUT,flush=True)
