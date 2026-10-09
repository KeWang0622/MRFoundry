# Reconstruction software: which toolbox, and how to use it

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this to pick a toolbox for a task and give the user real, runnable starting
points. These are pointers + usage patterns, not full docs — link the official
docs and let the user go deep there.

## Decision guide

| Situation | Reach for |
|---|---|
| Battle-tested, publication-grade recon; non-Cartesian, calibration (ESPIRiT), PICS (PI+CS), CLI + scripting | **BART** |
| Pythonic prototyping, GPU (CuPy), clean iterative-methods API, MRI app layer | **SigPy** |
| Julia; fast, composable, research recon incl. non-Cartesian | **MRIReco.jl** |
| Julia; classic image-reconstruction algorithms (also CT/PET), NUFFT | **MIRT.jl** (and Python **MIRTorch**) |
| Just need a fast, differentiable NUFFT inside a PyTorch model | **torchkbnufft** (or **gpuNUFFT** for CUDA/MATLAB) |
| Deep-learning recon framework with datasets/baselines wired up | **DIRECT** or the **fastMRI** repo |
| Streaming/online recon on the scanner or a server, vendor-agnostic pipeline | **Gadgetron** |

## BART — Berkeley Advanced Reconstruction Toolbox

The de-facto standard for reproducible computational MRI. C core with CLI tools
and MATLAB/Python wrappers. From Lustig's and Uecker's groups.

- **Repo (active):** https://codeberg.org/mrirecon/bart · **Docs:**
  https://mrirecon.codeberg.page/ — BART moved to Codeberg; the
  `github.com/mrirecon/bart` repository was **archived in 2026** and no longer
  receives updates. Update bookmarks, CI checkouts, and submodules accordingly.
- Tutorials: https://github.com/mikgroup/espirit-matlab-examples and the
  webinar materials linked from the docs.
- Canonical mini-pipeline (ESPIRiT maps → L1-regularized PI+CS recon):
  ```
  bart ecalib -m1 -r 24 kspace sens      # estimate ESPIRiT coil maps
  bart pics -l1 -r 0.01 kspace sens img  # parallel-imaging + compressed sensing
  ```
  `-m1` is not cosmetic: `ecalib` returns **two** ESPIRiT map sets by default
  (soft-SENSE), so `pics` emits an image with a size-2 MAPS dimension — silently
  breaking anything downstream that expects a single image. `-r 24` merely caps
  the calibration region and is already BART's default.
- Also provides `nufft`/`nufftbase` (non-Cartesian), `traj` (trajectory
  generation: radial, spiral, etc.), `pocsense`, `nlinv`, `rss`, phantom
  simulation, and file I/O in its `.cfl/.hdr` format. Great for scripting whole
  experiments deterministically.

## SigPy (+ sigpy.mri)

Pythonic signal-processing package with an MRI submodule. GPU via CuPy, a clean
`App`/`Alg`/`Linop` abstraction, and NUFFT. From the Lustig group.

- Repo: https://github.com/mikgroup/sigpy  ·  Docs: https://sigpy.readthedocs.io/
- Tutorial notebooks: https://github.com/mikgroup/sigpy-mri-tutorial
- Typical usage:
  ```python
  import sigpy as sp, sigpy.mri as mr
  maps = mr.app.EspiritCalib(ksp).run()           # ESPIRiT sensitivity maps
  img  = mr.app.L1WaveletRecon(ksp, maps, lamda=0.01).run()   # PI + CS
  # non-Cartesian: mr.app.SenseRecon with a NUFFT linop built from a trajectory
  ```
- Related from the same group: k-space preconditioning
  (https://github.com/mikgroup/kspace_precond), extreme_mri, MEL_MRI.

## Julia toolboxes

- **MRIReco.jl** — https://github.com/MagneticResonanceImaging/MRIReco.jl —
  full recon (Cartesian & non-Cartesian, CS, PI), reads ISMRMRD; fast and
  composable.
- **MIRT.jl** — https://github.com/JeffFessler/MIRT.jl — Fessler group's
  Michigan Image Reconstruction Toolbox (Julia); classic regularized recon,
  NUFFT, also applies to CT/PET. Python port: **MIRTorch**.

## NUFFT / non-Cartesian building blocks

- **torchkbnufft** — https://github.com/mmuckley/torchkbnufft — differentiable
  Kaiser–Bessel gridding NUFFT in pure PyTorch; drop into a learned recon.
- **gpuNUFFT** — https://github.com/andyschwarzl/gpuNUFFT — CUDA gridding with
  MATLAB/Python interfaces; fast 3D.
- **mri-nufft** — https://github.com/mind-inria/mri-nufft — a unified Python
  interface that wraps many NUFFT backends (FINUFFT, cuFINUFFT, gpuNUFFT,
  torchkbnufft, …) behind one API, with MRI-oriented trajectory helpers. Use it
  when you want to swap NUFFT backends without rewriting your recon.
- BART `nufft` and SigPy's NUFFT are also solid, and integrate with their
  respective recon stacks.

## Deep-learning recon frameworks

- **DIRECT** — https://github.com/NKI-AI/direct — PyTorch framework with many
  baselines (VarNet, RIM, etc.), dataset loaders, training loops. Good when you
  want to train/compare methods rather than write one from scratch.
- **fastMRI** — https://github.com/facebookresearch/fastMRI — reference models
  (U-Net, VarNet, End-to-End VarNet), data transforms, and evaluation code that
  matches the challenge metrics.
- **ATOMMIC** — https://github.com/wdika/atommic — "Advanced Toolbox for
  Multitask Medical Imaging Consistency": data-consistency-focused DL recon plus
  segmentation/quantitative tasks. **Supersedes `mridc`**, which its author
  archived (read-only since Apr 2024) and explicitly redirects here.
- **DeepInPy** — https://github.com/utcsilab/deepinpy — "deep inverse problems
  in Python"; a lightweight framework for prototyping unrolled/model-based recon
  (from Tamir's group). Good when you want to iterate on a new unrolled method
  quickly rather than adopt a large framework.
- **TensorFlow MRI** — https://github.com/mrphys/tensorflow-mri — a library of
  computational-MRI operators (NUFFT, coil ops, losses) for TensorFlow/Keras
  users.
- **pygrappa** — https://github.com/mckib2/pygrappa — Python implementations of
  GRAPPA and many GRAPPA-like variants; handy for classical k-space parallel
  imaging without leaving Python.

## Scanner / streaming recon

- **Gadgetron** — https://github.com/gadgetron/gadgetron — vendor-agnostic
  streaming reconstruction framework; connects to scanners via ISMRMRD, chains
  "gadgets," and can call into BART/Python. Use for online/inline recon or
  productionizing a pipeline.

## Coil-map / ESPIRiT standalone implementations

- Python: https://github.com/mikgroup/espirit-python
- MATLAB examples (with BART): https://github.com/mikgroup/espirit-matlab-examples
- Auto-tuned ESPIRiT: https://github.com/mikgroup/auto-espirit

## Practical notes when helping with these

- Version/skew: APIs move (esp. SigPy and DL frameworks). If you're writing
  code for the user, prefer checking the installed version or the current docs
  over relying on a remembered signature.
- Reproducibility: BART's CLI + fixed seeds makes experiments scriptable and
  citable; recommend it when the user cares about reproducibility.
- GPU: SigPy (CuPy), torchkbnufft/DIRECT/fastMRI (PyTorch), gpuNUFFT (CUDA).
  Match the toolbox to the user's existing stack.
