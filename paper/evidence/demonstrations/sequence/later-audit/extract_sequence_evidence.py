"""Re-read the existing Pulseq prototype; export scientific figure material.

No sequence redesign, simulator execution, or new image reconstruction occurs.
Scientific trajectories and waveforms come from installed PyPulseq APIs.
"""
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np
import pypulseq as pp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'outputs/golden-angle-gre'
OUT = ROOT / 'outputs/mrm-toolbox/sequence-evidence-v22'
OUT.mkdir(parents=True, exist_ok=True)
SEQ = SRC / 'golden_angle_radial_gre.seq'

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

source_hash = digest(SEQ)
system = pp.Opts(max_grad=32, grad_unit='mT/m', max_slew=130,
                 slew_unit='T/m/s', rf_dead_time=100e-6,
                 rf_ringdown_time=20e-6, adc_dead_time=10e-6)
seq = pp.Sequence(system)
seq.read(str(SEQ))
timing_ok, timing_errors = seq.check_timing()
k_adc, k_full, excitation, refocusing, t_adc = seq.calculate_kspace()
excitation, t_adc = np.asarray(excitation), np.asarray(t_adc)
duration, n_blocks, event_counts = seq.duration()
dummy = int(seq.definitions['NumDummy'])
tr = float(seq.definitions['TR'])
fov = np.asarray(seq.definitions['FOV'])

adc_events, rf_events = [], []
t_block = 0.0
for b in seq.block_events:
    block = seq.get_block(b)
    if block.adc is not None:
        a = block.adc
        adc_events.append(dict(start_s=t_block + a.delay,
                               end_s=t_block + a.delay + a.dwell*a.num_samples,
                               samples=int(a.num_samples), dwell_s=float(a.dwell),
                               phase_offset_rad=float(a.phase_offset)))
    if block.rf is not None:
        r = block.rf
        # Pulseq RF samples are in Hz. This is nominal on-resonance pulse area,
        # not a Bloch-derived achieved flip under a tissue or off-resonance model.
        nominal_flip = 360*abs(np.sum(r.signal))*seq.rf_raster_time
        rf_events.append(dict(start_s=t_block+r.delay,
                              phase_offset_rad=float(r.phase_offset),
                              nominal_flip_deg=float(nominal_flip)))
    t_block += seq.block_durations[b]

n_spokes = len(adc_events)
n_adc = adc_events[0]['samples']
assert all(a['samples'] == n_adc for a in adc_events)
assert k_adc.shape == (3, n_spokes*n_adc)
assert timing_ok and not timing_errors
start = dummy*tr
three = seq.waveforms(append_RF=True, time_range=[start, start+3*tr])
all_grad = seq.waveforms()
peak_g = [float(np.max(np.abs(w[1]))/system.gamma*1e3) for w in all_grad]
peak_s = []
for w in all_grad:
    dt, dv = np.diff(w[0]), np.diff(w[1])
    assert np.all(dt > 0)
    peak_s.append(float(np.max(np.abs(dv/dt))/system.gamma))
assert max(peak_g) < 32 and max(peak_s) < 130
te_ms = (t_adc.reshape(n_spokes,n_adc)[:,n_adc//2]-excitation[dummy:])*1e3
tr_ms = np.diff(excitation)*1e3
historic = np.load(SRC/'trajectory.npz')
export_vs_prewrite = float(np.max(np.abs(k_adc-historic['k_adc'])))
angles = np.mod(np.arctan2(k_adc[1,n_adc-1::n_adc],k_adc[0,n_adc-1::n_adc]),np.pi)
angle_increments = np.mod(np.diff(angles),np.pi)*180/np.pi

def crop_wave(w, stop):
    t, v = np.real(w[0]), w[1]
    keep = (t > start) & (t < stop)
    xx = np.r_[start,t[keep],stop]
    yy = np.interp(xx,t,v,left=0,right=0)
    return (xx-start)*1e3, yy

arrays = dict(k_adc_cycles_m=k_adc, t_adc_s=t_adc,
              excitation_s=excitation, angles_rad=angles,
              adc_start_s=np.array([a['start_s'] for a in adc_events]),
              adc_end_s=np.array([a['end_s'] for a in adc_events]))
waveform_json = {'time_origin_s':start, 'time_range_ms':[0,45],
                 'source':'PyPulseq Sequence.waveforms from unchanged exported .seq',
                 'tracks':{}, 'adc_events':adc_events[:3]}
for i, channel in enumerate(['gx','gy','gz','rf']):
    xx, yy = crop_wave(three[i],start+3*tr)
    units = 'mT/m' if i<3 else 'Hz'
    vv = np.real(yy)/system.gamma*1e3 if i<3 else np.abs(yy)
    arrays[channel+'_time_ms'] = xx
    arrays[channel+('_mTm' if i<3 else '_magnitude_Hz')] = vv
    waveform_json['tracks'][channel] = {'units':units,'time_ms':xx.tolist(),'values':vv.tolist()}
np.savez_compressed(OUT/'sequence-arrays.npz',**arrays)
(OUT/'waveforms-first-three-TR.json').write_text(json.dumps(waveform_json))

report = {
 'operation':'Fresh PyPulseq read/timing/trajectory audit of prior exported prototype; no redesign or new simulation',
 'audit_date':'2026-10-28', 'historical_design_and_simulation_date':'2026-09-23',
 'sequence_path':str(SEQ.relative_to(ROOT)), 'sequence_sha256':source_hash,
 'software':{'pypulseq':pp.__version__,'numpy':np.__version__,
             'python':sys.version,'platform':platform.platform()},
 'configured_per_axis_limits':{'gradient_mTm':32,'slew_T_m_s':130,
   'source':'Original design_sequence.py; reapplied to reader. Not scanner hardware certification.'},
 'sequence':{'simulation_only':True,'fov_mm':(fov*1000).tolist(),
   'spokes':n_spokes,'adc_samples_per_spoke':n_adc,'adc_samples_total':int(t_adc.size),
   'adc_dwell_us':adc_events[0]['dwell_s']*1e6,
   'dummy_excitations':dummy,'rf_excitations':len(rf_events),
   'nominal_flip_deg_from_first_RF_integral':rf_events[0]['nominal_flip_deg'],
   'te_ms_min_mean_max':[float(te_ms.min()),float(te_ms.mean()),float(te_ms.max())],
   'tr_ms_min_mean_max':[float(tr_ms.min()),float(tr_ms.mean()),float(tr_ms.max())],
   'duration_s':float(duration),'sampled_train_duration_s':n_spokes*tr,
   'first_sampled_TR_start_s':start,'blocks':n_blocks,
   'golden_angle_definition_deg':float(seq.definitions['GoldenAngleDeg']),
   'readback_spoke_increment_min_max_deg':[float(angle_increments.min()),float(angle_increments.max())]},
 'checks':{'pypulseq_timing_pass':bool(timing_ok),'timing_error_count':len(timing_errors),
   'peak_gradient_per_axis_mTm':peak_g,'peak_slew_per_axis_T_m_s':peak_s,
   'max_per_axis_gradient_mTm':max(peak_g),'max_per_axis_slew_T_m_s':max(peak_s),
   'gradient_fraction_of_configured_limit':max(peak_g)/32,
   'slew_fraction_of_configured_limit':max(peak_s)/130,
   'readback_vs_saved_prewrite_trajectory_max_abs_cycles_m':export_vs_prewrite,
   'all_trajectory_values_finite':bool(np.isfinite(k_adc).all()),
   'trajectory_z_max_abs_cycles_m':float(np.max(np.abs(k_adc[2])))},
 'historic_simulation':json.loads((SRC/'koma_report.json').read_text()),
 'historic_simulation_provenance':{'report':str((SRC/'koma_report.json').relative_to(ROOT)),
   'sha256':digest(SRC/'koma_report.json'),'new_simulation_performed':False},
 'limitations':['Simulation-only prototype, not an acquired human dataset.',
   'Gradient/slew checks are per-axis programmed waveform checks against configured limits, not measured scanner output.',
   'No PNS, SAR, heating, vendor-interpreter, gradient-delay or eddy-current validation.',
   'Coarse-phantom RF-step sensitivity is not spatial or full physical-model convergence.',
   'Historical dense quadrature and reconstruction checks are separate from the present waveform audit.',
   'No agent benchmark, runtime improvement or fully autonomous success claim.'],
 'current_skill_read':{'path':'/Users/kewang/.agents/skills/pulse-sequence-design/SKILL.md',
   'sha256':digest('/Users/kewang/.agents/skills/pulse-sequence-design/SKILL.md'),
   'scope':'Read for this evidence audit; no retroactive claim of its historical retrieval.'},
 'source_references':[
   'https://github.com/pulseq/pypulseq',
   'https://github.com/pulseq/pypulseq/blob/master/examples/scripts/write_radial_gre.py',
   'https://doi.org/10.1109/TMI.2006.885337',
   'https://publikationen.bibliothek.kit.edu/1000006342',
   'https://github.com/JuliaHealth/KomaMRI.jl']
}

# Recompute ONLY scalar summaries from existing saved simulation arrays.
# This inspects the historical simulator output; it does not invoke a simulator.
sim = np.load(SRC/'koma_signal.npz')
fine, coarse = sim['signal'], sim['signal_rf10us']
report['saved_simulation_array_check'] = {
 'source':str((SRC/'koma_signal.npz').relative_to(ROOT)),
 'source_sha256':digest(SRC/'koma_signal.npz'),
 'shape':list(fine.shape),'finite':bool(np.isfinite(fine).all()),
 'nonzero_sample_count':int(np.count_nonzero(fine)),
 'RF_step_relative_signal_change':float(np.linalg.norm(fine-coarse)/np.linalg.norm(fine)),
 'definition':'L2(S_5us-S_10us)/L2(S_5us); same saved coarse phantom, entire128x64signal',
 'not_a_new_simulation':True}
np.savez_compressed(OUT/'historical-signal-display.npz',magnitude=np.abs(fine),
                    normalization_max=float(np.abs(fine).max()))

plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.linewidth':.7,
 'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,
 'svg.fonttype':'none','savefig.facecolor':'white'})
C = dict(rf='#6955A3',gx='#2467B0',gy='#227C78',gz='#5F6C7B',adc='#6955A3')
def save_fig(fig,name):
    for fmt in ['pdf','svg','png']:
        fig.savefig(OUT/(name+'.'+fmt),dpi=300)
    plt.close(fig)

for ntr in [1,3]:
    end = ntr*tr*1000
    fig, axs = plt.subplots(5,1,figsize=(4.8,3.3),sharex=True,
                            gridspec_kw={'height_ratios':[1.05,1,1,1,.6]})
    for i,ch in enumerate(['rf','gx','gy','gz']):
        ax=axs[i]; d=waveform_json['tracks'][ch]
        ax.plot(d['time_ms'],d['values'],color=C[ch],lw=1.1)
        ax.axhline(0,color='#CBD5E1',lw=.5,zorder=0)
        ax.set_ylabel({'rf':'RF\n(Hz)','gx':'Gx\n(mT/m)','gy':'Gy\n(mT/m)','gz':'Gz\n(mT/m)'}[ch],
                      rotation=0,ha='right',va='center',labelpad=10)
        ax.tick_params(labelsize=7,length=2.5,width=.6,pad=2)
        ax.set_yticks([0,40] if ch=='rf' else ([0,12] if ch=='gz' else [-5,5]))
        ax.set_xlim(0,end)
    for a in adc_events[:ntr]:
        lo,hi=(a['start_s']-start)*1000,(a['end_s']-start)*1000
        axs[-1].plot([lo,lo,hi,hi],[0,1,1,0],color=C['adc'],lw=1.1)
        samples=t_adc[(t_adc>=a['start_s'])&(t_adc<a['end_s'])]
        axs[-1].vlines((samples-start)*1000,0,.55,color=C['adc'],lw=.4)
    axs[-1].set_ylabel('ADC',rotation=0,ha='right',va='center',labelpad=10)
    axs[-1].set_ylim(-.15,1.3);axs[-1].set_yticks([])
    axs[-1].set_xlabel('Time from first sampled TR (ms)')
    axs[-1].set_xticks(np.arange(0,end+1,5 if ntr==1 else 15))
    for ax in axs:
        if ntr==3:
            for boundary in [15,30]:ax.axvline(boundary,color='#DDE3EA',lw=.7,ls='--')
    fig.subplots_adjust(left=.18,right=.985,top=.98,bottom=.13,hspace=.16)
    save_fig(fig,f'waveforms-{ntr}-TR')

fig, ax=plt.subplots(figsize=(2.6,2.6))
for j in range(n_spokes):
    kk=k_adc[:2,j*n_adc:(j+1)*n_adc]
    ax.plot(kk[0],kk[1],color='#D5DDE6',lw=.45,zorder=1)
for j,col in enumerate([C['gx'],C['rf'],C['gy']]):
    kk=k_adc[:2,j*n_adc:(j+1)*n_adc]
    ax.plot(kk[0],kk[1],color=col,lw=1.3,zorder=2)
ax.set_aspect('equal');ax.set(xlabel=r'$k_x$ (cycles/m)',ylabel=r'$k_y$ (cycles/m)')
ax.set_xticks([-150,0,150]);ax.set_yticks([-150,0,150]);ax.tick_params(labelsize=7)
fig.subplots_adjust(left=.21,right=.98,top=.98,bottom=.2)
save_fig(fig,'trajectory-128-spokes')

assert digest(SEQ)==source_hash, 'Original sequence must remain unchanged'
(OUT/'sequence-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'sources.json').write_text(json.dumps({str(p.relative_to(ROOT)):digest(p) for p in [
    SEQ,SRC/'design_sequence.py',SRC/'design_report.json',SRC/'trajectory.npz',
    SRC/'koma_report.json',SRC/'koma_signal.npz',SRC/'dense/reconstruction_report.json',
    ROOT/'.mrfoundry/runs/2026-09-23-golden-angle-gre.md']},indent=2)+'\n')
print(json.dumps({'output':str(OUT),'timing_ok':timing_ok,'max_grad_mTm':max(peak_g),
                  'max_slew_T_m_s':max(peak_s),'TE_ms':float(te_ms.mean()),
                  'TR_ms':float(tr_ms.mean()),'samples':int(t_adc.size),
                  'roundtrip_k_error':export_vs_prewrite},indent=2))
