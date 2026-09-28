# Papers and textbooks — deep-learning-recon

[Skill instructions](../SKILL.md) · [All skill reading lists](../../../REFERENCES.md)

A starter reading list, organized by the decision it supports. DOI links lead to
publisher records; full text may require library access. Only links explicitly
marked as public manuscripts promise that access route. Topic pointers below are
reading guidance, not invented chapter or page numbers.

## Unrolled reconstruction

Hammernik K, et al. **Learning a variational network for reconstruction of accelerated MRI data.** Magnetic Resonance in Medicine, 2018;79:3055–3071. [DOI](https://doi.org/10.1002/mrm.26977).

**Use it for:** How variational reconstruction becomes a trainable network.

## Model-based learning

Aggarwal HK, Mani MP, Jacob M. **MoDL: Model-Based Deep Learning Architecture for Inverse Problems.** IEEE Transactions on Medical Imaging, 2019;38:394–405. [PubMed / publisher links](https://pubmed.ncbi.nlm.nih.gov/30106719/) · [Public author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC6760673/). DOI: `10.1109/TMI.2018.2865356`.

**Use it for:** Learned priors coupled to a physics-based data-consistency step.

## Self-supervision

Yaman B, et al. **Self-supervised learning of physics-guided reconstruction neural networks without fully sampled reference data.** Magnetic Resonance in Medicine, 2020;84:3172–3191. [DOI](https://doi.org/10.1002/mrm.28378).

**Use it for:** SSDU training with separate acquired-data subsets for consistency and loss.

## Generative priors

Chung H, Ye JC. **Score-based diffusion models for accelerated MRI.** Medical Image Analysis, 2022;80:102479. [DOI](https://doi.org/10.1016/j.media.2022.102479).

**Use it for:** Score-based reconstruction; distinguish these diffusion models from diffusion-weighted MRI.

## Practical references and software

[Additional DL methods and implementations](../../mri-research/references/recon-methods.md)

Software documentation explains installation and APIs; it does not replace the
method paper. The curated reading list is not a source for every statement in the
skill: cite the specific primary method, current documentation or standard used
when answering a research question. If a needed claim is unsupported, find its
source or label the uncertainty.
