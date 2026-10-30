# Optional project pointer to MRFoundry skills

Some coding agents read a project instruction file (`AGENTS.md`, `CLAUDE.md`) before
they consult installed skills. Adding this short pointer to that file makes MRI work
start from the matching skill. It is optional; it adds no data or results.

```markdown
## MRI work in this project

MRFoundry MRI skills are installed in `.agents/skills/` (or your agent's skills folder).
Before writing code for an MRI task, read the matching `SKILL.md` and use its checks
and tested scripts:

- acquisition, pulse sequences, RF/gradient waveforms, Bloch simulation: `pulse-sequence-design`
- images or parameter maps from k-space or images (reconstruction, relaxometry, perfusion): `mri-reconstruction`
- diffusion-weighted data: `diffusion-mri`
- hardware, field maps, shimming, coils, SAR, PNS, noise and SNR: `mri-hardware`
- trained reconstruction networks: `deep-learning-recon`
- studies with subjects or groups, statistics, reports and papers: `mri-research-workflow`
- anything else, image analysis, formats and references: `mri-research`
```
