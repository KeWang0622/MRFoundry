# Contributing to MRFoundry

Thanks for helping keep this a high-quality entry point for the **MRI research**
community — the whole pipeline, not just reconstruction. Contributions that add
landmark papers, new toolboxes, corrected or updated links, additional
vendor/format notes, or new open datasets are all welcome.

## The five-minute contribution

You do not need to read the rest of this file to fix one link or add one paper:

1. Find the right file (table below) and edit it on GitHub — the pencil icon
   creates the branch and the PR for you.
2. Put the primary source in the PR description: the URL you opened, or the DOI.
3. Add a line under `## Unreleased` in `CHANGELOG.md`.

That's it. CI does the rest (structure, ShellCheck, link check, and a check that
every repo/DOI/package you cited actually exists), and a maintainer reviews.

## Where things live (7 skills)

| If your change is about… | Edit |
|---|---|
| Orientation, routing, or any of the 11 reference files | [`skills/mri-research/`](skills/mri-research/) |
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

This is a **pointer / reference skill**, not a data or textbook dump. The value
is in accurate navigation and good judgment, so:

- **Link and summarize; do not vendor.** Never add datasets, model weights, or
  copyrighted text (textbook chapters, paywalled paper bodies). Cite the source
  and describe it in your own words.
- **Point to primary sources.** Prefer the original paper/repo over a
  secondary summary. Use awesome-lists as living indexes, not as the citation.
- **Keep the "which tool for which task" framing.** The reference files are
  organized to help a researcher *decide*, not just to enumerate.

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
2. Make your edit in the appropriate `references/*.md` (or a `SKILL.md` routing
   table if you add a new area).
3. Add a bullet to `CHANGELOG.md` under the `## Unreleased` heading.
4. Open a pull request describing the addition and linking the primary source
   you verified.

Run the checks locally first if you like — both are stdlib-only Python:

```bash
python3 .github/scripts/validate_repo.py      # structure, versions, links-on-disk
python3 .github/scripts/check_upstreams.py    # every repo / DOI / package resolves
```

## Maintainer release checklist

Version lives in **three** places and CI enforces that they agree: every
`skills/*/SKILL.md` frontmatter, `CITATION.cff`, and the README badge + BibTeX
block. To cut a release:

1. Bump all three (all seven skills), and date the `CITATION.cff`
   `date-released`.
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
