# Quantitative MRI (qMRI) & MR spectroscopy (MRS)

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this when the goal is **parameter maps or metabolite concentrations**, not a
single qualitative image — relaxometry, susceptibility, perfusion, magnetization
transfer, and spectroscopy. These methods pair a specialized acquisition with a
model-fitting step, so they sit between acquisition (`sequences-and-
trajectories.md`) and analysis ([`analysis-processing.md`](analysis-processing.md)). Links verified;
point users to each tool's own docs.

## Quantitative MRI (parameter mapping)

The idea: acquire several images with varying sequence parameters, then fit a
signal model per voxel to recover a physical quantity (T1, T2, T2\*, PD, MT,
susceptibility, perfusion). Reproducible and scanner-comparable, unlike
weighted images.

- **qMRLab** — https://github.com/qMRLab/qMRLab — a broad, multi-method toolbox
  for simulating, fitting, and visualizing many qMRI models (T1/T2 relaxometry,
  MT/ihMT, diffusion, field mapping). The best general starting point for qMRI
  methods and teaching.
- **hMRI toolbox** — https://github.com/hMRI-group/hMRI-toolbox — SPM-based
  multi-parameter mapping (R1, R2\*, PD, MT) for "in-vivo histology"
  (microstructure) studies.
- **Relaxometry basics:** T1 mapping (e.g., variable flip angle, MP2RAGE,
  inversion recovery), T2/T2\* mapping (multi-echo). For **MR fingerprinting**
  — a one-shot route to simultaneous T1/T2 maps — see the fingerprinting entry
  in [`recon-methods.md`](recon-methods.md); its reconstruction and quantification are intertwined.

## Quantitative susceptibility mapping (QSM)

Recovers tissue magnetic susceptibility (iron, calcium, myelin, venous blood)
from gradient-echo phase. A multi-step pipeline (phase unwrapping → background-
field removal → dipole inversion).

- **SEPIA** — https://github.com/kschan0214/sepia — a MATLAB GUI that chains
  established QSM algorithms into a reproducible pipeline; good for
  standardizing a QSM workflow rather than reimplementing each step.
- The hard step is **dipole inversion**: the dipole kernel has a zero cone in
  k-space, so the inverse problem is ill-posed and needs regularization. This is
  why two pipelines on the same phase data can disagree — always report which
  inversion (and which background-field removal) you used.
  - Review / primer: Wang Y, Liu T. "Quantitative susceptibility mapping (QSM):
    Decoding MRI data for a tissue magnetic biomarker." *Magn Reson Med*
    2015;73(1):82–101. doi:10.1002/mrm.25358.
  - **MEDI** (morphology-enabled dipole inversion), the canonical regularized
    inversion: de Rochefort L, Liu T, Kressler B, et al. *Magn Reson Med*
    2010;63(1):194–206. doi:10.1002/mrm.22187.

## Fat–water separation (Dixon) & CEST

- **Fat–water (Dixon)** — multi-echo chemical-shift encoding separates fat and
  water and quantifies **proton-density fat fraction (PDFF)** and **R2\***. Two
  distinct things get conflated here, so keep them straight:
  - **IDEAL is the species-decomposition step** — an iterative least-squares fit
    that, *given* a field map, solves for water and fat (and extends to any set of
    chemical species, multi-coil). Reeder SB, Wen Z, Yu H, et al. *Magn Reson Med*
    2004;51(1):35–45. doi:10.1002/mrm.10675. Original two-point idea: Dixon WT.
    "Simple proton spectroscopic imaging." *Radiology* 1984;153(1):189–194.
    doi:10.1148/radiology.153.1.6089263.
  - **Graph cuts solve the field map**, not the decomposition. The fit is
    non-convex and has a water/fat *swap* ambiguity at every voxel; a graph-cut
    (or region-growing) step picks a globally consistent field map before/with
    IDEAL. Hernando D, Kellman P, Haldar JP, Liang Z-P. *Magn Reson Med*
    2010;63(1):79–90. doi:10.1002/mrm.22177.
  - **For quantitative PDFF you need a multi-peak fat spectrum and simultaneous
    R2\*** — a single-peak fat model biases PDFF, and unmodelled R2\* decay biases
    it further. Yu H, Shimakawa A, McKenzie CA, Brodsky E, Brittain JH, Reeder SB.
    *Magn Reson Med* 2008;60(5):1122–1134. doi:10.1002/mrm.21737.
  - Reference implementations: the **ISMRM fat–water toolbox** and its challenge
    data — https://www.ismrm.org/workshops/FatWater12/data.htm
- **CEST (chemical exchange saturation transfer)** — saturation-transfer
  contrast sensitive to exchangeable protons (e.g., amide proton transfer, APT).
  Design/simulate with **pulseq-CEST** (https://github.com/kherz/pulseq-cest) and
  its preset library.

## Perfusion

- **Arterial spin labeling (ASL)** — magnetically labels arterial blood as an
  endogenous tracer to quantify cerebral blood flow (CBF). The subtraction image
  is *not* CBF: you get perfusion only by inverting a **kinetic model** that
  accounts for label decay at blood T1, the arterial transit delay, and
  exchange into tissue. Buxton RB, Frank LR, Wong EC, Siewert B, Warach S, Edelman
  RR. "A general kinetic model for quantitative perfusion imaging with arterial
  spin labeling." *Magn Reson Med* 1998;40(3):383–396. doi:10.1002/mrm.1910400308.
  - **Label the acquisition precisely** — **PCASL** (pseudo-continuous, the
    recommended default), **PASL** (pulsed), and **VSASL** (velocity-selective,
    transit-delay-insensitive) need different model parameters, and the
    **post-labeling delay (PLD)** must be reported: too short and label is still
    in the arteries, too long and it has decayed.
  - **Follow the consensus paper** for implementation and quantification defaults
    (including the single-PLD CBF equation): Alsop DC, Detre JA, Golay X, et al.
    *Magn Reson Med* 2015;73(1):102–116. doi:10.1002/mrm.25197.
  - Fit with **BASIL / oxford_asl** (part of FSL):
    https://fsl.fmrib.ox.ac.uk/fsl/docs/#/perfusion/asl (Python port **oxasl**:
    https://github.com/physimals/oxasl). BIDS-native pipeline: **ASLPrep**
    (https://github.com/PennLINC/aslprep).
- **DSC / DCE** — dynamic susceptibility contrast and dynamic contrast-enhanced
  perfusion use gadolinium bolus tracking (note: gadolinium is a contrast agent
  — a clinical/safety consideration, out of scope for method tooling here).

## MR spectroscopy (MRS)

Measures the concentration of metabolites (NAA, creatine, choline, lactate,
GABA, …) from the chemical-shift spectrum rather than forming an image. Common
localization: single-voxel PRESS/STEAM, and edited MEGA-PRESS for GABA.

- **LCModel** — http://www.lcmodel.com/ — the long-standing reference for
  linear-combination metabolite quantification. Closed-source but free to
  download (since 2020); still a common comparison baseline.
- **Osprey** — https://github.com/schorschinho/osprey — modern all-in-one
  open-source MRS processing and quantification (MATLAB); a good default for new
  work.
- **FSL-MRS** — https://github.com/wtclarke/fsl_mrs — Python MRS preprocessing,
  fitting, and quantification (the maintained GitHub mirror; the FMRIB docs host
  had a stale TLS cert at last check).
- **Gannet** — https://github.com/markmikkelsen/Gannet — the standard tool for
  GABA-edited (MEGA-PRESS) MRS analysis.
- **Tarquin** — http://tarquin.sourceforge.net/ — open-source automated 1H-MRS
  quantification (time-domain fitting). Source also at
  https://github.com/martin3141/tarquin, but that repo has had no commits since
  2021, so treat Tarquin as dormant: fine as a comparison baseline, not a
  foundation for new tooling.
- **MRSHub** — https://mrshub.org (software index: https://mrshub.org/software_all/)
  — the community hub for MRS: a curated software list, tutorials, example data,
  and the mailing list. Best first stop for anything MRS, and the place to check
  whether a tool is still alive.

## Which tool for which task

- *General qMRI modeling / simulation / fitting* → qMRLab; hMRI toolbox for
  SPM-based multi-parameter maps.
- *Susceptibility maps from GRE phase* → SEPIA.
- *Cerebral blood flow from ASL* → BASIL / oxford_asl (or oxasl in Python);
  ASLPrep for BIDS-native preprocessing. Report the labeling scheme and PLD.
- *PDFF / fat–water separation* → the ISMRM fat–water toolbox implementations;
  insist on a multi-peak fat model with simultaneous R2\* if the number is meant
  to be quantitative.
- *Metabolite quantification* → Osprey or FSL-MRS for open pipelines; LCModel as
  the reference baseline; Gannet specifically for GABA-edited data; MRSHub to
  check what is current.
