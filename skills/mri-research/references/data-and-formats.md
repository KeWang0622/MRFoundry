# Data formats, vendor conversion, and datasets

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this when the user has (or wants) MR data — raw k-space or reconstructed
images: to identify a format, convert it to something workable, or find an open
dataset. Always respect each dataset's license / data-use agreement (see ground
rules in SKILL.md). For analysis-oriented handling of DICOM/NIfTI/BIDS, see also
[`analysis-processing.md`](analysis-processing.md).

## The interchange standard: ISMRMRD

**ISMRMRD** (ISMRM Raw Data format) is the vendor-neutral raw k-space container
the community standardizes on: an XML header (acquisition parameters, encoding,
coils) plus HDF5 datasets of the acquisitions. Convert vendor raw → ISMRMRD,
then read it from any toolbox (BART, SigPy, MRIReco.jl, Gadgetron).

- Spec & C/C++ API: https://github.com/ismrmrd/ismrmrd
- Python API: https://github.com/ismrmrd/ismrmrd-python
- Python tools/utilities: https://github.com/ismrmrd/ismrmrd-python-tools
- Viewer: https://github.com/ismrmrd/ismrmrdviewer

## Vendor raw formats and how they differ

Each scanner vendor writes its own proprietary raw format. Practical
orientation (details vary by software baseline/version):

- **Siemens — "twix" / `.dat`** (meas.dat, VB/VD/VE baselines). Contains raw
  ADC data + a large embedded protocol header. Read with the community
  `mapVBVD` (MATLAB) or `pymapVBVD`/`twixtools` (Python), or convert to
  ISMRMRD: https://github.com/ismrmrd/siemens_to_ismrmrd
- **GE — "P-file" (`P#####.7`)** plus, on modern systems, ScanArchive
  (`.h5`). Vendor SDK is **Orchestra** (requires a GE research agreement — the
  converter below links against it). Convert to ISMRMRD:
  https://github.com/ismrmrd/ge_to_ismrmrd
- **Philips — raw is a triplet `.raw` / `.lab` / `.sin`** (data, labels,
  scan-info) — sometimes also `.cpx`/`.data`/`.list`. Convert to ISMRMRD:
  https://github.com/ismrmrd/philips_to_ismrmrd
- **Bruker (preclinical)** — `fid` / `2dseq` with `method`/`acqp` parameter
  files (ParaVision). Often handled via BrkRaw or vendor tools.

Rule of thumb when a user shows you a raw file: identify the vendor from the
extension/structure, convert to ISMRMRD with the matching converter above, then
reconstruct with the toolbox of their choice ([`tools.md`](tools.md)). If they only need
the trajectory/sampling, that lives in the sequence (`sequences-and-
trajectories.md`).

## Image-level formats (DICOM, NIfTI, BIDS)

Once data is reconstructed into images, the analysis world uses different
formats:

- **DICOM** — the clinical/scanner image standard (pixel data + rich metadata).
  Read/write in Python with **pydicom** (https://github.com/pydicom/pydicom).
- **NIfTI** — the neuroimaging analysis volume format. Convert DICOM→NIfTI with
  **dcm2niix** (https://github.com/rordenlab/dcm2niix); read/write with
  **nibabel** (https://github.com/nipy/nibabel).
- **BIDS** — the standard for organizing a whole study so pipelines run
  automatically: https://bids.neuroimaging.io/ (convert with heudiconv/dcm2bids).

See [`analysis-processing.md`](analysis-processing.md) for how these feed the analysis pipelines.

## Open datasets (mind the license/DUA)

### Raw k-space (reconstruction)

- **mridata.org** — http://mridata.org — open archive of multi-vendor raw
  k-space (knee, brain, …), auto-converted to ISMRMRD, with parameters and
  thumbnails. Source: https://github.com/mikgroup/mridata . Basic recon
  scripts: https://github.com/MRSRL/mridata-recon . Per-dataset terms apply.
- **fastMRI** (NYU Langone + FAIR) — the large-scale benchmark: knee (~1.5k raw
  + 10k DICOM), brain (~7k), plus **prostate** and **breast** expansions. Raw
  k-space + DICOM. **Requires a signed data-use agreement / application.**
  - Apply / download: https://fastmri.med.nyu.edu  ·  Project: https://fastmri.org
  - Code & models: https://github.com/facebookresearch/fastMRI
  - Also mirrored on the AWS Open Data registry (still under the fastMRI DUA).
  - Extra labels: https://github.com/microsoft/fastmri-plus ;
    prostate: https://github.com/cai2r/fastMRI_prostate
- **OCMR** — open cardiovascular multi-coil k-space (real-time cardiac):
  https://ocmr.info . Good for dynamic/non-Cartesian cardiac recon.
- **SKM-TEA** (Stanford Knee MRI Multi-Task Evaluation) — quantitative DESS knee
  scans with raw k-space, DICOMs, tissue segmentations, and pathology bounding
  boxes; enables joint recon + segmentation + detection evaluation. Desai AD, et
  al., NeurIPS 2021 Datasets (arXiv:2203.06823).
  Code/data: https://github.com/StanfordMIMI/skm-tea ·
  https://aimi.stanford.edu/datasets/skm-tea-knee-mri
- **Calgary-Campinas (CC-359)** — multi-coil 3D T1 brain raw k-space; a common
  brain-recon benchmark. https://sites.google.com/view/calgary-campinas-dataset/home
- **CMRxRecon (MICCAI 2023 / 2024)** — cardiac MRI reconstruction challenge
  datasets (cine, mapping, and more). Code:
  https://github.com/CmrxRecon/CMRxRecon and
  https://github.com/CmrxRecon/CMRxRecon2024 . Results:
  "The state-of-the-art in cardiac MRI reconstruction: Results of the CMRxRecon
  challenge in MICCAI 2023," *Medical Image Analysis* 2025 (arXiv:2404.01082).
- **M4Raw** — multi-contrast, multi-repetition, multi-channel k-space for
  **low-field** MRI research. *Scientific Data* 2023;10:264.

### Image-level (analysis / ML)

Reconstructed-image datasets for analysis, segmentation, and machine learning
(not raw k-space). Access terms vary — check each before use:

- **OpenNeuro** — https://openneuro.org — 1000+ public BIDS datasets
  (MRI/fMRI/EEG/MEG/PET). **Fully open** (mostly CC0), no application.
- **IXI** — https://brain-development.org/ixi-dataset/ — ~600 healthy-subject
  brain scans (T1/T2/PD/MRA/DTI). **Fully open** (CC BY-SA 3.0).
- **Human Connectome Project (HCP)** — https://www.humanconnectome.org —
  high-quality multimodal brain MRI (structural, dMRI, rest/task fMRI).
  Registration (ConnectomeDB) + open-access terms; sensitive variables need a
  restricted-access DUA.
- **UK Biobank** (imaging) —
  https://www.ukbiobank.ac.uk/enable-your-research/about-our-data/imaging-data —
  large-scale multi-organ MRI (brain, cardiac, abdominal) + linked health data.
  **Application required** (approved project + access fee).
- **ADNI** — https://adni.loni.usc.edu — longitudinal Alzheimer's brain MRI +
  PET/clinical/biomarkers. **Application + DUA** via LONI IDA.
- **OASIS** — https://www.oasis-brains.org — cross-sectional/longitudinal brain
  MRI for aging/Alzheimer's (OASIS-1/2/3/4). **Registration + DUA**.
- **BraTS** — https://www.synapse.org/brats — multi-institutional brain-tumor
  MRI with expert tumor segmentations. **Registration + DUA** via Synapse.
- **ACDC** (Automated Cardiac Diagnosis Challenge) — cine cardiac MRI with
  LV/RV/myocardium segmentations and diagnosis labels (150 patients); free
  download after registration on the CREATIS platform.
  https://www.creatis.insa-lyon.fr/Challenge/acdc/ (Bernard O, et al. *IEEE TMI*
  2018;37(11):2514–2525).
- **M&Ms** (Multi-Centre, Multi-Vendor & Multi-Disease Cardiac Segmentation) —
  cine cardiac MRI across 4 vendors and multiple centres (375 subjects);
  registration required. https://www.ub.edu/mnms/ (Campello VM, et al.
  *IEEE TMI* 2021;40(12):3543–3554).

- Do NOT help bypass any access gate. If a user lacks access, point them to the
  official application and to fully-open alternatives (OpenNeuro, IXI,
  mridata.org, OCMR, Calgary-Campinas).

## Getting from raw to image (sanity pipeline)

1. Convert vendor raw → ISMRMRD (or load the provided `.h5`).
2. Read k-space + trajectory + coil data. Options: the Python `ismrmrd` package,
   MRIReco.jl (native ISMRMRD reader), or BART's `ismrmrd` tool — but note BART
   builds that tool only when compiled with `ISMRMRD=1` (the Makefile defaults to
   `ISMRMRD=0`), so on a stock build `bart ismrmrd` does not exist. Check with
   `bart ismrmrd -h`; if it's missing, read in Python and write a `.cfl` with
   BART's `cfl.py`.
3. Estimate coil sensitivities (ESPIRiT: BART `ecalib` / SigPy `EspiritCalib`).
4. Reconstruct (FFT/NUFFT for fully sampled; PICS/CS/DL for undersampled — see
   [`recon-methods.md`](recon-methods.md) and [`tools.md`](tools.md)).
5. Coil-combine and inspect. Watch for FOV/orientation and readout-oversampling
   conventions, which differ by vendor.
