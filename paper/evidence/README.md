# Recorded evidence for the MRFoundry paper

This folder preserves **historical demonstration evidence for inspection**, rather than claiming a newly tested, portable scientific reproduction. Original scripts, reports, the exported sequence and waveform/trajectory arrays retain their exact bytes. `demo-manifest.json` maps each to its historical workspace-relative source and SHA-256. The separate `evaluation/` directory documents evaluation provenance under its own scope.

No sequence simulation, reconstruction, diffusion fitting, benchmark trial, regrading or statistical recalculation was performed when assembling this archive. The paper's existing figure sources remain the source of its reviewed artwork.

Verify the copied bytes without importing scientific software or running a demonstration:

```sh
python3 verify-demo-archive.py
```

## What is included

| Folder | Evidence | Scope |
| --- | --- | --- |
| `demonstrations/sequence/original/` | Original design script, exported `.seq`, coarse KomaMRI simulator, reports, Python/Julia environment records, trajectory | Recorded September 2026 simulation-only prototype |
| `demonstrations/sequence/later-audit/` | Original extraction/compilation scripts, readback report and waveform arrays | October 2026 audit of the unchanged sequence; source text retains historical figure/table labels |
| `demonstrations/acquired/code/` | `run_m4raw.py`, `finalize_evidence.py`, `run_dwi.py`, direct dependencies and full environment snapshot | Original October 2026 acquired-data demonstration scripts |
| `demonstrations/acquired/m4raw/` | Initial SENSE report, final fixed-L1 report, diagnostic ROI definition | One public M4Raw acquisition, fixed native slice 8 |
| `demonstrations/acquired/source/` | Two calibration diagnostic records, L1 diagnostic, selected acquisition and selected manifest row | Recorded checks and public input identity |
| `demonstrations/acquired/diffusion/` | Tensor-fit report and definitions | Supplemental Stanford HARDI example, fixed slices 30, 38 and 46 |

Full raw M4Raw/Stanford data, full logs, conversations, internal run notes and private benchmark material are excluded. Exact public download URLs, licenses and expected hashes are in [input-identities.json](demonstrations/input-identities.json) and [INPUTS-AND-LICENSES.md](INPUTS-AND-LICENSES.md). Large derived image arrays are identified by original hash rather than duplicated. The saved coarse Koma signal array is also identified by hash; the archive does not claim independent re-verification of that scalar from the omitted array.

## Original workspace mapping and execution order

The following mapping explains how the retained code found its inputs. **It is not an executed installation recipe.** Use a disposable workspace for any future reproduction; never execute these scripts inside this evidence archive, because they create/overwrite outputs.

| Archived file(s) | Original location relative to a chosen workspace root |
| --- | --- |
| `sequence/original/*` | `outputs/golden-angle-gre/` |
| `sequence/later-audit/extract_sequence_evidence.py`, `compile_evidence.py` | `work/sequence-evidence-v22/` |
| `acquired/code/run_m4raw.py`, `run_dwi.py`, `finalize_evidence.py` | `work/mrfoundry-real-data-v19/` |
| Selected acquisition JSON and selected manifest TSV | `work/mrfoundry-real-data-v19/source/selected-acquisition.json` and `file_inventory.tsv` |
| Downloaded M4Raw H5 | `work/mrfoundry-real-data-v19/data/2022061203_T201.h5` |
| Stanford `dwi.nii.gz`, `dwi.bvals`, `dwi.bvecs`, public record XML | `work/figure-v4/data/` (XML filename `stanford-record.xml`) |

`design_sequence.py` writes the `.seq` and `trajectory.npz` beside itself; `simulate_koma.py` consumes them and runs the original **coarse** phantom through KomaMRI. Julia project/manifest filenames were retained exactly; Julia environment activation/bootstrap must be configured explicitly for a future run. The recorded Python requirements and Julia versions have not been reinstalled or tested for this archive. The Julia project includes packages beyond the CPU example; it is not a minimal dependency claim.

For acquired data, the recorded order is `run_m4raw.py` → `run_dwi.py` → `finalize_evidence.py`. The first creates `m4raw/arrays.npz` and an initial report; the finalizer retains that report and produces fixed-L1 outputs. `run_dwi.py` also reads the public Stanford XML. Direct dependencies are listed in `requirements-scientific.txt`; platform and Python versions are recorded in each report. Historical commands used `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2`.

Two explicit portability limits remain. The finalizer's scientific computation is followed by historical packaging that reads local skill files and downloaded source metadata. The sequence extractor also hashes a local skill, a private historical run note and a separate dense-extension report at its end. Those dependencies are **not distributed**, and unchanged scripts would require adaptation before complete execution elsewhere. These absolute paths are retained as original code/provenance, not installation requirements or evidence of access on another machine. Upstream README/data-card/format text is linked with hashes instead of copied. No separate executable script for the exploratory calibration sweep was retained in the selected source bundle; its saved diagnostic rows are provided without claiming a reproducible sweep recipe.

## Interpretation that must travel with the records

- **Sequence:** the 10-to-5 μs RF-step result concerns 13,497 spins on the same coarse phantom. It is not spatial convergence, scanner approval or reconstruction validation. Dense quadrature/reconstruction extensions are excluded and must not be substituted for this main example.
- **Reconstruction:** the source has 195 acquired PE lines in a 256-column grid. Both masks keep the same 24 central lines, retaining 110 and 67 source lines. The all-source RSS image is noisy and supplies the shared normalization scalar; it is not complete-PE, noise-free anatomical truth.
- **Calibration:** the original width 24 / threshold 0.02 / crop 0.95 maps were retained. One exploratory candidate lowered the recorded diagnostic errors, so “every alternative was worse” is unsupported. The recorded decision was that the bounded exploration did not justify a parameter change; it did not validate the map model or isolate the cause of error. The final report retains full-FOV and post-hoc ROI projection residuals.
- **Solver revision:** fixed L1-wavelet reconstructions reduced discrepancy relative to the initial SENSE outputs, while zero-filled RSS remained closer to the noisy reference. Small 200-to-400-iteration changes establish only iteration stability; substantial source-data and held-out residuals remain. No superiority or isolated causal explanation is claimed.
- **Diffusion:** WLS tensor residual measures model agreement on provider-preprocessed acquired HARDI. It is not a clinical pass threshold, gradient-frame validation or biological conclusion.

These are researcher-supervised worked examples, not controlled comparisons of agent guidance, autonomous planning, skill retrieval efficacy or later memory benefit. Short task wording in reports is an editorial summary, not a verbatim conversation.
