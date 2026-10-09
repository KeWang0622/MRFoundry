# Reading MR image contrast — background orientation only

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

**Scope and safety.** This primer exists so you can follow *research*
conversations about MR image contrast (e.g., "train on T2-FLAIR," "the lesion
is bright on DWI"). It is **not** clinical or diagnostic guidance. Do not use it
to interpret a real patient's scan, suggest a diagnosis, or make management
recommendations. If a user asks for medical interpretation of an actual scan,
decline and refer them to a qualified radiologist. Keep this framing explicit
whenever the topic comes up.

## Why "weighting" matters

An MR image's appearance depends on which tissue property the sequence
emphasizes ("weighting"), set by timing parameters — repetition time (**TR**)
and echo time (**TE**), plus inversion time (**TI**) and b-value where
relevant. The same anatomy looks completely different across weightings; that
is the point, and it's why datasets are labeled by contrast.

## The common contrasts (rule-of-thumb appearance)

- **T1-weighted** (short TR, short TE): fat bright, fluid (CSF) dark. Good for
  anatomy. Gadolinium contrast agent shortens T1 → enhancing tissue turns
  bright ("post-contrast T1").
- **T2-weighted** (long TR, long TE): fluid bright, many pathologies (edema,
  many lesions) bright. Good for detecting fluid/pathology.
- **PD-weighted** (long TR, short TE): proton-density; intermediate contrast,
  useful for e.g. cartilage/joints.
- **FLAIR** (T2 with fluid signal nulled by an inversion pulse): CSF is
  suppressed (dark) while lesions near fluid stay bright — heavily used in
  neuro to make periventricular lesions conspicuous.
- **DWI / ADC** (diffusion-weighted): sensitizes to water diffusion via strong
  gradients (b-value). Restricted diffusion (e.g., acute stroke, some tumors)
  is bright on high-b DWI and dark on the computed ADC map. DWI is usually
  EPI-based (see [`sequences-and-trajectories.md`](sequences-and-trajectories.md)), so it inherits EPI
  distortions.
- **T2\*** / **GRE / SWI**: sensitive to susceptibility — blood products,
  calcium, iron show as signal loss/blooming.

## Quick orientation table

| Weighting | CSF / fluid | Fat | Typical research use |
|---|---|---|---|
| T1 | dark | bright | anatomy; post-contrast enhancement |
| T2 | bright | intermediate–bright | fluid/edema/lesion detection |
| FLAIR | dark (nulled) | intermediate | neuro lesions near ventricles |
| DWI (high b) | dark–intermediate | — | restricted diffusion (stroke, tumor) |
| ADC map | bright | — | quantifies diffusion (restriction = dark) |

## How this connects to reconstruction research

- **Labels = contrasts.** fastMRI and similar datasets are organized by
  weighting; a recon model trained on one contrast may not transfer to another
  (a real evaluation concern — cf. the fastMRI transfer track).
- **Artifacts a recon person cares about** read differently than clinical
  findings: aliasing/wrap, Gibbs ringing, motion ghosting, EPI distortion,
  chemical-shift. When discussing image quality, separate *reconstruction
  artifacts* (your domain) from *clinical interpretation* (a radiologist's).
- **Metrics:** SSIM/PSNR/NMSE quantify fidelity but don't guarantee diagnostic
  quality — which is why challenges add radiologist reads. Keep that distinction
  when advising on evaluation.

For deeper (still non-diagnostic) physics of why each contrast arises, see
Elster's MRIquestions.com and Hornak's *Basics of MRI* in [`foundations.md`](foundations.md).
