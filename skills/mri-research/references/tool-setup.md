# Set up the tool, then do the work

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this workflow whenever a task needs an MRI application, library, simulator,
reconstruction framework, analysis pipeline, or research utility. Install only
the dependencies needed for the user's task, not this entire catalog.

## Agent-owned setup

1. **Discover.** Identify the needed operation and the established tool that
   implements it. Find its official repository and installation documentation;
   verify the package name, supported OS/architecture, Python/Julia version,
   CPU/GPU requirements, and whether the upstream is maintained. A paper title
   or similarly named package is not sufficient provenance.
2. **Inspect.** Check the active environment, existing executable/import,
   version, available accelerator, disk needs, and required data/license. Reuse
   compatible installations. Do not silently replace a working environment.
3. **Install and execute.** When ordinary dependency installation is within the
   user's authorized task, perform it rather than giving the user commands to
   run. Prefer a project-local virtual environment, the upstream's environment
   file, or an official container. Use that environment's explicit executable
   for subsequent commands. Explain first-run downloads or long compilation.
   Respect actual execution permissions and license requirements; request only
   the specific unavailable credential, acceptance, or privilege when needed.
4. **Verify readiness.** Check the version/import/CLI and run a small official
   example or upstream test that exercises the needed operation on CPU first
   when practical. An import alone does not verify a solver, simulator, GPU
   kernel, or file-format reader. Then run the requested workflow and inspect
   its outputs, units, shapes, and diagnostics.
5. **Record.** Save the tool version or commit, environment/lockfile, commands,
   parameters, input provenance and actual results. Distinguish installation
   success, example success, and scientific validation of the user's task.

## Reuse established implementations

Write configuration, sequence definitions, orchestration and necessary format
adapters around existing tools. Do not respond to a missing dependency by
writing a replacement Bloch/EPG simulator, NUFFT, reconstruction solver,
segmentation pipeline, or metric implementation. Scientific-looking output
does not establish correctness. Small analytic checks may complement the
established implementation; they do not replace it.

If setup fails, inspect the actual error and follow the upstream's supported
repair path. If the requested tool remains unavailable, explain the blocker
and propose an established alternative with its limitations. Do not silently
change the requested method or call a toy demonstration a validated result.
Only implement a new numerical method when the user explicitly requests that
research/development work; compare it against an established reference.

## Python applications

Start from the selected upstream's supported Python version. For a simple
PyPI-supported application, use an isolated environment (on Windows the
executable is `.venv/Scripts/python.exe`):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pypulseq
.venv/bin/python -c "import pypulseq; print(pypulseq.__version__)"
```

This is a PyPulseq example, not an instruction to install PyPulseq for unrelated
tasks. Follow the selected project's requirements or lockfile when supplied.
Save resolved versions after a successful run; do not guess old pins or install
CUDA wheels on an incompatible machine.

## Pulseq design and established simulation

- **PyPulseq:** [official repository and examples](https://github.com/pulseq/pypulseq).
  Install `pypulseq` in the task environment, adapt an upstream sequence example,
  run `check_timing()`, inspect `calculate_kspace()`, then inspect the exported
  file with the target reader. Timing/trajectory checks are not Bloch simulation.
- **KomaMRI:** [official Julia project](https://github.com/JuliaHealth/KomaMRI.jl).
  Use its documented Julia environment and example, or the official
  [komamripy Python interface](https://github.com/JuliaHealth/komamripy):

  ```bash
  .venv/bin/python -m pip install komamripy
  .venv/bin/python -c "import komamripy as km; print(km.Scanner())"
  ```

  First use provisions Julia and KomaMRI and can take several minutes. Creating
  `Scanner()` initializes the backend; a bare import may be lazy. Complete the
  upstream small CPU simulation next, then import and simulate the user's
  exported `.seq`. Check supported Pulseq format/version and ADC counts. GPU
  backend setup is optional, not a prerequisite for a small correctness check.
  Record phantom, relaxation, off-resonance, discretization and spoiling model.
  The Python interface is evolving: use its installed-version documentation.
- **MRzero-Core / JEMRIS:** use their official installations and examples if
  chosen for the task; do not replace them with a new simulator when dependency
  setup takes longer than expected.

## Application entry points

These links identify the upstream to consult for current installation steps;
they do not claim that every application has been installed or tested locally.

| Task / application | Official installation entry point | Readiness check |
|---|---|---|
| Classical reconstruction: BART | [BART](https://mrirecon.codeberg.page/) and [source](https://codeberg.org/mrirecon/bart) | Confirm executable, then run an upstream phantom/calibration/reconstruction example. Check optional ISMRMRD support separately. |
| Python reconstruction / RF: SigPy | [SigPy](https://github.com/mikgroup/sigpy) | Import in the selected environment; run a small CPU reconstruction/RF example before configuring GPU support. |
| DL reconstruction: DIRECT / ATOMMIC | [DIRECT](https://github.com/NKI-AI/direct), [ATOMMIC](https://github.com/wdika/atommic) | Use upstream environment and a small forward/inference example; confirm Torch/device compatibility and checkpoint provenance. |
| NUFFT for Torch | [torchkbnufft](https://github.com/mmuckley/torchkbnufft) | Run upstream forward/adjoint example on the intended device; verify trajectory units. |
| Frozen fastMRI baselines | [fastMRI](https://github.com/facebookresearch/fastMRI) | Preserve compatible upstream dependencies; test transforms/model input. Dataset access is separate from package installation. |
| Diffusion: MRtrix3 / DIPY | [MRtrix3](https://www.mrtrix.org/), [DIPY](https://dipy.org/) | Verify CLI/import and a small official example. Check gradient conventions before user data. |
| FSL / FreeSurfer | [FSL documentation](https://fsl.fmrib.ox.ac.uk/fsl/docs/), [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/) | Follow supported platform/environment or container setup; check required licenses and a real executable. |
| QSIPrep / fMRIPrep | [QSIPrep](https://qsiprep.readthedocs.io/), [fMRIPrep](https://fmriprep.org/) | Prefer documented containers; check runtime, BIDS input, license mounts and a small documented run. |
| NODDI / bundles: AMICO / TractSeg | [AMICO](https://github.com/daducci/AMICO), [TractSeg](https://github.com/MIC-DKFZ/TractSeg) | Use upstream installation and model/kernel setup; test an official example. |
| RF and gradient design | [pulpy](https://github.com/jonbmartin/pulpy), [GrOpt](https://github.com/mloecher/grOpt) | Follow upstream build/runtime requirements and compare an official design example with requested limits. |
| Coil design / EM | [pyCoilGen](https://github.com/kev-m/pyCoilGen), [openEMS](https://github.com/thliebig/openEMS), [CoSimPy](https://github.com/umbertozanovello/CoSimPy) | Install required native solver as well as language bindings; run an upstream mesh/solver example. |
| Shimming | [Shimming Toolbox](https://github.com/shimming-toolbox/shimming-toolbox) | Follow environment instructions; validate a small shim example and coordinate/field units. |
| Console software: MaRCoS / OCRA | [MaRCoS client](https://github.com/vnegnev/marcos_client), [OCRA Pulseq](https://github.com/LincolnCB/ocra-pulseq) | Use offline examples first. Software setup does not authorize connecting to, flashing, or operating scanner hardware. |
| Manuscript / figures / literature | Selected venue's official template; established plotting/statistics tools; provider's official API docs | Compile the template or run a small analysis/query. Request an API key only when that provider requires one; never invent results. |

Commercial tools and vendor SDKs (IDEA, EPIC, HFSS, CST, etc.) require the
appropriate licensed environment. Do not bypass this with an imitation tool.
