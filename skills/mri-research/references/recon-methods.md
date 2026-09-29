# Reconstruction methods & the landmark-paper reading list

Use this to (a) pick the right method for a task and (b) hand the user the
canonical paper. Every citation below was verified; include the DOI/arXiv id
when you cite so the user can find it behind their own library access. Do not
paste paper bodies — cite and summarize.

## Choosing a method (quick decision guide)

- **Fully sampled, just need an image?** Inverse FFT (Cartesian) or NUFFT
  (non-Cartesian) + coil combination — sensitivity-weighted with noise
  prewhitening is SNR-optimal (Roemer, below); root-sum-of-squares is the
  map-free fallback. See [`tools.md`](tools.md).
- **Undersampled, multi-coil, no training data?** Parallel imaging
  (ESPIRiT/SENSE/GRAPPA) — possibly combined with compressed sensing (L1-
  wavelet / TV) if acceleration is high and sampling is incoherent.
- **Undersampled + want state-of-the-art quality + have training data?**
  Deep-learning recon (unrolled/variational network); diffusion/score-based if
  you want a sampling-pattern-agnostic generative prior and can afford the
  inference cost.
- **Dynamic / multi-contrast / high-dimensional?** Low-rank + sparse (L+S),
  structured low-rank (e.g., SAKE/ALOHA-style), or subspace/low-rank DL.

## Parallel imaging

- **SENSE** — image-domain unfolding using coil sensitivity maps.
  Pruessmann KP, Weiger M, Scheidegger MB, Boesiger P. "SENSE: sensitivity
  encoding for fast MRI." *Magn Reson Med* 1999;42(5):952–962.
- **GRAPPA** — k-space interpolation from autocalibration lines (no explicit
  sensitivity maps). Griswold MA, et al. "Generalized autocalibrating partially
  parallel acquisitions (GRAPPA)." *Magn Reson Med* 2002;47(6):1202–1210.
- **SPIRiT** — GRAPPA generalized: enforce the k-space calibration-consistency
  relation at *every* k-space location together with data consistency, solved
  iteratively. That is what makes arbitrary (including non-uniform) sampling
  tractable, and it needs no explicit sensitivity maps. L1-SPIRiT adds
  joint-sparsity CS regularization. Lustig M, Pauly JM. "SPIRiT: Iterative
  self-consistent parallel imaging reconstruction from arbitrary k-space."
  *Magn Reson Med* 2010;64(2):457–471. doi:10.1002/mrm.22428.
  (It is **ESPIRiT**, below, that bridges the image-domain and k-space views —
  "where SENSE meets GRAPPA".)
- **ESPIRiT** — eigenvalue-based autocalibration for robust sensitivity maps;
  "where SENSE meets GRAPPA." The default way to estimate coil maps today.
  Uecker M, Lai P, Murphy MJ, Virtue P, Elad M, Pauly JM, Vasanawala SS,
  Lustig M. *Magn Reson Med* 2014;71(3):990–1001. doi:10.1002/mrm.24751.
  Code: https://github.com/mikgroup/espirit-python (and BART `ecalib`).
- **NLINV** — regularized nonlinear inversion that jointly estimates the image
  and coil sensitivities (calibrationless; strong for real-time/radial). Uecker
  M, Hohage T, Block KT, Frahm J. "Image reconstruction by regularized
  nonlinear inversion—joint estimation of coil sensitivities and image
  content." *Magn Reson Med* 2008;60(3):674–682. doi:10.1002/mrm.21691.
  Available as BART `nlinv`.
- **CG-SENSE** — iterative SENSE for **arbitrary (non-Cartesian) k-space** via
  conjugate gradient; the foundation of non-Cartesian parallel imaging.
  Pruessmann KP, Weiger M, Börnert P, Boesiger P. "Advances in sensitivity
  encoding with arbitrary k-space trajectories." *Magn Reson Med*
  2001;46(4):638–651.
- **SMASH** — the original k-space parallel-imaging idea GRAPPA generalizes
  (useful context when explaining why GRAPPA looks the way it does).
  Sodickson DK, Manning WJ. *Magn Reson Med* 1997;38(4):591–603.
  doi:10.1002/mrm.1910380414.
- **Partial Fourier** — acquire just over half of k-space and recover the rest
  from conjugate (Hermitian) symmetry via **homodyne** detection or **POCS**.
  Crucial caveat: Hermitian symmetry holds only for a *real-valued* image, so
  homodyne applies a low-pass **phase correction** first; phase errors are what
  limit how far you can push it. Noll DC, Nishimura DG, Macovski A. "Homodyne
  detection in magnetic resonance imaging." *IEEE Trans Med Imaging*
  1991;10(2):154–163. doi:10.1109/42.79473.

### What acceleration costs: the g-factor

Never quote an acceleration factor without the SNR it costs. For SENSE-type
reconstruction:

```
SNR_accel  =  SNR_full / (g · √R)
```

where the **geometry factor** `g ≥ 1` measures how ill-conditioned the unfolding
problem is at each voxel (coil geometry, sampling pattern, R). `g` blows up where
coil sensitivities are hard to distinguish — typically the image centre at high R
— so it is a *map*, not a scalar. Report g maps alongside R.

- **Coil combination and the array-SNR baseline** — optimal combination needs the
  receive **noise covariance**, so *prewhiten* before reconstruction; root-sum-of-
  squares is the map-free fallback and is not SNR-optimal. Roemer PB, Edelstein WA,
  Hayes CE, Souza SP, Mueller OM. "The NMR phased array." *Magn Reson Med*
  1990;16(2):192–225. doi:10.1002/mrm.1910160203.
- **g is analytic for SENSE**; for GRAPPA, ESPIRiT, CS, and nonlinear or learned
  reconstruction it generally is not — use Monte-Carlo **pseudo-replica** SNR
  estimation instead. Robson PM, Grant AK, Madhuranthakam AJ, Lattanzi R,
  Sodickson DK, McKenzie CA. *Magn Reson Med* 2008;60(4):895–907.
  doi:10.1002/mrm.21728.
- For learned reconstruction, note that regularization makes "SNR" ill-defined
  (noise is traded for bias/hallucination) — see the metrics caveats at the end
  of this file.

## Compressed sensing MRI

- **Sparse MRI (the foundational CS-MRI paper)** — Lustig M, Donoho D,
  Pauly JM. "Sparse MRI: The application of compressed sensing for rapid MR
  imaging." *Magn Reson Med* 2007;58(6):1182–1195. doi:10.1002/mrm.21391.
  Core idea: incoherent undersampling + transform sparsity (wavelets, finite
  differences) + nonlinear L1-regularized reconstruction.
- **L1-ESPIRiT / combined PI+CS** is the practical workhorse: ESPIRiT maps +
  L1-wavelet regularization, solved with BART `pics` or SigPy's app. See
  [`tools.md`](tools.md).
- Curated CS/DL index: https://github.com/mosaf/Awesome-DL-based-CS-MRI

## Low-rank, dynamic & structured low-rank

- **L+S (low-rank plus sparse)** for dynamic MRI — Otazo R, Candès E, Sodickson
  DK. "Low-rank plus sparse matrix decomposition for accelerated dynamic MRI."
  *Magn Reson Med* 2015;73(3):1125–1136.
- **k-t BLAST / k-t SENSE** — the classic spatiotemporal-correlation approach to
  dynamic MRI; useful background and still a baseline for cine/perfusion.
  Tsao J, Boesiger P, Pruessmann KP. "k-t BLAST and k-t SENSE: Dynamic MRI with
  high frame rate exploiting spatiotemporal correlations." *Magn Reson Med*
  2003;50(5):1031–1042. doi:10.1002/mrm.10611.
- **GRASP** — golden-angle radial sparse parallel MRI; combines compressed
  sensing, parallel imaging, and golden-angle radial for continuous dynamic
  imaging. Feng L, et al. *Magn Reson Med* 2014;72(3):707–717.
  doi:10.1002/mrm.24980.
- **XD-GRASP** — extra-dimensional, **motion-resolved** golden-angle recon: sort
  data into extra motion dimensions (respiratory/cardiac) instead of fighting
  motion. Feng L, et al. *Magn Reson Med* 2016;75(2):775–788.
  doi:10.1002/mrm.25665.
- **Structured low-rank matrix completion** — build a structured (Hankel /
  Casorati) matrix from local k-space neighbourhoods and complete it under a
  low-rank constraint. Calibrationless, so it is the family to reach for when no
  ACS exists. The three are distinct ideas, not variants of one:
  - **SAKE** — multi-channel block-Hankel low-rank completion, motivated by
    inter-coil linear dependency. Shin PJ, Larson PEZ, Ohliger MA, Elad M,
    Pauly JM, Vigneron DB, Lustig M. *Magn Reson Med* 2014;72(4):959–970.
    doi:10.1002/mrm.24997.
  - **LORAKS** — low-rank modelling of local k-space neighbourhoods, additionally
    exploiting **limited image support and phase** constraints (which neither SAKE
    nor ALOHA does). Haldar JP. *IEEE Trans Med Imaging* 2014;33(3):668–681.
    doi:10.1109/TMI.2013.2293974. Parallel-imaging extension **P-LORAKS**:
    Haldar JP, Zhuo J. *Magn Reson Med* 2016;75(4):1499–1514.
    doi:10.1002/mrm.25717.
  - **ALOHA** — the **annihilating-filter**-based Hankel low-rank framework,
    linking CS and parallel imaging. Jin KH, Lee D, Ye JC. *IEEE Trans Comput
    Imaging* 2016;2(4):480–495. doi:10.1109/TCI.2016.2601296.

## Deep-learning reconstruction

The dominant paradigm is the **unrolled network**: unroll N iterations of an
iterative solver and learn the regularizer/updates end-to-end, keeping the
measured data-consistency step.

- **Variational Network (VN)** — Hammernik K, et al. "Learning a variational
  network for reconstruction of accelerated MRI data." *Magn Reson Med*
  2018;79(6):3055–3071. Code: https://github.com/VLOGroup/mri-variationalnetwork
  (PyTorch reimplementation: https://github.com/khammernik/sigmanet ).
- **MoDL** — model-based DL with a CNN prior and conjugate-gradient data
  consistency, weight-shared across iterations. Aggarwal HK, Mani MP, Jacob M.
  "MoDL: Model-Based Deep Learning Architecture for Inverse Problems." *IEEE
  TMI* 2019;38(2):394–405. Code: https://github.com/hkaggarwal/modl
- **End-to-End VarNet** — the strong fastMRI baseline that also learns coil
  sensitivities. Sriram A, et al. "End-to-End Variational Networks for
  Accelerated MRI Reconstruction." MICCAI 2020. Implemented in the fastMRI repo
  (below).
- **Deep cascade** — Schlemper J, et al. "A Deep Cascade of CNNs for Dynamic MR
  Image Reconstruction." *IEEE TMI* 2018. Code:
  https://github.com/js3611/Deep-MRI-Reconstruction
- **SSDU (self-supervised, no fully-sampled data)** — trains a physics-guided
  unrolled network by splitting the acquired k-space into a data-consistency
  set and a loss set; crucial when fully-sampled references don't exist. Yaman
  B, et al. "Self-supervised learning of physics-guided reconstruction neural
  networks without fully sampled reference data." *Magn Reson Med*
  2020;84(6):3172–3191. doi:10.1002/mrm.28378. Code:
  https://github.com/byaman14/SSDU
- **AUTOMAP** — learns the entire sensor→image domain transform end-to-end
  (a different philosophy from unrolling); memory-heavy but instructive. Zhu B,
  Liu JZ, Cauley SF, Rosen BR, Rosen MS. "Image reconstruction by domain-
  transform manifold learning." *Nature* 2018;555:487–492.
  doi:10.1038/nature25988 (arXiv:1704.08841).
- **Frameworks that collect many DL methods:** DIRECT
  (https://github.com/NKI-AI/direct), **ATOMMIC**
  (https://github.com/wdika/atommic — supersedes the archived `mridc`), the
  reproducible benchmark
  (https://github.com/zaccharieramzi/fastmri-reproducible-benchmark), and the
  fastMRI repo (https://github.com/facebookresearch/fastMRI — reference models
  and evaluation code, **archived** upstream in 2025, so treat it as a stable
  baseline rather than an actively maintained framework).
- **Vendor DL reconstruction is the de-facto clinical baseline** — Siemens *Deep
  Resolve*, GE *AIR Recon DL*, Philips *SmartSpeed*. Reviewers of a new learned-
  recon paper will ask how you compare against what is already shipping, so name
  it explicitly in related work even though the implementations are proprietary.

### fastMRI challenge (benchmarks & what won)

- 2019/2020 challenges established the modern benchmarks. Results paper:
  Muckley MJ, et al. "Results of the 2020 fastMRI Challenge for Machine
  Learning MR Image Reconstruction." *IEEE TMI* 2021;40(9):2306–2317.
  arXiv:2012.06318. Takeaway: unrolled/variational approaches with learned
  sensitivities led; SSIM and radiologist evaluation both mattered, and
  transfer to unseen scanners was a distinct, harder track.

## Diffusion / score-based reconstruction (generative priors)

Rapidly evolving; these use a learned generative prior and enforce measurement
consistency during sampling. Sampling-pattern-agnostic but computationally
heavy at inference. Codebases the user specifically wants to know:

- **Score-based diffusion for MRI** — Chung H, Ye JC. "Score-based diffusion
  models for accelerated MRI." *Medical Image Analysis* 2022;80:102479.
  arXiv:2110.05243. Code: https://github.com/hyungjin-chung/score-MRI
- **CSGM / posterior sampling via Langevin dynamics** — Jalal A, Arvinte M,
  Daras G, Price E, Dimakis AG, Tamir JI. "Robust Compressed Sensing MRI with
  Deep Generative Priors." NeurIPS 2021. arXiv:2108.01368.
  Code: https://github.com/utcsilab/csgm-mri-langevin
- **Foundational (not MRI-specific) score-SDE** that these build on: Song Y, et
  al. "Score-Based Generative Modeling through SDEs." ICLR 2021.
  Code: https://github.com/yang-song/score_sde_pytorch
- **High-frequency space diffusion (HFS-SDE)** — Cao C, et al. "High-Frequency
  Space Diffusion Model for Accelerated MRI." *IEEE Trans Med Imaging*
  2024;43(5):1853–1865. doi:10.1109/TMI.2024.3351702.
  Code: https://github.com/Aboriginer/HFS-SDE
- Also watch **SPIRiT-Diffusion** (arXiv:2304.05060) for self-consistency-
  driven diffusion. For anything newer, check the awesome-lists and
  [`literature-access.md`](literature-access.md).

## Quantitative & fingerprinting

- **MR Fingerprinting (MRF)** — acquires with pseudo-randomized sequence
  parameters so each tissue yields a unique signal "fingerprint," then matches
  against a Bloch-simulated dictionary to map T1/T2/etc. in one scan. A distinct
  paradigm where reconstruction and quantification are intertwined (and where
  low-rank/subspace and deep-learning acceleration are active research). Ma D,
  Gulani V, Seiberlich N, Liu K, Sunshine JL, Duerk JL, Griswold MA. "Magnetic
  resonance fingerprinting." *Nature* 2013;495:187–192. doi:10.1038/nature11971.
- **Subspace / low-rank model-based recon** for MRF and multi-contrast qMRI —
  project the signal time series onto a low-dimensional temporal subspace so
  highly-undersampled quantitative recon becomes tractable. Zhao B, et al.
  *Magn Reson Med* 2018;79(2):933–942 (doi:10.1002/mrm.26701); see also
  Assländer J, et al. *Magn Reson Med* 2018;79(1):83–96 (low-rank ADMM,
  doi:10.1002/mrm.26639).
- Related: quantitative susceptibility mapping (QSM), relaxometry, and other
  quantitative recon are adjacent areas worth a pointer when a user's goal is
  parameter maps rather than a single image (see
  [`quantitative-and-spectroscopy.md`](quantitative-and-spectroscopy.md)).

## Denoising

Thermal-noise denoising can act like extra acceleration (higher effective SNR):

- **NORDIC** — locally low-rank thermal-noise removal for MRI/fMRI. Repo:
  https://github.com/SteenMoeller/NORDIC_Raw . Vizioli L, et al. *Nat Commun*
  2021;12:5181 (doi:10.1038/s41467-021-25431-8).
- **MP-PCA (Marchenko–Pastur PCA)** — random-matrix-theory denoising, widely
  used for diffusion MRI via MRtrix3 `dwidenoise`
  (https://github.com/MRtrix3/mrtrix3). Veraart J, et al. *NeuroImage*
  2016;142:394–406 (doi:10.1016/j.neuroimage.2016.08.016).
- **Patch2Self** — self-supervised diffusion-MRI denoising (in DIPY,
  https://github.com/dipy/dipy). Fadnavis S, Batson J, Garyfallidis E. NeurIPS
  2020 (arXiv:2011.01355).

## Evaluation & image-quality metrics

Start with the intended use and the evidence needed for the claim. See the
[evaluation and attribution guide](evaluation-and-attribution.md) for a planning
template, task-specific examples, failure tests and original-source credit.

SSIM (Wang Z, et al. *IEEE Trans Image Process* 2004;13(4):600–612,
doi:10.1109/TIP.2003.819861), PSNR and NMSE/NRMSE can support benchmark comparisons
when conventions are explicit. Keep their interpretation tied to that purpose;
perceptual scores or attractive images are not substitutes for task validation.

## Related recon-adjacent methods

- **Deep J-Sense** (joint sensitivity + image, unrolled):
  https://github.com/utcsilab/deep-jsense
- **Complex-valued networks** for MR: https://github.com/MRSRL/complex-networks-release
- **Memory-efficient learning** for high-dimensional recon:
  https://github.com/mikgroup/MEL_MRI
- **UFLoss** (unsupervised feature loss for sharper recon):
  https://github.com/mikgroup/UFLoss
- **Extreme MRI** (huge-scale volumetric/dynamic recon):
  https://github.com/mikgroup/extreme_mri
- **Subtle inverse crimes** (a caution about over-idealized retrospective
  experiments — worth citing when reviewing methodology):
  https://github.com/mikgroup/data_crimes
