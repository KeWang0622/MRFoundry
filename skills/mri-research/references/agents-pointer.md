# Optional project pointer to MRFoundry skills

Some coding agents read a project instruction file (`AGENTS.md`, `CLAUDE.md`) before they consult installed
skills. Adding this short pointer makes MRI work start from the matching skill and end with the finish check.
It is optional and contains no data, results or task-specific content.

```markdown
## MRI work in this project

MRFoundry MRI skills are installed in `.agents/skills/` (or your agent's skills folder). Before writing code
for an MRI task, read the ONE matching `SKILL.md`, follow its route table to the helper or reference it names,
and import its tested scripts instead of re-deriving their maths. Open other files only when the table
points to them.

- acquisition, pulse sequences, RF/gradient waveforms, Bloch simulation: `pulse-sequence-design`
- images or parameter maps from k-space or images (reconstruction, relaxometry, ASL, DCE, QSM): `mri-reconstruction`
- diffusion-weighted data: `diffusion-mri`
- hardware, field maps, shimming, coils, SAR, PNS, noise and SNR: `mri-hardware`
- trained reconstruction networks: `deep-learning-recon`
- studies with subjects or groups, statistics, reports and papers: `mri-research-workflow`
- spectroscopy, image analysis, formats and references: `mri-research`

Before finishing, run `python .agents/skills/mri-research-workflow/scripts/finish_check.py` with every
deliverable name and the documented entrypoint command, and fix every FAIL line.
```
