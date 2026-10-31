"""Convention tests for mrfoundry_reconlib (python test_reconlib.py)."""
import os,sys
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mrfoundry_reconlib import *
n=24;fov=0.2;rng=np.random.default_rng(0);img=np.zeros((n,n));img[5:9,3:7]=1;img[15:18,14:20]=0.6;img[2,20]=2.0
j,i=np.mgrid[0:n,0:n];k=np.stack([(i-n//2)/fov,(j-n//2)/fov],-1)
s=direct_dft(img,k,fov);rec=cartesian_image(s)
assert np.allclose(rec.real,img,atol=1e-9) and abs(rec.imag).max()<1e-9;print('cartesian_image matches direct DFT (orientation and centring)')
try:
    import sigpy  # noqa
    ang=np.arange(40)*np.deg2rad(111.246117975);r=(np.arange(48)-24)/fov
    kr=np.stack([np.outer(np.cos(ang),r),np.outer(np.sin(ang),r)],-1);sr=direct_dft(img,kr,fov)
    est,res=nufft_least_squares(sr,kr,fov,(n,n),lamda=1e-6,max_iter=300)
    pred=direct_dft(est,kr,fov);e=np.linalg.norm(pred-sr)/np.linalg.norm(sr);c=np.corrcoef(abs(est).ravel(),img.ravel())[0,1]
    assert e<0.02 and c>0.95,(e,c);print('nufft_least_squares consistent with direct DFT: data residual %.2e, image corr %.3f'%(e,c))
except ImportError:print('sigpy not installed: NUFFT test skipped')



# B6: off-resonance-corrected spiral reconstruction with the exact encoding (field map known)
n2 = 32; fov2 = 0.2; obj2 = np.zeros((n2, n2)); obj2[6:14, 5:12] = 1.0; obj2[18:27, 16:26] = 0.7; obj2[3, 25] = 2.0
yy2, xx2 = np.mgrid[0:n2, 0:n2] / n2 - 0.5
fmap = 150 * (xx2 + 0.6 * yy2 ** 2 - 0.2)                                          # Hz, smooth
ns = 3000; tt = np.arange(ns) * 4e-6; kmax = n2 / (2 * fov2)
turns = n2 / 2 * 1.3; th = 2 * np.pi * turns * np.sqrt(np.arange(ns) / ns)
kk = np.stack([kmax * np.sqrt(np.arange(ns) / ns) * np.cos(th), kmax * np.sqrt(np.arange(ns) / ns) * np.sin(th)], -1)
t_from_exc = 3e-3 + tt
clean2 = offres_encoding(kk, t_from_exc, fmap, fov2, phase_sign=-1).astype(complex) @ obj2.ravel()
data2 = clean2 + 0.002 * np.abs(clean2).max() * (rng.normal(size=ns) + 1j * rng.normal(size=ns))
def cerr(a, ref):
    s = np.vdot(a.ravel(), ref.ravel()) / np.vdot(a.ravel(), a.ravel()); return float(np.linalg.norm(s * a - ref) / np.linalg.norm(ref))
oracle, _ = offres_least_squares(clean2, kk, t_from_exc, fmap, fov2, phase_sign=-1, lamda=1e-2)
corr, res = offres_least_squares(data2, kk, t_from_exc, fmap, fov2, phase_sign=-1, lamda=1e-2)
nocorr, _ = offres_least_squares(data2, kk, t_from_exc, 0 * fmap, fov2, lamda=1e-2)
wrong, _ = offres_least_squares(data2, kk, t_from_exc, fmap, fov2, phase_sign=+1, lamda=1e-2)
assert cerr(corr, oracle) < 0.05 and cerr(nocorr, oracle) > 0.3 and cerr(wrong, oracle) > 0.3, (cerr(corr, oracle), cerr(nocorr, oracle), cerr(wrong, oracle))
print('offres_least_squares: complex NRMSE vs the noise-free exact reconstruction %.3f (no field %.2f, wrong phase sign %.2f)'
      % (cerr(corr, oracle), cerr(nocorr, oracle), cerr(wrong, oracle)))
lin = 40 + 3.0 * (np.arange(n2)[None, :] - 10) - 2.0 * (np.arange(n2)[:, None] - 12) + 0 * obj2   # linear field (Hz)
w2 = (obj2 > 0).astype(float)
s1 = smooth_field(np.where(w2 > 0, lin, 0.0), w2, 1.5); s0 = smooth_field(np.where(w2 > 0, lin, 0.0), w2, 1.5, order=0)
e1 = np.abs(s1 - lin)[w2 > 0].max(); e0 = np.abs(s0 - lin)[w2 > 0].max()
assert e1 < 1e-3 and e0 > 1.0, (e1, e0)
noisy_f = lin + rng.normal(0, 2.0, lin.shape)
sn = smooth_field(np.where(w2 > 0, noisy_f, 0.0), w2, 1.0)
assert np.std((sn - lin)[w2 > 0]) < 0.75 * np.std((noisy_f - lin)[w2 > 0])
print('smooth_field (local plane): linear field exact at edges (plain weighted mean off by %.1f Hz); noise SD reduced %.2fx'
      % (e0, np.std((noisy_f - lin)[w2 > 0]) / np.std((sn - lin)[w2 > 0])))
