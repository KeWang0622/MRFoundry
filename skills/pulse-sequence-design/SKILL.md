---
name: pulse-sequence-design
description: >-
  Read before designing, exporting or simulating an MRI acquisition: pulse
  sequences, RF and gradient waveforms, k-space trajectories (Cartesian,
  radial, spiral, EPI), Pulseq/PyPulseq files and Bloch simulation of the
  export. Prevents silent errors in realized TE/TR/TI and echo spacing,
  sampling and coverage requirements, spoiling and receive phase, gradient
  continuity, slice selection, steady state and delivered simulations that
  differ from a fresh simulation of the file. Ships tested builders, an
  exported-sequence checker, a KomaMRI replay check and an end-to-end example.
metadata:
  author: Ke Wang
  version: "0.14.0"
---

# MRFoundry: Pulse Sequence and Trajectory Design

Prototype vendor-neutrally with PyPulseq. Treat the build script as a claim and the exported `.seq` as the
evidence: measure the export, simulate the export, reconstruct from the simulation of the export.

## Fast path (sequence -> Bloch simulation -> reconstruction -> report)

1. **Simulator first** (it takes minutes): `pip install pypulseq sigpy matplotlib komamripy`, then start
   `python .agents/skills/pulse-sequence-design/scripts/test_seqlib.py > warmup.log 2>&1 &` (installs Julia +
   KomaMRI; keep logs in the workspace, /tmp may be read-only). If no Julia appears within about 3 minutes (empty
   log, a juliapkg lock wait, an install error), stop it and run
   `sh .agents/skills/pulse-sequence-design/scripts/setup_koma_julia.sh > koma.log 2>&1 &` (Julia 1.10 +
   KomaMRICore in ./koma_julia), then `simulate_with_koma(..., backend='julia')` with the paths it prints. Both
   backends give the same signal. Deliver KomaMRI output only: MRzero, EPG, homemade Bloch code and ideal-signal
   formulas have not matched KomaMRI replays of the same file (scale, sign and timing conventions differ).
2. Copy `scripts/example_pipeline.py` (build, read back, waveform figure, simulation of the exported file,
   archive with hashes, replay check, standalone reconstruction, orientation check, report) and swap in a family
   builder: spoiled GRE in `scripts/test_seqlib.py`; inversion-recovery GRE, balanced SSFP, spin echo, CPMG and
   EPI in `scripts/test_check_exported_seq.py`. Helpers (`mrfoundry_seqlib.py --api`): `make_system`,
   `slice_selective_excitation` (`center_shift`), `centered_readout` and `add_epi_readout` (`oversample`, `extra`,
   `adc_shift`), `split_interval`, `fill_delay`, `RFSpoiler`, `spoiler_area`, `kspace_grid`, `simulate_with_koma`,
   `replay_check`, `plot_waveforms`.
3. Run the checker with EVERY requested parameter until all lines PASS and NOT CHECKED is empty; verify each
   VERIFY SEPARATELY item yourself or by simulating the exported file (`--help` lists the flags; do not read the source):
   `python .agents/skills/pulse-sequence-design/scripts/check_exported_seq.py sequence.seq --te ... --matrix NX NY --fov F ...`
4. Simulate the exact file you deliver and save the samples as returned (KomaMRI gives sum rho exp(-2 pi i k.r)
   with pypulseq's k: never conjugate, rescale or reorder them). Before finishing, run
   `replay_check(seq, delivered, x, y, z, rho, T1, T2)`: it re-simulates the delivered file from scratch and must
   report a difference below 1 %.
5. Grid samples with `kspace_grid` (exported k; `drop_off_grid=True` for oversampled lines), fit maps with
   `mri-reconstruction/scripts/qmri_fit.py`, check orientation on a simulated asymmetric object, and report values
   measured from the export and endpoint values from the delivered image, applying the task's region definition as
   written in every image dimension. If a region rule allows two readings (face or corner neighbours; reference
   region restricted too or not), compute both on the delivered image, report the plainest and note the other.
   One script per stage, in the workspace root; keep printed output short.

## Rules the checker enforces

| Topic | Rule | Flags |
|---|---|---|
| Timing | TE = excitation centre -> k = 0 sample; TR = excitation-centre spacing; meet each within the task tolerance. The 10 us block raster can leave 5 us: put the remainder in the RF delay (`split_interval` + `center_shift`) or in a single readout's ADC (`adc_shift`); never report a raster-rounded value as meeting a tighter tolerance. RF and ADC keep their dead and ringdown times inside each block | `--te --tr --ti --time-tol` (default 1 us), `--rf-dead-time --rf-ringdown-time --adc-dead-time` |
| Sampling, exact positions | each sample index has a required k position: n samples, `oversample=1` | `--matrix NX NY [NZ] --fov F` |
| Sampling, coverage | an interval of k must be covered with a bounded sample spacing: `oversample=2, extra>=1`, so samples pass both ends and the step stays below the bound. Exactly n samples sit ON the ends with the step AT the bound, and the 6-digit export rounding breaks that about half the time | `--kx-cover LO HI --max-gap G` |
| Acquired lines | an ADC in a dummy or preparation repetition counts as an extra acquisition, so leave it out; every line is acquired the stated number of times; 3D: each cycle encodes its own partition | `--line-repeats R --n-adc N` |
| Gradients | Pulseq amplitudes are Hz/m (mT/m x 42.576e3), areas 1/m (cycles/m); arbitrary gradients (spirals) start and end at 0 with explicit `first=0, last=0` (or the neighbouring block's value), otherwise the extrapolated end values jump | continuity always checked; `--max-grad --max-slew` |
| Slice selection | sinc/SLR pulse WITH its slice-select gradient, then the rephaser; hard pulses are non-selective | `--slice-thickness` |
| Spoiled GRE | quadratic RF spoiling; each ADC takes its excitation's phase; spoiler after the last ADC; multi-echo monopolar needs flyback | `--rf-spoil 117 --min-spoil-cycles 2 --monopolar` |
| Inversion recovery, MP-RAGE | TI = inversion centre -> excitation centre (MP-RAGE: the excitation of the central k-space line); the same timing in every cycle, dummies too; spoil after the inversion; simulate one column of spins through the slab to verify a tissue null and that the signal no longer changes from one acquired cycle to the next (point isochromats can keep coherent echoes under a constant spoiler: vary the spoiler moment or the RF increment if the null fails); fit a + b exp(-TI/T1) or a dictionary of the exact timing | `--ti ... --tr TRAIN_TR CYCLE_GAP --min-inversion-spoil-cycles 2` |
| Spin echo, TSE, CPMG | refocusing centre at TE/2 (ESP/2); CPMG phase = excitation +/- 90 deg; rewind each phase encode before the next refocusing pulse; crusher moments equal on both sides and inside the range with margin; reach steady state before acquiring (dummy shots without ADC; confirm by simulating one column of spins) | `--te --cpmg --crusher-range LOW HIGH` |
| UTE half-pulse | two half-pulse acquisitions per spoke with opposite slice-gradient polarity, added as complex signals. Play each half pulse on the gradient plateau with `center=` at its end (the excitation k-space centre), so the slice gradient is on at the RF centre (not on the ramp-down, where it reaches 0); one lobe then ramps down and rewinds kz from the RF centre to 0 before the first ADC sample. The ADC delay respects the ADC dead time and the readout starts at k = 0 with its first sample; simulate single spins along z through both acquisitions to measure the summed slice response | `--n-adc`; gradient at each RF centre always checked |
| Diffusion (SE-EPI) | b-matrix from the exported waveforms using the effective gradient (sign inverted after each refocusing pulse); the same crushers around the refocusing pulse in every volume (b = 0 too) and a refocusing slab wider than the excited slice when spins extend beyond it; dummy repetitions before the first acquired volume unless TR >> T1. Point isochromats do not diffuse: a simulation without diffusion weighting must give the same signal in every volume (check it; differences bias the fit) | `--te --crusher-range` |
| Balanced SSFP | zero net area per TR; TE = TR/2; 0/180 phase cycling with matching ADC phase; catalyze or use dummies | `--balanced --rf-phase-cycle 180 --te-half-tr` |
| EPI | TE to the kx = ky = 0 sample of the train; constant line period; odd lines traverse the same grid backwards; no ramp sampling unless allowed; with ramp sampling the first and last samples must still pass the coverage ends | `--epi --echo-spacing ES` |

**Margins.** Design 2-5 % inside every limit and range (raster rounding moves areas, timing and slew; the checker
WARNs within 2 %). Report safety and timing values measured from the export: `--safety` with `--b1rms-max
--b1peak-max --grms-max --pns-rheobase --pns-chronaxie --pns-max` and `--json`.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder>

Every listed output, build and simulation scripts and their imported helpers included, goes directly in the folder
the task names (workspace root if none), never in `scripts/`; name the actual script files in `--require`. If the simulation could not run, say so plainly; never fabricate simulated or reconstructed outputs.

## More (open only when needed)

- Trajectories, EPI/diffusion/DENSE preparation, RF pulse design (SigPy.RF), SMS/CAIPI, time-optimal gradients,
  PNS, GIRF, other simulators, vendor SDKs: [tools and families](references/tools-and-families.md).
- Physics and citations: [reading list](references/reading-list.md),
  [sequences and trajectories](../mri-research/references/sequences-and-trajectories.md).
- Setup problems: [tool setup guide](../mri-research/references/tool-setup.md). Project notes (only with
  `.mrfoundry/INDEX.md`): [project memory](../mri-research/references/project-memory.md).
- Reconstruction: `mri-reconstruction`. Hardware limits and safety: `mri-hardware`.
