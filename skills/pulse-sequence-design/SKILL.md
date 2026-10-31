---
name: pulse-sequence-design
description: >-
  Read before designing, exporting or simulating an MRI acquisition: pulse
  sequences, RF and gradient waveforms, k-space trajectories (Cartesian,
  radial, spiral, EPI), Pulseq/PyPulseq files and Bloch simulation of the
  export. Prevents silent errors in realized TE/TR/TI and echo spacing,
  spoiling and receive phase, gradient balance, slice selection, steady state
  and sampling grids. Ships tested builders, an exported-sequence checker and
  an end-to-end example.
metadata:
  author: Ke Wang
  version: "0.12.0"
---

# MRFoundry: Pulse Sequence and Trajectory Design

Prototype vendor-neutrally with PyPulseq. Treat the build script as a claim and the exported `.seq` as the
evidence: measure the export, simulate the export, reconstruct from the simulation of the export.

## Fast path (sequence -> Bloch simulation -> reconstruction -> report)

1. Setup: `pip install pypulseq sigpy matplotlib` plus a Bloch simulator that reads Pulseq files. The tested
   route is KomaMRI through `komamripy` (`simulate_with_koma` in `scripts/mrfoundry_seqlib.py`): start
   `python .agents/skills/pulse-sequence-design/scripts/test_seqlib.py` in the background at once, because the first call installs and compiles
   Julia (about 3.5 min on a fresh depot). If that warm-up fails or has not finished within about 6 minutes,
   switch to MRzeroCore (`pip install MRzeroCore`, pure Python) rather than waiting; never replace the
   simulator with a homemade Bloch routine or an ideal-signal formula.
2. Copy `scripts/example_pipeline.py` (build, read back, waveform figure, simulation of the exported file,
   archive with hashes, standalone reconstruction, orientation check, report) and swap in a family builder:
   spoiled GRE in `scripts/test_seqlib.py`; inversion-recovery GRE, balanced SSFP, spin echo and single-shot
   EPI (`add_epi_readout`) in `scripts/test_check_exported_seq.py`. `python .agents/skills/pulse-sequence-design/scripts/mrfoundry_seqlib.py --api`
   lists signatures. Helpers: `make_system`,
   `slice_selective_excitation`, `centered_readout` (sample n//2 exactly at k = 0), `fill_delay` (exact
   intervals on the block raster), `RFSpoiler`, `spoiler_area`, `kspace_grid`, `plot_waveforms`.
3. Run the checker with EVERY requested parameter until all lines PASS and NOT CHECKED is empty; verify each
   VERIFY SEPARATELY item yourself or by simulating the exported file:
   `python .agents/skills/pulse-sequence-design/scripts/check_exported_seq.py sequence.seq --te ... --matrix NX NY --fov F ...`
4. Grid samples with `kspace_grid` (it uses the exported k, so line order and polarity cannot be mixed up),
   fit maps with `mri-reconstruction/scripts/qmri_fit.py`, check orientation on a simulated asymmetric
   object, and report values measured from the export.
5. One script per stage with built-in checks; keep printed output short (it is re-read every turn).

## Checker flags by family

| Family | Rule | Flags |
|---|---|---|
| All | TE = excitation RF centre -> ADC sample at k = 0; TR = excitation-centre spacing; delays on the block raster, never a collapsed minimum | `--te --tr --flip --max-grad --max-slew` |
| Slice selection | sinc/SLR pulse WITH its slice-select gradient, then the rephaser; hard pulses are non-selective | `--slice-thickness` |
| Spoiled GRE | quadratic RF spoiling `inc=(inc+117)%360; phase=(phase+inc)%360`; each ADC takes its excitation's phase; spoiler after the last ADC (cycles per slice); multi-echo monopolar needs flyback | `--rf-spoil 117 --min-spoil-cycles 2 --monopolar` |
| Inversion recovery | TI = inversion centre -> excitation centre; spoil after the inversion; state the inversion repetition period; fit a + b exp(-TI/T1) or a dictionary of the exact timing | `--ti ... --min-inversion-spoil-cycles 2` |
| Spin echo / TSE | refocusing centre at TE/2; CPMG phase = excitation ± 90°; equal crushers | `--te --cpmg` |
| Echo trains under safety limits | crusher moments equal on both sides of every refocusing pulse and inside the allowed range WITH margin; report the safety values measured from the file; fit with an EPG dictionary of the actual flip angles and each sample's T1 (`qmri_fit.epg_t2_dictionary`) | `--cpmg --crusher-range LOW HIGH --safety --b1rms-max --b1peak-max --grms-max --pns-rheobase --pns-chronaxie --pns-max` |
| Balanced SSFP | zero net area per TR on all axes; TE = TR/2; 0/180 phase cycling with matching ADC phase; steady state by catalyzation or dummies (simulate early vs late lines) | `--balanced --rf-phase-cycle 180 --te-half-tr` |
| EPI | TE to the kx = ky = 0 sample of the whole train; constant line period; no ramp sampling unless allowed; odd lines are the same kx grid traversed backwards (an odd-only kx error means the ADC is not centred on reversed flat tops) | `--epi --echo-spacing ES --matrix NX NY --fov F` |
| Sampling | k = 0 sample index, line set and order, polarity, 1/FOV spacing against any sampling contract | `--matrix NX NY --fov F` |

Report realized TE/TR/TI/echo spacing/flip/slice width/spoiling read back from the file; the block raster can
move realized timing by up to half a raster step from the request.

**Units and margins.** PyPulseq gradient amplitudes are Hz/m (mT/m x 42.576e3), areas and moments 1/m
(cycles/m), RF amplitudes Hz: passing T/m gives moments near 1e-5 cycles/m. Design 2-5 % inside every limit and
range (raster rounding moves areas, timing and slew); the checker prints WARN within 2 % of a limit. Report
safety and timing numbers measured from the exported file (`--safety --json`), never the build script's request.

## Before you finish

    python .agents/skills/mri-research-workflow/scripts/finish_check.py --require <every deliverable name> \
        --rerun "python <entrypoint> <documented arguments with {inputs} and {out}>" --inputs <input folder>

All deliverables in the folder the task names (workspace root if none). If the simulation could not run,
say so plainly; never fabricate simulated or reconstructed outputs.

## More (open only when needed)

- Trajectories, EPI/diffusion/DENSE preparation, RF pulse design (SigPy.RF), SMS/CAIPI, time-optimal gradients,
  PNS, GIRF, other simulators, vendor SDKs: [tools and families](references/tools-and-families.md).
- Physics and citations: [reading list](references/reading-list.md),
  [sequences and trajectories](../mri-research/references/sequences-and-trajectories.md).
- Setup problems: [tool setup guide](../mri-research/references/tool-setup.md). Project notes (only with
  `.mrfoundry/INDEX.md`): [project memory](../mri-research/references/project-memory.md).
- Reconstruction: `mri-reconstruction`. Hardware limits and safety: `mri-hardware`.
