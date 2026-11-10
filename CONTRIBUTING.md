# Contributing to MRFoundry

Help make MRI research workflows easier to execute, check and reuse. We welcome
tested workflow improvements, new skills, scientific helper fixes, primary
references and corrections. The current skill collection is a starting point;
contributions can extend it to new methods and research areas.

## The five-minute contribution

You do not need to read the rest of this file to fix one link or add one paper:

1. Find the right file (table below) and edit it on GitHub — the pencil icon
   creates the branch and the PR for you.
2. Put the primary source in the PR description: the URL you opened, or the DOI.
3. Add a line under `## Unreleased` in `CHANGELOG.md`.

CI checks repository structure, shell scripts, links and upstream availability;
a maintainer reviews the content. Availability checks do not verify that a
source supports a scientific claim.

## From a research lesson to a shared skill

MRFoundry's [self-improvement workflow](docs/SELF-IMPROVEMENT.md) connects private
project experience to reviewed public guidance. For a workflow or helper change:

1. **Describe the trigger.** What task, output or assumption exposed the issue?
   Distinguish what you observed from your explanation of it.
2. **Propose a focused change.** Update the instruction or helper responsible
   for that decision. State the data, methods and conditions it applies to.
3. **Attach shareable evidence.** Provide a minimal example or source, the
   commands and environment, and the relevant output checks. Keep private
   `.mrfoundry/` notebooks, credentials and restricted data out of the PR.
4. **Check the effect.** For behavioral changes, show the relevant behavior
   before and after. Preserve a useful regression example and check another
   case when claiming broader reuse. Report regressions and exceptions.
5. **Submit for review.** Explain what a researcher should do differently.
   Maintainers review the scope, evidence and checks before merging.

Agents may help draft changes; contributors remain responsible for checking
them. A local observation can justify a narrowly scoped rule without being
presented as a general scientific conclusion. Citation or wording corrections
only need checks appropriate to that change.

## Where things live

| If your change is about… | Edit |
|---|---|
| Orientation, routing, project memory or cross-domain references | [`skills/mri-research/`](skills/mri-research/) |
| Running a study end-to-end, venues, manuscript mechanics | [`skills/mri-research-workflow/`](skills/mri-research-workflow/) |
| Classical recon that *executes* (BART/SigPy, ESPIRiT, PICS, NUFFT) | [`skills/mri-reconstruction/`](skills/mri-reconstruction/) |
| Anything **trained** (unrolled, self-supervised, diffusion priors) | [`skills/deep-learning-recon/`](skills/deep-learning-recon/) |
| Diffusion MRI: DTI/DKI/NODDI, topup/eddy, CSD, tractography | [`skills/diffusion-mri/`](skills/diffusion-mri/) |
| Pulse sequences, trajectories, RF, SMS, vendor SDKs | [`skills/pulse-sequence-design/`](skills/pulse-sequence-design/) |
| Magnets, gradients, coils, consoles, low-field, MR safety | [`skills/mri-hardware/`](skills/mri-hardware/) |

Deep background and citations belong in the hub's `references/*.md`; an expert
skill should stay short and actionable and link to the hub. Keep each topic in
**one** owner skill and cross-reference rather than duplicating — if you find a
topic with two owners or none, that's a bug worth an issue.

## Design philosophy (please preserve it)

MRFoundry combines **domain knowledge, executable helpers and research memory**.
Contributions should help an agent make a better decision or produce a result
that a researcher can inspect:

- **Link and summarize; do not vendor.** Never add datasets, model weights, or
  copyrighted text (textbook chapters, paywalled paper bodies). Cite the source
  and describe it in your own words.
- **Point to primary sources.** Prefer the original paper/repo over a
  secondary summary. Use awesome-lists as living indexes, not as the citation.
- **Keep the "which tool for which task" framing.** The reference files are
  organized to help a researcher *decide*, not just to enumerate.
- **Make checks explicit.** Say what artifact to inspect, what criterion to
  apply and what the check establishes. Preserve the distinction between a
  successful command and a scientifically useful result.

## Quality bar for additions

- **Verify every link and citation before submitting.** Confirm the URL
  resolves and the repo/paper exists (e.g., `gh repo view <owner>/<repo>`, or
  open the DOI). Broken or hallucinated links are the one thing that makes a
  reference hub worse than nothing.
- **Cite consistently.** Papers as `Author(s). "Title." Venue Year;Vol(Issue):
  Pages. doi:…` (or an `arXiv:XXXX.XXXXX` id). Repos as full GitHub URLs.
- **Match the file.** The reference set (under `skills/mri-research/references/`)
  is: `foundations.md` (physics/courses/handbooks), `sequences-and-trajectories.md`
  (acquisition, RF, trajectories, SMS, correction), `hardware.md` (hardware +
  safety), `recon-methods.md` (reconstruction methods/papers + denoising +
  metrics), `tools.md` (reconstruction software), `data-and-formats.md`
  (formats + datasets), `analysis-processing.md` (structural/fMRI/dMRI, cardiac/
  body/MSK, segmentation, radiomics), `quantitative-and-spectroscopy.md`
  (qMRI + MRS), `literature-access.md` (paper/data APIs & MCP), `publishing.md`
  (journals, LaTeX, reporting standards), `radiology-primer.md` (contrast
  reading, non-diagnostic). Put each addition in the matching file; if a topic
  spans files, add a short cross-reference rather than duplicating.
- **Stay concise.** Each entry should earn its place — one to three lines of
  what it is and when to reach for it.

## How to propose a change

1. Fork and create a branch (`main` is protected; everything lands via PR).
2. Edit the relevant skill, reference or helper. For a new skill, add its
   `SKILL.md`, register it in `skills.sh.json`, and link it from the README.
3. Add a bullet to `CHANGELOG.md` under the `## Unreleased` heading.
4. Open a pull request with the problem, change, evidence and validation.

Run the repository checks from the root (stdlib-only Python):

```bash
python3 .github/scripts/validate_repo.py      # structure, versions, links-on-disk
python3 .github/scripts/check_upstreams.py    # upstream availability; requires network
```

For changes to project-memory initialization, also run
`python3 -m unittest discover -s .github/tests`. For scientific helpers or
workflow instructions, run the relevant task checks and report the commands
and results in the PR; CI does not run every MRI helper test.

## Maintainer release checklist

CI enforces a consistent version across `skills/*/SKILL.md` frontmatter and
`CITATION.cff`; any version fields in the README must also agree. To cut a release:

1. Update all skill versions and `CITATION.cff`, including its `date-released`.
   Update any versioned README fields if present.
2. Write the `CHANGELOG.md` section and move anything from `## Unreleased` into
   it.
3. Merge via PR, tag `vX.Y.Z`, and publish the GitHub release.
4. Repoint that version's CHANGELOG link definition at the new release tag (it
   points at a `compare/` range until the tag exists, so link-checking passes on
   the PR).

## Scope reminders

- The **radiology primer** is deliberately non-diagnostic background. Do not
  turn it into clinical guidance.
- Respect **dataset access terms** (e.g., the fastMRI data-use agreement). Do
  not add instructions that circumvent an access gate.

Questions or larger proposals (e.g., a new reference area) are welcome as an
issue first, so we can align on scope before you invest the work.
