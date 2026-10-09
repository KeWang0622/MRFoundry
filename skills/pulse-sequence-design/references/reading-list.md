# Papers and textbooks — pulse-sequence-design

[Skill instructions](../SKILL.md) · [All skill reading lists](https://github.com/KeWang0622/MRFoundry/blob/main/REFERENCES.md)

A starter reading list, organized by the decision it supports. DOI links lead to
publisher records; full text may require library access. Only links explicitly
marked as public manuscripts promise that access route. Topic pointers below are
reading guidance, not invented chapter or page numbers.

## Core handbook

Bernstein MA, King KF, Zhou XJ. **Handbook of MRI Pulse Sequences.** Academic Press, 2004. [Publisher and contents](https://www.sciencedirect.com/book/monograph/9780120928613/handbook-of-mri-pulse-sequences).

**Use it for:** Look up the contrast, RF/gradient design and readout family needed for the experiment.

## EPI foundation

Mansfield P. **Multi-planar image formation using NMR spin echoes.** Journal of Physics C: Solid State Physics, 1977;10:L55–L58. [DOI](https://doi.org/10.1088/0022-3719/10/3/004).

**Use it for:** Foundational rapid echo-planar spatial encoding.

## DENSE foundation

Aletras AH, Ding S, Balaban RS, Wen H. **DENSE: Displacement Encoding with Stimulated Echoes in Cardiac Functional MRI.** Journal of Magnetic Resonance, 1999;137:247–252. [DOI](https://doi.org/10.1006/jmre.1998.1676) · [Public author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC2887318/).

**Use it for:** Displacement encoded in stimulated-echo phase; distinct from diffusion attenuation.

## Sequence framework

Layton KJ, et al. **Pulseq: A rapid and hardware-independent pulse sequence prototyping framework.** Magnetic Resonance in Medicine, 2017;77:1544–1552. [DOI](https://doi.org/10.1002/mrm.26235).

**Use it for:** The sequence-description/interpreter architecture; current API details still come from version-matched docs.

## Practical references and software

[Sequence families, EPI and DENSE guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/sequences-and-trajectories.md) · [Pulseq examples](https://pulseq.github.io/tutorials.html)

Software documentation explains installation and APIs; it does not replace the
method paper. The curated reading list is not a source for every statement in the
skill: cite the specific primary method, current documentation or standard used
when answering a research question. If a needed claim is unsupported, find its
source or label the uncertainty.
