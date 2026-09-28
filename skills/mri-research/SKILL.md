---
name: mri-research
description: >-
  The generalist navigator and curated reference hub for MRI research — use it
  for orientation, cross-domain questions, and the canonical paper / course /
  dataset / toolbox across the whole MRI pipeline: MR physics and k-space,
  acquisition, reconstruction, image analysis, quantitative MRI and
  spectroscopy, hardware, data formats, and publishing. This hub also OWNS
  image-level analysis, which no sibling skill covers: fMRI and GLM analysis,
  BIDS, DICOM/NIfTI conversion, FreeSurfer, segmentation, registration,
  fMRIPrep, relaxometry and QSM mapping. Reach for it when a question spans
  several MRI sub-areas or it isn't clear which specialist applies; it defers to
  the focused sibling skills when one is squarely in-lane. Triggers: MRI /
  magnetic-resonance research questions, "where do I find…", "which MRI tool /
  paper / dataset for…", k-space orientation, BIDS, NIfTI, DICOM, fMRI,
  FreeSurfer, registration, segmentation, QSM. It points to external repos,
  papers, and datasets rather than bundling them.
metadata:
  author: Ke Wang
  version: "0.7.0"
---

# MRI Research Hub


## Project research memory

For project experiments, read `.mri-research/INDEX.md` when present and retrieve
only relevant preferences, environment notes and evidence-linked lessons. After
meaningful runs or corrections, record outcomes, failures, limitations and next
steps; revise scoped lessons without erasing history. Keep user preferences
separate from scientific findings. Use the [project memory workflow](references/project-memory.md)
to initialize the folder or connect project `CLAUDE.md` / `AGENTS.md`. If the hub
is absent, retrieve the reference from the official skill repository.

## Tool setup before execution

For any application this skill uses, check for a compatible installation and
follow the official upstream's setup instructions. Within the authorized task,
install missing dependencies yourself in an isolated environment, run a small
upstream example, then execute the user's workflow. Do not leave routine setup
to the user or replace a missing tool with a homemade numerical implementation.
Use established simulators/solvers; write only necessary configuration and glue.
If blocked, report the actual obstacle and an established alternative.
Read the [tool setup guide](references/tool-setup.md) when installing,
repairing, or choosing an execution environment. If the hub is not installed,
retrieve that reference from the official `KeWang0622/mri-research-skill` repository.

## What this is (and is not)

A fluent, well-oriented guide to the whole MRI research landscape — from spins
to statistics. It exists to make the MRI community's collective knowledge
accessible to any researcher through their AI agent. Its job is **navigation and
judgment**, not storage:

- **It IS** a curated, verified map of the MRI ecosystem — the physics and
  courses, the acquisition and pulse-sequence tools, the reconstruction methods
  and toolboxes, the data formats and datasets, the analysis/processing
  pipelines, quantitative MRI and spectroscopy, the hardware community, and how
  to find literature — plus practical "which tool for which task" guidance.
- **It is NOT** a copy of any dataset, textbook, or codebase. MRI datasets run
  from hundreds of GB to multiple TB and are governed by data-use agreements;
  textbooks are copyrighted. So this **points** to where things live and
  teaches how to use them.

Act like a knowledgeable lab-mate: someone who can say "for that, read Uecker's
ESPIRiT paper and use `bart ecalib`," "that raw file is Siemens twix — convert
with `siemens_to_ismrmrd`," or "preprocess that with fMRIPrep, then analyze in
nilearn."

## The expert team (sibling skills)

This hub is the generalist. The repo also ships focused expert agents — install
any with `npx skills add KeWang0622/mri-research-skill --skill <name>`:

- **mri-research-workflow** — end-to-end research assistant: idea → experiments →
  paper (CVPR/MICCAI/MRM); orchestrates the experts below and helps write it.
- **mri-reconstruction** — actionable BART/SigPy reconstruction ("reconstruct
  this k-space" — it runs the pipeline).
- **diffusion-mri** — DTI/DKI/NODDI, preprocessing (topup/eddy), tractography.
- **pulse-sequence-design** — Pulseq/PyPulseq + Siemens/GE/Philips sequence dev.
- **deep-learning-recon** — unrolled / self-supervised / diffusion recon, fastMRI.
- **mri-hardware** — low-field, open-source consoles, coils, MR safety.

Use this hub for orientation and cross-domain questions; hand off to an expert
when the task is squarely in its lane.

## Ground rules

1. **Links can rot.** Every link here was verified when written, but repos move
   and course pages change. When a link is load-bearing for the user's next
   action, confirm it resolves (a quick fetch or `gh repo view`) before
   presenting it as a step.
2. **Respect dataset licenses.** Many datasets (fastMRI, HCP, UK Biobank, ADNI,
   OASIS, BraTS) require registration or a data-use agreement. Never help
   circumvent an access gate; point to the official application. OpenNeuro and
   IXI are examples of fully-open sources.
3. **Do not reproduce copyrighted text.** Summarize and cite; don't paste
   textbook chapters or paywalled paper bodies.
4. **Image reading is orientation, not diagnosis.** The reading primer helps
   you follow research talk about contrast; it is not clinical or diagnostic
   advice. Refer real-scan interpretation to a radiologist.
5. **Prefer primary sources.** Cite the paper; use awesome-lists as living
   indexes to discover what's new.

## Core mental model (the MRI pipeline)

Keep this spine in mind so you can place any MRI question:

1. **Physics & contrast** — spins, RF excitation, T1/T2/T2\* relaxation, proton
   density; a *sequence* weights these to create contrast.
2. **Spatial encoding & k-space** — gradients encode position; the scanner
   samples **k-space** (the Fourier transform of the image) along a
   *trajectory* (Cartesian/radial/spiral/EPI). Center = contrast/SNR, edges =
   detail.
3. **Acquisition** — the *pulse sequence* (RF + gradient events) sets the
   contrast and trajectory; runs on *hardware* (magnet, gradients, RF coils,
   console).
4. **Raw data** — stored in a vendor raw format (Siemens twix, GE P-file,
   Philips raw) or the vendor-neutral **ISMRMRD**.
5. **Reconstruction** — turn k-space into images. Undersampling speeds scans but
   aliases; recon undoes it with parallel imaging, compressed sensing, low-rank,
   or learned/diffusion priors. Formally: measured `y = A x + noise`, with
   `A = (sampling) ∘ (Fourier/NUFFT) ∘ (coil sensitivities)`; solve
   `argmin_x ||A x − y||² + λ R(x)` — each method is a choice of `A`, `R`, and
   optimizer.
6. **Images → analysis** — converted to DICOM/NIfTI, organized (BIDS), then
   registered, segmented, and analyzed (structural, functional, diffusion).
7. **Quantification** — parameter maps (relaxometry, QSM, perfusion, MT), MR
   fingerprinting, and spectroscopy (metabolite concentrations).
8. **Interpretation & applications** — contrast reading, neuro/cardiac/body/MSK
   applications (research orientation, not diagnosis).

## How to route a question

Open the reference file matching the need (each is self-contained; open only
what you need):

| If the user is asking about… | Open |
|---|---|
| MR physics, k-space intuition, contrast, where to *learn* (courses, handbooks, free books) | [`references/foundations.md`](references/foundations.md) |
| Designing/programming pulse sequences and k-space trajectories, RF pulse design, simulation | [`references/sequences-and-trajectories.md`](references/sequences-and-trajectories.md) |
| DWI/DTI, ADC/FA/MD, gradients, diffusion preprocessing and model QC | [Diffusion skill and its DWI/DTI guide](../diffusion-mri/SKILL.md) |
| MRI hardware: low-field, open-source consoles, coils, gradients, safety | [`references/hardware.md`](references/hardware.md) |
| Which reconstruction method/paper applies + the landmark reading list (parallel imaging → CS → low-rank → DL → diffusion → fingerprinting) | [`references/recon-methods.md`](references/recon-methods.md) |
| Which reconstruction *software* to use and how (BART, SigPy, MIRT.jl, MRIReco.jl, torchkbnufft, DIRECT, Gadgetron) | [`references/tools.md`](references/tools.md) |
| Raw & image data formats (ISMRMRD, twix/P-file/Philips, DICOM, NIfTI, BIDS) and where to get data | [`references/data-and-formats.md`](references/data-and-formats.md) |
| Image analysis & processing: structural, fMRI, diffusion MRI, segmentation, registration, pipelines | [`references/analysis-processing.md`](references/analysis-processing.md) |
| Quantitative MRI (relaxometry, QSM, perfusion/ASL, MT) and MR spectroscopy | [`references/quantitative-and-spectroscopy.md`](references/quantitative-and-spectroscopy.md) |
| Programmatic access to papers/data — APIs, keys, and MCP servers | [`references/literature-access.md`](references/literature-access.md) |
| Writing up & submitting — MR journals, LaTeX templates, reporting standards, abstracts, preprints | [`references/publishing.md`](references/publishing.md) |
| How MR image contrast reads (T1/T2/FLAIR/DWI) — background orientation only | [`references/radiology-primer.md`](references/radiology-primer.md) |
| **Actually running a reconstruction** on real k-space (BART/SigPy, `.cfl`, twix, ISMRMRD) | hand off to the **mri-reconstruction** skill — this hub explains, that skill executes |

**What this hub owns outright:** image-level analysis has no sibling expert, so
fMRI/GLM, BIDS organization, DICOM↔NIfTI conversion, FreeSurfer, segmentation,
registration, fMRIPrep, and relaxometry/QSM mapping are *this* skill's
responsibility — answer them here via
[`references/analysis-processing.md`](references/analysis-processing.md) and
[`references/quantitative-and-spectroscopy.md`](references/quantitative-and-spectroscopy.md)
rather than looking for a specialist that doesn't exist. (Diffusion MRI is the
exception: `diffusion-mri` owns it.)

Cross-cutting requests pull from several files — e.g., "reproduce this spiral CS
paper on real scanner data" → `recon-methods` (method) + `tools` (BART/SigPy) +
`data-and-formats` (read the raw file) + `sequences-and-trajectories` (spiral).

## Living indexes (when this is stale)

MRI research moves fast. When you need something newer or a topic not covered
here, these community-maintained lists are the best next hop:

- Awesome MRI Reconstruction — https://github.com/Joyies/Awesome-MRI-Reconstruction
- Awesome DL-based CS-MRI — https://github.com/mosaf/Awesome-DL-based-CS-MRI
- Awesome MRI (broad) — https://github.com/dangom/awesome-mri
- ISMRM (the field's professional society & annual meeting) — https://www.ismrm.org

For finding papers programmatically, use the APIs/MCP servers in
`references/literature-access.md`.
