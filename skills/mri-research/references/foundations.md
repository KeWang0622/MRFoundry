# Foundations: MR physics, k-space, and where to learn

[MRFoundry](https://github.com/KeWang0622/MRFoundry) · [Reference index](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

Use this when the user wants to build or refresh MR intuition, or asks "where
do I learn this?" Point to these resources; summarize concepts in your own
words rather than reproducing copyrighted text.

## The concepts worth being fluent in

- **Signal & relaxation:** net magnetization, RF excitation (flip angle), free
  induction decay; **T1** (longitudinal recovery), **T2** (transverse decay),
  **T2\*** (incl. field inhomogeneity), proton density. Contrast comes from how
  a sequence weights these (see [`radiology-primer.md`](radiology-primer.md)).
- **Spatial encoding:** slice-selective excitation, frequency encoding
  (readout gradient), phase encoding. Gradients make resonant frequency a
  function of position — this is what writes the image into k-space.
- **k-space:** the Fourier domain of the image. Each acquired sample is a
  Fourier coefficient. The trajectory (how you traverse k-space) is set by the
  gradient waveforms. Center = contrast/SNR, periphery = resolution/edges.
- **Sampling & artifacts:** Nyquist, field-of-view vs. sampling spacing,
  aliasing/wrap, Gibbs ringing, chemical shift, motion, off-resonance
  (especially for spiral/EPI). Undersampling trades scan time for artifacts
  that reconstruction must undo.
- **Sequence families:** spin echo, gradient echo, EPI, bSSFP, fast/turbo spin
  echo, inversion recovery, diffusion-weighted. Each is a recipe of RF +
  gradient events that produces a particular contrast and k-space trajectory.

## Free, open, high-quality learning resources

**Courses (publicly posted lecture material):**

- **UC Berkeley EE225E / BIOE265 — Principles of Magnetic Resonance Imaging**
  (Miki Lustig). Graduate MRI course; lecture notes, homework, and projects
  have been posted publicly across semesters. Entry points:
  - Course hub: https://sites.google.com/berkeley.edu/ee225ebioe265
  - Example archived offerings with notes/HW:
    https://inst.eecs.berkeley.edu/~ee225e/sp14/ ,
    https://inst.eecs.berkeley.edu/~ee225e/sp17/
  - Some lectures are on YouTube (search "EE225E Principles of MRI Berkeley").
  - A good first stop: it teaches MRI from a signal-processing / reconstruction
    viewpoint, so it pairs directly with
    [`recon-methods.md`](recon-methods.md).
- **Stanford EE369B — Medical Imaging Systems II** (Dwight Nishimura; the MR
  systems course). Now often taught as **RAD 229** (Brian Hargreaves) with
  extensive open notes and MATLAB: https://web.stanford.edu/class/rad229/
- **Stanford EE369C — Medical Image Reconstruction** (John Pauly). Builds recon
  tools from non-uniform sampling, projections, undersampling, autofocus:
  https://ee369c.stanford.edu/ (also https://web.stanford.edu/class/ee369c ).
  Lustig trained at Stanford with Pauly, so the Berkeley and Stanford materials
  share lineage and notation.

**Free online books / references:**

- **Nishimura, *Principles of Magnetic Resonance Imaging*** — the classic
  engineering-oriented MR text (signal-processing / Fourier view). Not free but
  inexpensive (Lulu print-on-demand); the natural companion to EE369B/EE225E.
- **Hornak, *The Basics of MRI*** — free, open-access hypertext intro to MR
  physics: https://www.cis.rit.edu/htbooks/mri/
- **Elster, MRIquestions.com ("Questions and Answers in MRI")** — free, deep,
  and beloved Q&A reference on MR physics and technology; excellent for
  clarifying specific points of confusion: https://www.mriquestions.com/
- **ISMRM educational materials** — the **ISMRM** (https://www.ismrm.org) runs
  the field's main annual meeting and publishes educational course content
  through its online learning portal, "MR Academy." Its journals *Magnetic
  Resonance in Medicine* (MRM) and *JMRI* are where most landmark methods appear.

**Canonical textbooks & handbooks (not free, but the standard references):**

- **McRobbie, Moore, Graves & Prince, *MRI from Picture to Proton*** (Cambridge
  University Press) — the most approachable rigorous introduction; ideal for
  building intuition.
- **Westbrook (& Talbot), *MRI in Practice*** (Wiley-Blackwell) — practical and
  widely used by technologists and clinicians.
- **Bernstein, King & Zhou, *Handbook of MRI Pulse Sequences*** (Elsevier /
  Academic Press, 2004) — the definitive reference for pulse-sequence and
  gradient design; the book to reach for when implementing a sequence (pairs
  with [`sequences-and-trajectories.md`](sequences-and-trajectories.md)).
- **Haacke, Brown, Thompson & Venkatesan, *Magnetic Resonance Imaging: Physical
  Principles and Sequence Design*** (Wiley) — deep physics and sequence design.

**Broad living index:**

- dangom/awesome-mri — https://github.com/dangom/awesome-mri (curated list
  spanning physics, sequences, analysis, and reconstruction).

## Calibrating explanations to the reader

Gauge the reader's level and match it. For an experienced MR researcher, assume
fluency with k-space, Fourier, parallel imaging, and optimization — skip
first-principles derivations and lead with the precise result, the canonical
citation, and the practical tool. For someone newer, start from Hornak /
MRIquestions and the course notes above, building intuition before formalism.
