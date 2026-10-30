"""Self-test for spectrum_fit.py (python test_spectrum_fit.py): an unregularized fine-grid NNLS
spectrum should recover a low-diffusivity fraction worse than a few well-separated compartments."""
import os,sys
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from spectrum_fit import *
b=np.array([0]*2+[100]*3+[500]*6+[1000]*6+[2000]*6+[3000]*6,float);cut=0.5e-3
def truth(rng,n,b):
    grid=np.geomspace(1e-5,4e-3,300);f=rng.dirichlet([2,4,2],n)
    def logn(med,s):w=np.exp(-.5*((np.log(grid)-np.log(med))/s)**2);return w/w.sum()
    comp=np.stack([logn(0.2e-3,.4),logn(1.1e-3,.25),logn(2.8e-3,.08)])
    w=f@comp;return w@np.exp(-np.outer(grid,b)),(w[:,grid<cut]).sum(1)
few=[0.0,0.3e-3,1.2e-3,3.0e-3];fine=np.geomspace(5e-5,3.2e-3,60)
r_few=recovery_test(truth,lambda M,b:fraction_below(fit_weights(M,b,few),few,cut),b,sigma=0.03,n=600)
r_fine=recovery_test(truth,lambda M,b:fraction_below(fit_weights(M,b,fine),fine,cut),b,sigma=0.03,n=600)
r_reg=recovery_test(truth,lambda M,b:fraction_below(fit_weights(M,b,fine,lam=0.05,smooth=True),fine,cut),b,sigma=0.03,n=600)
print('few compartments',r_few);print('fine grid, no regularization',r_fine);print('fine grid, smoothness-regularized',r_reg)
assert r_few['sd']<r_fine['sd'] and r_reg['sd']<r_fine['sd'],'expected regularization or few compartments to reduce spread'
print('ok')

