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

