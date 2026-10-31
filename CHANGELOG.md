# MRFoundry changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased — lean retrieval, finish check and tested helpers (0.11.0, B5)

- All skills 0.11.0: SKILL.md files rewritten as short route tables (task -> one helper or reference),
  silent-error checks and a single "before you finish" command; detail moved to on-demand references
  (mri-reconstruction `raw-data.md`, `bart-sigpy.md`, `quantitative-maps.md`; pulse-sequence-design
  `tools-and-families.md`; mri-hardware `landscape.md`; diffusion-mri `preprocessing-and-models.md`). Shared
  boilerplate removed; tool setup is read only when an install fails. SKILL.md total 101 KB -> 36 KB.
- mri-research-workflow: `finish_check.py` (+ test): required deliverables in one folder, environment
  record, clean-folder rerun of the entrypoint, JSON keys, map-median unit ranges.
- mri-reconstruction: `qmri_fit.py` adds exact piecewise-linear Tofts convolution and grid fit
  (`conv_exp_pwlinear`, `fit_tofts`), SPGR signal-to-concentration, ASL general kinetic model with explicit
  time origin and multi-delay fit, M0 finite-TR correction, order-independent ASL pairing, Rician-aware
  dictionary matching; `mrfoundry_rawrecon.py` adds SNR units, dwell-time noise scaling, coil maps from ACS,
  reconstruction ranking by simulated error, orientation check; new `qsm_lib.py` (+ test): Laplacian/temporal
  field estimation, PDF and V-SHARP, CG and TKD dipole inversion, synthetic head, analytic-sphere kernel test.
- mri-hardware: absolute shim currents with acquisition currents, `bounded_lsq_kkt` optimality check,
  `voxel_world_coords`, `fieldmap_multiecho`.
- pulse-sequence-design: `add_epi_readout`; checker `--epi` (TE to the train's k = 0 sample, echo spacing,
  kx error by line parity); simulator fallback to MRzeroCore when KomaMRI warm-up stalls.
- mri-research: `mrs_lib.py` (+ test): spectral registration, linear-combination fit, water referencing.

Motivated by A/B development trials (skill-hurt and both-fail cases); no task instance values.

## Unreleased — detail checks, tested pipelines and study statistics (0.10.0)

- pulse-sequence-design 0.10.0: `check_exported_seq.py` classifies excitation/inversion/refocusing pulses and checks
  TE, TR, TI, spin-echo refocusing timing and CPMG phase, quadratic RF spoiling or 0/180 phase cycling with receive
  phase, balanced moments per TR, inversion and post-readout spoilers, slice selection, Cartesian sampling and
  hardware limits (compact PASS/FAIL output; tests cover spoiled GRE, inversion-recovery GRE, bSSFP and spin echo,
  each with failing variants). New tested `example_pipeline.py` (build, check, waveforms, KomaMRI simulation of the
  export, archive, standalone reconstruction, orientation check, report); `kspace_grid` and `plot_waveforms`
  helpers; fast-path and per-family checklists; description covers simulation and relaxometry studies.
- mri-reconstruction 0.10.0: `qmri_fit.py` (+ test): mono-exponential, 3-parameter inversion recovery with
  polarity restoration, VFA, dictionary fits; Ernst, inversion-recovery and bSSFP (Bloch fixed point) signals.
- diffusion-mri 0.10.0: `adc_fit` with an explicit b-range (conventional b <= 1000) and `fixed_compartment_fraction`;
  biomarker-study checklist.
- mri-research-workflow 0.10.0: `study_stats.py` (+ test): subject-level AUC, subject bootstrap CIs, ICC(3,1),
  wCV/repeatability coefficient, development-only thresholds.
- All skills 0.10.0.

Motivated by development failure modes and token sinks (turn count) in A/B evaluations; no held-out task content.


## Unreleased — evaluation-driven detail guidance

- pulse-sequence-design 0.9.0: verify the exported sequence (realized TE/TR, slice-selective
  excitation and width, wrapped quadratic RF spoiling with matching ADC phase, sampling) and
  `scripts/check_exported_seq.py`.
- diffusion-mri 0.9.0: signal-fraction and diffusivity-spectrum models (well-posed models,
  recovery tests, noise floor); description now covers ADC and RSI-type studies.
- mri-research-workflow 0.9.0: check deliverables against the requested interface.

- Tested helper libraries: pulse-sequence-design `scripts/mrfoundry_seqlib.py` (+ `test_seqlib.py`),
  mri-reconstruction `scripts/mrfoundry_reconlib.py` (+ test), diffusion-mri `scripts/spectrum_fit.py`
  (+ test), mri-research-workflow `scripts/check_deliverables.py`.
- All skills 0.9.0: run the skill's tests or a small upstream example, start slow installs in the
  background, work from local skill content first, write each stage as one checked script;
  project memory only for ongoing projects.

Motivated by detail-level failures and token/time sinks in development A/B evaluations; no task content.

## Unreleased

### Changed
- Rebrand the collection as **MRFoundry**, with a two-tone vector logo, updated repository/install/citation links, and the renamed interactive tutorial. Existing skill identifiers stay compatible.
- Rename the canonical project notebook to `.mrfoundry/`; migrate legacy `.mri-research/` notebooks without overwriting notes, and update managed agent entrypoints in place. Conflicting dual notebooks stop migration for reconciliation.

- Replace the unavailable Berkeley time-optimal gradient software page with the official SigPy implementation reference, retaining original-method credit.

## [0.8.0] — 2026-10-07

- Replace failing software-index and COBIDAS site links with the upstream gradient archive and committee/report sources.

- Add evidence-first paper-writing guides for MICCAI, MRM, JMRI and IEEE TMI, with official policy sources, a paper-plan template, reviewer-response template and a clearly labeled illustrative diffusion study.
- Make cross-skill and repository-index links usable from standalone skill installations by linking to canonical repository paths.

- Use the open-access manuscript and canonical DOI routes for MoDL and diffusion tensor references after PubMed and publisher responses failed CI link validation.

- Replace metric-first reconstruction evaluation with task-specific evidence planning; clarify data-consistency limits, independent validation and original-source attribution, with a guide informed by Haldar’s 2026 editorial.

- Add a central paper/textbook index and annotated, skill-local reading lists for all seven skills.

- Expand DWI/DTI guidance, EPI and DENSE sequence references, and journal/conference selection and literature summaries (MRM, MICCAI, ISMRM, CVPR and related venues).

- Add project-local `.mri-research/` memory: scoped preferences, environments, evidence-linked lessons and experiment logs, with a non-overwriting initializer and optional CLAUDE.md/AGENTS.md entrypoints.

- All seven skills now own official tool discovery, dependency installation and smoke testing; add a shared setup guide and require established scientific implementations instead of homemade substitutes.

- Link to the hosted interactive MRI research presentation; generated deck HTML is kept outside this skills repository.

### Changed
- Compact README header with a transparent mascot beside the wordmark, replacing the large black-background image.

### Added
- A 3D-style MRI mascot illustration, displayed in the README, with its generation prompt and provenance in `assets/`.

## [0.7.0] — 2026-09-22

A second adversarial multi-agent review round, this time with every consequential
claim checked against a primary source (Crossref, PyPI, the GitHub/Codeberg APIs)
rather than taken from a reviewer's word. The headline finding: **BART moved to
Codeberg** and the GitHub repository is archived, so the repo's central execution
dependency was pointing at a frozen tree.

### Fixed — correctness (found by verification, not opinion)
- **BART now points at its active home**, https://codeberg.org/mrirecon/bart
  (docs https://mrirecon.codeberg.page/), everywhere it appears; the archived
  `github.com/mrirecon/bart` mirror is labelled as such.
- **`ecalib` two-map bug.** `bart ecalib` returns **two** ESPIRiT map sets by
  default, so `pics` emitted a soft-SENSE image with a size-2 MAPS dimension — a
  silent wrong answer. `bart_recon.sh`, the hub, and `mri-reconstruction` now all
  pass `-m1` and explain why (and note that `-r 24` is already BART's default).
- **Non-Cartesian calibration used the wrong NUFFT.** Gridding for ESPIRiT now
  uses the **inverse** NUFFT (`nufft -i`); the adjoint (`-a`) leaves sampling
  density in the data and biases the coil maps.
- **EPI is Cartesian.** The docs no longer imply EPI needs a trajectory/NUFFT; it
  needs ramp-sampling regridding plus Nyquist-ghost/phase correction upstream.
- **`bart_recon.sh` hygiene:** refuses to overwrite an existing output, writes
  intermediates to `mktemp` scratch and cleans them up on exit, and prints the
  output dimensions so a stray MAPS dimension is visible.
- **Raw-data ingest was wrong in two places.** `bart twixread` needs `-A` (or
  explicit `-x/-y/-z/-c/-s/-n`); `cfl.py` ships in BART's `python/` directory and
  is **not** on PyPI (the `bartpy` package there is an unrelated decision-tree
  library); and `bart ismrmrd` only exists when BART is built with `ISMRMRD=1`
  (the Makefile defaults to `ISMRMRD=0`).
- **MaRCoS was miscredited.** The system paper is Negnevitsky V, et al.,
  *J Magn Reson* 2023;350:107424 (doi:10.1016/j.jmr.2023.107424); Guallart-Naval
  et al. is the multi-site benchmarking paper (*NMR Biomed* 2023;36(1):e4825).
- **SPIRiT was described as the SENSE/GRAPPA bridge** — that is ESPIRiT. SPIRiT is
  GRAPPA generalized to enforce calibration consistency everywhere, with no
  explicit sensitivity maps.
- **`mridc` is archived** (read-only since Apr 2024) and its author redirects to
  **ATOMMIC** (https://github.com/wdika/atommic); all three mentions updated.
- **Papers with Code has been retired** — paperswithcode.com now redirects to
  Hugging Face Papers; the workflow agent says so instead of linking a dead index.
- **SPM is no longer "SPM12"** — development moved to github.com/spm/spm with
  calendar versioning (25.01.02 stable, 26.01 in RC), which is not path- or
  script-compatible with SPM12.
- Removed a garbled GE parenthetical (the `GEHealthcare` org has no public repos)
  and a private note that had leaked into `foundations.md`.
- Dropped a stray trailing whitespace and pinned down Tarquin's status (source at
  `martin3141/tarquin`, no commits since 2021 — dormant, baseline only).

### Added
- **The SNR cost of acceleration**, which the repo previously never quoted: a
  g-factor section (`SNR_accel = SNR_full/(g·√R)`), noise prewhitening / optimal
  coil combination (Roemer 1990), and pseudo-replica SNR for GRAPPA/ESPIRiT/
  nonlinear recon where `g` has no analytic form (Robson 2008). The recon agent is
  now required to report it.
- **Structured low-rank split into its three distinct ideas** — SAKE
  (block-Hankel, inter-coil dependency), LORAKS (limited support + phase, plus
  P-LORAKS), ALOHA (annihilating filters) — each with its own citation.
- **SMASH** (the k-space ancestor GRAPPA generalizes) and a fuller
  **partial-Fourier** entry with the real-image/Hermitian caveat (Noll 1991).
- **Controlled aliasing, properly separated:** CAIPIRINHA (multi-slice and 2D),
  blipped-CAIPI for SMS-EPI, and Wave-CAIPI for 3D.
- **Dixon/IDEAL untangled:** IDEAL is the species decomposition, graph cuts solve
  the *field map* and its water/fat swap ambiguity, and quantitative PDFF needs a
  multi-peak fat model with simultaneous R2\*.
- **ASL needs a kinetic model:** the subtraction image is not CBF (Buxton 1998),
  plus PCASL/PASL/VSASL, the post-labeling delay, the consensus implementation
  (Alsop 2015), and ASLPrep.
- **QSM dipole inversion** is the ill-posed step (zero cone in k-space) — review
  and MEDI citations, with a note on why two pipelines disagree.
- **MRSHub** (https://mrshub.org) as the MRS community index, and a full citation
  for HFS-SDE diffusion recon.
- **Explicit, bidirectional hand-offs** in every expert skill, so trained recon,
  classical recon, acquisition design, hardware, and image analysis each have one
  unambiguous owner. The hub now states that **it** owns image-level analysis
  (fMRI/GLM, BIDS, DICOM/NIfTI, FreeSurfer, segmentation, registration) — no
  sibling skill covered it, and the hub's description didn't trigger on it.

### Changed
- The hub description now fits the **1024-character limit** skill validators
  enforce (it was over) and includes the analysis triggers it was missing.
- All seven skills are on version 0.7.0 (previously five were still on 0.1.0).

### CI
- `validate_repo.py` now enforces what this round had to catch by hand:
  description length ≤ 1024, one source of truth for the version across all seven
  skills + `CITATION.cff` + README, frontmatter `name` matching its directory, and
  routing-table rows that resolve to real files.
- New **freshness** job: flags linked upstreams that have been archived, renamed,
  or moved (this is what would have caught the BART migration), and checks that
  every PyPI package and DOI the repo names actually exists.
- Pinned the third-party ShellCheck action to a commit SHA.

## [0.6.0] — 2026-09-22

More tools across sequence design and hardware/RF, a multi-agent red-team
improvement pass, and stronger CI + branch protection.

### Added
- **Sequence design:** gradient/trajectory optimization (GrOpt, Lustig
  minTimeGradient, safe_pns_prediction), GIRF (MRI-gradient/GIRF, GIRFReco.jl),
  Pulseq ecosystem (TOPPE for GE, pulseq-CEST, MR-Physics-with-Pulseq), more
  simulators (JEMRIS, MRiLab, sycomore, EPG-X, MRzero-Core), and RF design
  (pulpy, Spectral-Spatial-RF-Pulse-Design, Multiband-RF, kpTx).
- **Hardware / RF:** coil design (CoilGen, pyCoilGen), EM/SAR (MARIE, mariepy,
  CoSimPy, scikit-rf), B0 shimming (Shimming Toolbox), the MaRCoS ecosystem
  (marcos_client/server, marga, ocra-pulseq), GPA-FHDO, MRI4ALL, and OSI² ONE
  (with the correction that OSI² code lives on GitLab).
- **Reconstruction:** CG-SENSE and partial-Fourier/homodyne. **Quantitative:**
  fat–water (Dixon / IDEAL / PDFF / R2*) and CEST.
- **CI:** a committed `validate_repo.py` (frontmatter + registry↔folder
  consistency) and a "skills CLI detects all skills" job.

### Changed / Fixed (multi-agent red-team pass)
- `mri-reconstruction`: `bart_recon.sh` now states its assumptions (Cartesian,
  coils on dim 3, ACS required), adds an explicit **trajectory path** for
  non-Cartesian data instead of silently FFT-ing it, and the docs no longer
  overclaim ("just works" → scoped to Cartesian; non-Cartesian needs a
  trajectory). Named the real `.cfl` conversion mechanisms.
- Rescoped the `mri-research` hub description to orientation/routing so it no
  longer over-triggers and collides with every expert.
- Foundations: disambiguated ISMRM "MR Academy" (dropped the unrelated
  "MRIcademy" brand). Bumped the hub and `skills.sh.json` to 0.6.0 — note this
  release claimed to have "aligned all version numbers", but the five expert
  skills were in fact left on 0.1.0; that was corrected in 0.7.0.

### Governance
- Branch protection on `main`: PRs must pass the CI status checks before merge.

## [0.5.1] — 2026-09-19

Industry-standard hardening (no skill-content changes).

### Added
- Community health: `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1),
  `SECURITY.md`, issue templates, and a pull-request template.
- CI (`.github/workflows/validate.yml`): validates `skills.sh.json` and every
  SKILL.md's frontmatter, runs ShellCheck on the helper script, and link-checks
  all Markdown (tolerant of publisher bot-blocks) on each change and weekly.
- `.editorconfig`.

### Fixed
- Repointed the README stars-badge link to the repo home (the `/stargazers` path
  returned 404 to link checkers).

### Verified
- Full link sweep across every file: 172 URLs return 200; the remainder are
  publisher pages that bot-block (403/429) but load in a browser.

## [0.5.0] — 2026-09-19

Added an end-to-end **research-workflow** agent that shepherds a project from
idea to a published paper.

### Added
- `skills/mri-research-workflow/` — orchestrator/assistant for the full research
  lifecycle (literature → hypothesis → experiment design → running experiments →
  analysis → figures/tables → manuscript → submission/rebuttal). Venue-aware for
  **CVPR / MICCAI / NeurIPS / MRM**, with template and reproducibility pointers
  (cvpr-org/author-kit, Springer LNCS, MRM LaTeX class, Papers with Code,
  CLAIM/COBIDAS). Hands off to the expert agents.

### Changed
- `skills.sh.json` adds a "Research workflow" group; README and the hub SKILL.md
  list the new agent. Version 0.5.0.

## [0.4.0] — 2026-09-19

Turned the repo into a multi-agent MRI **team**: five specialized, installable
expert skills alongside the generalist hub, with the reconstruction agent made
**actionable** (it runs BART/SigPy).

### Added
- `skills/mri-reconstruction/` — actionable reconstruction agent (ESPIRiT +
  PI/CS via BART/SigPy) including a runnable `scripts/bart_recon.sh`.
- `skills/diffusion-mri/` — diffusion MRI (DTI/DKI/NODDI, topup/eddy, CSD,
  tractography; MRtrix3, DIPY, FSL, AMICO, TractSeg, QSIPrep).
- `skills/pulse-sequence-design/` — Pulseq/PyPulseq, KomaMRI, RF/SMS design, and
  Siemens (IDEA/ICE) / GE (EPIC/Orchestra) / Philips (Paradise) sequence dev.
- `skills/deep-learning-recon/` — unrolled / self-supervised / diffusion recon,
  DIRECT/fastMRI/mridc, evaluation & hallucination caveats.
- `skills/mri-hardware/` — low-field, open-source consoles, coils, MR safety.
- `skills.sh.json` groups the hub and the expert team.

### Changed
- `mri-research` hub gains an "expert team" section pointing to the siblings
  (version 0.4.0). README documents the team and per-skill install
  (`--skill <name>` / `--all`).

## [0.3.0] — 2026-09-19

Deepened coverage (review-driven) and added a publishing reference.

### Added
- `references/publishing.md` — MR journals + author guidelines (MRM, JMRI, NMR in
  Biomedicine, MAGMA, IEEE TMI, Medical Image Analysis, NeuroImage, Imaging
  Neuroscience, Radiology), LaTeX templates/classes (MRM class, IEEEtran,
  elsarticle, Springer, Overleaf, arXiv), reporting/reproducibility standards
  (COBIDAS, CLAIM, TRIPOD+AI, ISMRM RRSG), and abstract submission.
- `sequences-and-trajectories.md` — acquisition-side acceleration & correction:
  SMS/multiband (Moeller 2010, Setsompop 2012, CMRR), B0 field mapping &
  distortion correction (FSL topup/FUGUE), B1 mapping, off-resonance correction,
  prospective motion.
- `recon-methods.md` — GRASP/XD-GRASP (motion-resolved), subspace/low-rank
  model-based qMRI, a denoising section (NORDIC, MP-PCA, Patch2Self), and an
  evaluation & image-quality-metrics section (SSIM/PSNR/…, DL-hallucination
  caveat, retired-leaderboard note).
- `analysis-processing.md` — quality control & motion (MRIQC, MCFLIRT), and a
  cardiac/body/MSK + radiomics section (pyradiomics; ACDC/M&Ms benchmarks).
- `data-and-formats.md` — ACDC and M&Ms cardiac datasets.
- `hardware.md` — a dedicated, non-clinical MRI safety section (ACR,
  MRIsafety.com, ISMRM).
- README Mermaid pipeline diagram.

### Changed
- `SKILL.md` routing and triggers extended (publishing, safety); version 0.3.0.

## [0.2.0] — 2026-09-19

Broadened from a reconstruction-focused reference into a **general MRI** research
hub, and switched distribution to the open `skills` CLI (`npx skills add`).

### Added
- `references/analysis-processing.md` — image analysis & processing: structural,
  functional, and diffusion MRI; segmentation and registration; DICOM/NIfTI/BIDS
  handling. Tools include FreeSurfer, FSL, SPM, AFNI, ANTs, fMRIPrep, nilearn,
  MRtrix3, DIPY, nnU-Net, TotalSegmentator, MONAI, Nipype, dcm2niix, nibabel.
- `references/quantitative-and-spectroscopy.md` — quantitative MRI (relaxometry,
  QSM, perfusion/ASL, MT) and MR spectroscopy (LCModel, Osprey, FSL-MRS, Gannet,
  qMRLab, SEPIA).
- `references/data-and-formats.md` — image-level formats (DICOM, NIfTI, BIDS) and
  image-level datasets (HCP, OpenNeuro, UK Biobank, ADNI, OASIS, IXI, BraTS) with
  access-term notes.
- `references/foundations.md` — canonical textbooks/handbooks (McRobbie,
  Westbrook, Bernstein *Handbook of MRI Pulse Sequences*, Haacke).
- `skills.sh.json` registry metadata for the `skills` ecosystem.

### Changed
- `SKILL.md` reframed around the full MRI pipeline (physics → acquisition →
  reconstruction → analysis → quantification) with an expanded routing table.
- Repository restructured to the `skills` layout (`skills/mri-research/`) so it
  installs with `npx skills add KeWang0622/MRFoundry`.
- README rewritten: MRI-first framing, `npx skills` install, working badges.

## [0.1.0] — 2026-09-19

Initial public release.

### Added
- `SKILL.md` navigator: core MR mental model, ground rules (link rot, dataset
  licenses, non-diagnostic scope, no copyrighted text), and a question →
  reference routing table.
- `references/foundations.md` — MR physics / k-space and where to learn
  (UC Berkeley EE225E, Stanford EE369B/C, Hornak, MRIquestions, ISMRM).
- `references/recon-methods.md` — landmark-paper reading list spanning parallel
  imaging (SENSE, GRAPPA, ESPIRiT, SPIRiT, NLINV), compressed sensing, low-rank
  and dynamic (L+S, k-t, structured low-rank), deep learning (VarNet, MoDL,
  E2E-VarNet, SSDU, AUTOMAP), diffusion / score-based recon, and MR
  fingerprinting; plus a "which method for which task" guide.
- `references/tools.md` — toolbox decision guide and usage patterns for BART,
  SigPy, MIRT.jl, MRIReco.jl, torchkbnufft, gpuNUFFT, mri-nufft, pygrappa,
  DIRECT, fastMRI, DeepInPy, TensorFlow MRI, and Gadgetron.
- `references/data-and-formats.md` — ISMRMRD and vendor raw formats (Siemens
  twix, GE P-file, Philips raw) with converters, plus open datasets (fastMRI,
  mridata.org, OCMR, SKM-TEA, Calgary-Campinas, CMRxRecon, M4Raw).
- `references/sequences-and-trajectories.md` — pulse-sequence programming
  (Pulseq/PyPulseq, vendor SDKs), trajectory design, and simulation (KomaMRI).
- `references/hardware.md` — MRI hardware and the open-hardware community
  (OSI², MaRCoS, OCRA, low-field, coils, gradients, safety).
- `references/literature-access.md` — literature/data APIs, API-key handling,
  and paper-search MCP servers.
- `references/radiology-primer.md` — MR image-contrast orientation (T1/T2/
  FLAIR/DWI), scoped strictly as non-diagnostic background.
- Project scaffolding: `README.md`, `LICENSE` (MIT), `CITATION.cff`,
  `CONTRIBUTING.md`, `.gitignore`.

[0.7.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.7.0
[0.6.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.6.0
[0.5.1]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.5.1
[0.5.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.5.0
[0.4.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.4.0
[0.3.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.3.0
[0.2.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.2.0
[0.1.0]: https://github.com/KeWang0622/MRFoundry/releases/tag/v0.1.0
