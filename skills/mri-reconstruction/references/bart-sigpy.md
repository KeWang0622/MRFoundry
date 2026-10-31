# BART and SigPy pipelines

**Summary.** BART is the default CLI toolbox (ESPIRiT `ecalib -m1`, `pics`, `nufft`); SigPy is the Python
alternative. Identify the file format, convert to `.cfl` when using BART, estimate one set of coil maps, and
inspect dimensions, scaling and orientation. `scripts/bart_recon.sh` runs ESPIRiT + PI/CS on a Cartesian
`.cfl` (pass a trajectory for non-Cartesian data).

## File formats

- **BART `.cfl` + `.hdr`**: dims `[X Y Z COILS ...]` (coils on dim 3).
- **Siemens twix `.dat`**: `bart twixread -A meas.dat ksp` (`-A` guesses dimensions), then `bart show -m ksp`;
  or read with `twixtools`/`pymapVBVD` and write a `.cfl`.
- **NumPy**: BART's `python/cfl.py` (not on PyPI; the PyPI `bartpy` is unrelated): `cfl.writecfl(name, arr)`.
- **ISMRMRD `.h5`**: `bart ismrmrd` exists only in builds with `ISMRMRD=1`; otherwise read with the Python
  `ismrmrd` package or h5py (acquisition header fields: flags, idx.kspace_encode_step_1, idx.average,
  center_sample, sample_time_us; data stored [channels][samples]). Vendor raw to ISMRMRD with
  `siemens_to_ismrmrd`, `ge_to_ismrmrd`, `philips_to_ismrmrd`.

## BART workflow

    bart ecalib -m1 -r 24 kspace sens          # one map set; two sets give a soft-SENSE MAPS dimension
    bart fft -iu 7 kspace img_coils && bart rss 8 img_coils img        # fully sampled
    bart pics -l1 -r 0.01 kspace sens img                               # PI + CS
    bart pics -t traj kspace sens img                                   # non-Cartesian

For non-Cartesian calibration grid with the inverse NUFFT (`bart nufft -i`), not the adjoint. EPI is
Cartesian. Investigate aliasing or over-smoothing with calibration checks and a documented regularization
sweep. BART source: https://codeberg.org/mrirecon/bart (docs https://mrirecon.codeberg.page/; the GitHub
mirror is archived).

## SigPy

    import sigpy as sp, sigpy.mri as mr
    maps = mr.app.EspiritCalib(ksp).run()
    img = mr.app.L1WaveletRecon(ksp, maps, lamda=0.01).run()

Non-Cartesian: build a NUFFT from coordinates ordered like the image axes, in grid units, and use
`mr.app.SenseRecon`. Scaling is orthonormal.

## Guardrails

- Confirm acceleration and Cartesian versus non-Cartesian sampling before choosing a method.
- Report the SNR cost (g-factor or pseudo-replicas); acceleration R costs g·sqrt(R).
- Theory and citations: [recon methods](../../mri-research/references/recon-methods.md); tools:
  [tools](../../mri-research/references/tools.md).
