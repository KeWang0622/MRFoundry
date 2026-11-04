"""Join actual scoped checks for a quantitative table; no new experiments."""
from pathlib import Path
import json, hashlib, shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'outputs/mrm-toolbox/sequence-evidence-v22'
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()

S='outputs/mrm-toolbox/sequence-evidence-v22/sequence-audit.json'
R='outputs/mrm-toolbox/real-data-v19/m4raw/report.json'
D='outputs/mrm-toolbox/real-data-v19/dwi/report.json'
s,r,d=read(S),read(R),read(D)
table=[
 {'workflow':'Sequence design','evidence_status':'Prior exported prototype; fresh read-only audit',
  'setting':{'spokes':128,'samples_per_spoke':64,'dummy_TRs':200,'TE_ms':5,'TR_ms':15},
  'readouts':{'timing_errors':s['checks']['timing_error_count'],
              'max_component_gradient_mTm':s['checks']['max_per_axis_gradient_mTm'],
              'max_component_slew_T_m_s':s['checks']['max_per_axis_slew_T_m_s']},
  'comparison':{'configured_max_gradient_mTm':32,'configured_max_slew_T_m_s':130},
  'scope':'Programmed per-axis checks; no scanner/PNS/SAR validation','source':S},
 {'workflow':'Bloch simulation','evidence_status':'Prior KomaMRI run; saved-array scalar recheck only',
  'setting':{'coarse_phantom_spins':13497,'RF_steps_us':[10,5],'ADC_samples':8192},
  'readouts':{'relative_signal_change':s['saved_simulation_array_check']['RF_step_relative_signal_change']},
  'definition':'norm(S5us-S10us)/norm(S5us), all8192complexsamples',
  'scope':'Temporal sensitivity on the same coarse phantom; not spatial convergence','source':S},
]
for stride in ['2','4']:
    x=r['sampling_comparison'][stride]
    table.append({'workflow':'Acquired-data reconstruction','evidence_status':'Recorded current human-supervised demonstration',
      'setting':{'source':'M4Raw','slice_zero_based':8,'available_PE_lines':195,
                 'retained_PE_lines':x['retained_lines'],
                 'effective_acceleration':x['effective_acceleration_vs_available_source']},
      'readouts':{'magnitude_NRMSE_vs_all_source_RSS':x['all_source_rss_nrmse'],
                  'measured_data_residual':x['measured_data_residual'],
                  'source_withheld_data_residual':x['heldout_source_data_residual']},
      'comparison':{'zero_filled_RSS_NRMSE':x['zero_filled_rss_nrmse']},
      'scope':'One acquired slice; noisy all-source reference, not anatomical truth or reconstruction gain','source':R})
for z in ['30','38','46']:
    x=d['metrics_by_slice'][z]
    table.append({'workflow':'Diffusion tensor analysis','evidence_status':'Recorded current human-supervised demonstration',
      'setting':{'source':'Stanford HARDI','slice_zero_based':int(z),'mask_voxels':x['mask_voxels'],
                 'volumes':160},
      'readouts':{'median_relative_signal_residual':x['median_relative_signal_residual']},
      'definition':'Median within2Dmask of norm(Sfit-Smeas)/norm(Smeas) acrossall160volumes',
      'scope':'One acquired subject; descriptive model agreement, not biological or gradient-frame validation','source':D})

evidence={
 'purpose':'Task-specific numerical evidence for Figure3 sequence design and quantitativeTable2',
 'current_operation':'Re-read existing exported.seq with PyPulseq; inspect previously saved simulation arrays and frozen reports',
 'no_new_simulator_or_reconstruction_run':True,
 'sequence_audit':S,'table_rows':table,
 'metric_comparability':'Rows describe heterogeneous checks. They are not interchangeable accuracy scores, agent-performance measures, success rates or causal comparisons.',
 'source_hashes':{p:sha(p) for p in [S,R,D,'outputs/golden-angle-gre/golden_angle_radial_gre.seq',
                  'outputs/golden-angle-gre/koma_signal.npz','outputs/golden-angle-gre/koma_report.json']},
 'commands':[
  'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 work/radial-gre-venv/bin/python work/sequence-evidence-v22/extract_sequence_evidence.py',
  'work/radial-gre-venv/bin/python work/sequence-evidence-v22/compile_evidence.py'],
 'host':'Codex desktop; no historical Claude Code execution claimed',
 'historical_data_dates':{'sequence_design_and_simulation':'2026-09-23','acquired_demonstrations':'2026-10-27'},
 'audit_date':'2026-10-28',
 'current_skill':s['current_skill_read'],
 'recommended_layout':{'columns':['Workflow','Evaluated setting','Numerical readout','Reference / scope'],
   'grouping':'Sequence, simulation, two reconstruction masks, three diffusion slices; use one shared scope note per group.'},
}
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
source_dir=OUT/'source';source_dir.mkdir(exist_ok=True)
for name in ['golden_angle_radial_gre.seq','design_report.json','koma_report.json','design_sequence.py']:
    shutil.copy2(ROOT/'outputs/golden-angle-gre'/name,source_dir/name)
for name in ['extract_sequence_evidence.py','compile_evidence.py']:
    shutil.copy2(Path(__file__).parent/name,OUT/name)
print(OUT/'evidence.json')
