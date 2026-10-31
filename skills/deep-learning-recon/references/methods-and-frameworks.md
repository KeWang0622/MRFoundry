# Deep-learning reconstruction: methods, frameworks and data

Opened from the deep-learning-recon SKILL.md when a method, toolbox or dataset has to be chosen or cited.

## Method families (with citations)

- **Variational Network (VN)** — Hammernik et al., *MRM* 2018;79(6):3055–3071.
  Code: https://github.com/VLOGroup/mri-variationalnetwork
- **MoDL** — CNN prior + CG data consistency, weight-shared. Aggarwal et al.,
  *IEEE TMI* 2019. Code: https://github.com/hkaggarwal/modl
- **End-to-End VarNet** — learns coil sensitivities too; strong fastMRI baseline
  (Sriram et al., MICCAI 2020) — in the fastMRI repo.
- **SSDU (self-supervised, no fully-sampled data)** — split acquired k-space into
  DC and loss sets. Yaman et al., *MRM* 2020. Code:
  https://github.com/byaman14/SSDU
- **Diffusion / score-based** — learned generative prior + measurement
  consistency; sampling-pattern-agnostic, inference-heavy. Chung & Ye, *MedIA*
  2022 (https://github.com/hyungjin-chung/score-MRI); Jalal et al., NeurIPS 2021
  (https://github.com/utcsilab/csgm-mri-langevin).
- **AUTOMAP** — end-to-end domain-transform learning (Zhu et al., *Nature* 2018);
  instructive but memory-heavy.

## Frameworks & building blocks

- **DIRECT** — https://github.com/NKI-AI/direct — many baselines + training loops.
- **fastMRI** — https://github.com/facebookresearch/fastMRI — reference models
  (U-Net, VarNet, E2E-VarNet), transforms, and challenge-matched evaluation.
  **Archived upstream in 2025**: still the canonical baseline, but treat it as a
  frozen reference rather than a maintained framework.
- **ATOMMIC** — https://github.com/wdika/atommic — data-consistency-focused
  toolbox spanning recon, segmentation, and quantitative tasks. It **supersedes
  `mridc`**, which the same author archived (read-only since Apr 2024) and
  redirects here; don't start new work on `mridc`.
- **torchkbnufft** — https://github.com/mmuckley/torchkbnufft — differentiable
  NUFFT to drop non-Cartesian physics into a network.

## Data

**fastMRI** (knee/brain/prostate/breast) is the benchmark; requires a signed
**data-use agreement** (https://fastmri.med.nyu.edu). Fully-open alternative for
prototyping: mridata.org.
