"""Repeatable tensor summary on acquired Stanford HARDI; no synthetic anatomy."""
from pathlib import Path
import hashlib,json,sys,platform
import numpy as np
import nibabel as nib
import dipy
from dipy.core.gradients import gradient_table
from dipy.reconst.dti import TensorModel,fractional_anisotropy,mean_diffusivity
from dipy.segment.mask import median_otsu
from scipy.ndimage import binary_fill_holes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
INP=ROOT/'work/figure-v4/data'
OUT=ROOT/'outputs/mrm-toolbox/real-data-v19/dwi';OUT.mkdir(parents=True,exist_ok=True)
expected={'dwi.nii.gz':'0b18513b46132b4d1051ed3364f2acbc','dwi.bvals':'4e08ee9e2b1d2ec3fddb68c70ae23c36','dwi.bvecs':'4c63a586f29afc6a48a5809524a76cb4'}
hashes={}
for f,md5 in expected.items():
    b=(INP/f).read_bytes();assert hashlib.md5(b).hexdigest()==md5
    hashes[f]={'md5':md5,'sha256':hashlib.sha256(b).hexdigest()}
image=nib.load(INP/'dwi.nii.gz');data=image.get_fdata(dtype=np.float32)
b=np.loadtxt(INP/'dwi.bvals');g=np.loadtxt(INP/'dwi.bvecs');g=g.T if g.shape[0]==3 else g
assert len(b)==len(g)==data.shape[-1] and np.isfinite(data).all()
norm=np.linalg.norm(g[b>50],axis=1);assert np.allclose(norm,1,atol=.01)
assert nib.aff2axcodes(image.affine)==('R','A','S')
gtab=gradient_table(b,bvecs=g,b0_threshold=50)
b0=data[...,b<=50].mean(-1)
_,mask3=median_otsu(b0,median_radius=3,numpass=1,autocrop=False,dilate=1)
zlist=[30,38,46];arrays={'bvals':b,'bvecs':g,'affine':image.affine};metrics={}
for z in zlist:
    d=data[:,:,z,:];m=binary_fill_holes(mask3[:,:,z]);fit=TensorModel(gtab,fit_method='WLS').fit(d,mask=m)
    fa=np.nan_to_num(fractional_anisotropy(fit.evals));md=mean_diffusivity(fit.evals)
    predicted=fit.predict(gtab,S0=b0[:,:,z]);res=np.linalg.norm(predicted-d,axis=-1)/np.maximum(np.linalg.norm(d,axis=-1),1)
    assert np.isfinite(fa).all() and np.isfinite(md).all() and fa[m].min()>=0 and fa[m].max()<=1+1e-6
    arrays.update({f'b0_z{z}':b0[:,:,z],f'fa_z{z}':fa,f'md_z{z}':md,f'residual_z{z}':res,f'mask_z{z}':m})
    metrics[str(z)]={'mask_voxels':int(m.sum()),'median_relative_signal_residual':float(np.median(res[m])),'residual_p10_p90':np.percentile(res[m],[10,90]).tolist(),'FA_range_in_mask':[float(fa[m].min()),float(fa[m].max())],'MD_range_mm2_s':[float(md[m].min()),float(md[m].max())]}
scale=float(np.percentile(arrays['b0_z38'][arrays['mask_z38']],99))
def disp(a):return np.flipud(a.T) # sourceRAS => screenleftL/rightR/topA
def save(a,name,vmax,cmap='gray',m=None):
    rgb=plt.get_cmap(cmap)(np.clip(disp(a)/vmax,0,1))[...,:3]
    if m is not None:rgb[~disp(m)]=0
    Image.fromarray(np.uint8(rgb*255)).resize((81*6,106*6),Image.Resampling.NEAREST).save(OUT/(name+'.png'))
for z in zlist:
    m=arrays[f'mask_z{z}']
    save(arrays[f'b0_z{z}'],f'b0-z{z}',scale)
    save(arrays[f'fa_z{z}'],f'fa-z{z}',1,m=m)
    save(arrays[f'md_z{z}'],f'md-z{z}',.003,'magma',m)
    save(arrays[f'residual_z{z}'],f'residual-z{z}',.20,'magma',m)
z=38
fig,ax=plt.subplots(1,4,figsize=(10,3.7),constrained_layout=True)
for axis,key,title,vmax,cmap in zip(ax,['b0','fa','md','residual'],['Acquired mean b=0','Fractional anisotropy','Mean diffusivity','Signal-fit residual'],[scale,1,.003,.20],['gray','gray','magma','magma']):
    a=disp(arrays[f'{key}_z{z}']).copy()
    if key!='b0':a[~disp(arrays[f'mask_z{z}'])]=0
    im=axis.imshow(a,cmap=cmap,vmin=0,vmax=vmax,interpolation='nearest');axis.set_title(title,fontsize=10);axis.axis('off')
    if key!='b0':fig.colorbar(im,ax=axis,shrink=.55,pad=.02,label='mm²/s' if key=='md' else 'fraction')
fig.suptitle('Acquired Stanford HARDI · native axial slice 38 · screen L–R; anterior at top',fontsize=11)
fig.savefig(OUT/'inspection.png',dpi=200);plt.close(fig)
np.savez_compressed(OUT/'arrays.npz',**arrays)
source_xml=(INP/'stanford-record.xml').read_bytes();(OUT/'stanford-record.xml').write_bytes(source_xml)
report={'task':'Inspect acquired diffusion data, fit a tensor summary, and report the maps with fit checks and interpretation limits.',
'source':{'name':'Stanford HARDI','url':'https://purl.stanford.edu/yx282xq2090','authors':'Rokem, Yeatman, Pestilli and Wandell (2013)','license':'Open Data Commons Public Domain Dedication and License1.0','license_url':'https://opendatacommons.org/licenses/pddl/1-0/','data_urls':['https://stacks.stanford.edu/file/druid:yx282xq2090/'+f for f in expected],'hashes':hashes,'source_record_sha256':hashlib.sha256(source_xml).hexdigest()},
'input':{'acquired_human_data':True,'raw_kspace':False,'shape':list(data.shape),'voxel_mm':list(map(float,image.header.get_zooms()[:3])),'native_axes':['R','A','S'],'b0_count':int(sum(b<=50)),'DW_count':int(sum(b>50)),'b_values_s_mm2':list(map(float,np.unique(b))),'direction_norm_range':[float(norm.min()),float(norm.max())],'preprocessing':'Provider already applied motion correction to meanb0 with SPM/mrVista. No new preprocessing here.'},
'method':{'DIPY':dipy.__version__,'fit':'TensorModel WLS','mask':'median_otsu(radius3,numpass1,dilate1), holes filled independently per displayed axial slice','slices_zero_based':zlist,'prediction_S0':'Mean of10b0 volumes','residual':'L2(Sfit-Smeasured)/L2(Smeasured) pervoxel; all160volumes'},
'metrics_by_slice':metrics,
'display':{'b0_window':[0,scale],'FA_window':[0,1],'MD_window_mm2_s':[0,.003],'residual_window':[0,.20],'native_render':'flipud(array.T) fromsourceRAS; leftL,rightR,topA','orientation_labels_supported_by_affine':True,'PNG':'nearest-neighbor6x enlargement; no generated detail','isotropic_in_plane_mm':2,'b0_common_window_across_slices':True},
'software':{'python':sys.version,'dipy':dipy.__version__,'numpy':np.__version__,'nibabel':nib.__version__,'platform':platform.platform()},
'limitations':['Illustrative tensor summary on one acquired subject; b=2000s/mm2 is not an optimal conventional DTI protocol','No susceptibility/eddy correction or independent verification of the source preprocessing and gradient frame','Unit-norm and volume-count checks do not establish correct bvector-to-anatomy alignment','Fit residual is model agreement, not a pass/fail clinical threshold','No tractography, group statistics, biological diagnosis or agent-performance benchmark']}
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(metrics,indent=2))
