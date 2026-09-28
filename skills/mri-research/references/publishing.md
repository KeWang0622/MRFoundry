# Publishing MRI research: journals, LaTeX, reporting standards

Use this when the user is writing up MRI work — choosing a venue, finding a
journal's author guidelines or LaTeX template, meeting a reporting/reproducibility
standard, or submitting an abstract/preprint. Links point to official author
pages; summarize requirements rather than pasting them.

Note: several publisher pages (Wiley, Elsevier, RSNA, MIT Press) block automated
fetching but open normally in a browser — they are not login-gated. If a link
appears to fail programmatically, it's the bot-block, not a dead URL.

## Venue summary: journals, conferences and meeting abstracts

**MRM is a journal; MICCAI and CVPR are conferences; ISMRM is a society whose
annual meeting publishes abstracts.** Label the publication type when reviewing
or comparing evidence. The following is a fit guide, not a ranking or an
acceptance guarantee. Select by the claim and audience, not just prestige.

| Venue | Publication type / audience | When to consider it | Evidence to emphasize |
|---|---|---|---|
| **MRM — Magnetic Resonance in Medicine** | Journal; MR methods, physics and engineering | Acquisition, reconstruction, diffusion or quantitative MR methods | Physical assumptions, technical validation, reproducibility and limitations |
| **JMRI** | Journal; clinical MR applications | Diagnostic or clinical-use studies | Study design, cohorts, reference standards and clinical relevance |
| **IEEE TMI** | Journal; medical imaging methodology | Reconstruction, learning and image-analysis advances | Methodological contribution, strong comparisons and broad validation |
| **Medical Image Analysis (MedIA)** | Journal; computational medical imaging | Substantial analysis/learning methods | Technical depth, meaningful medical tasks and generalization |
| **MICCAI** | Conference proceedings; medical image computing and computer-assisted intervention | New methods tied to medical imaging or intervention | Clear contribution, medical relevance, baselines and robust evaluation |
| **ISMRM annual meeting** | Meeting abstracts and presentations; MR community | Communicating a focused MR result and obtaining specialist feedback | One clear question, methods, quantitative results and supported conclusion |
| **CVPR / ICCV / ECCV** | Conference proceedings; computer vision | MRI work with a substantive vision-method contribution | Explain what generalizes beyond an application-specific pipeline; compare fairly |
| **NeurIPS / ICLR / ICML** | Conference proceedings; ML | MRI motivates a substantive learning or inference contribution | Method or theory, controlled experiments and reproducibility |
| **NeuroImage / Imaging Neuroscience** | Journals; neuroimaging | Brain imaging methods or neuroscience findings, including dMRI | Acquisition/preprocessing transparency, statistics and interpretation |
| **NMR in Biomedicine / MAGMA** | Journals; biomedical MR and MR methods | Diffusion, spectroscopy, quantitative MR or technical studies | Measurement validity, experimental controls and biomedical context |

For example, a better EPI distortion method may fit MRM; a new medical-image
learning method may fit MICCAI/TMI/MedIA; a general vision method demonstrated on
MRI may fit CVPR. These are editorial judgments to check against the venue's
current scope and related accepted work, not rules inferred from the modality.
An ISMRM abstract and a later full article are different evidence records;
link them without counting them as independent studies.

Official starting points:
- [ISMRM journals](https://www.ismrm.org/journals/) and
  [abstract submission](https://www.ismrm.org/abstract-submission-and-review/).
- [MICCAI Society](https://www.miccai.org/) and the
  [2026 paper guidelines](https://conferences.miccai.org/2026/en/PAPER-SUBMISSION-GUIDELINES.html).
- [CVPR](https://cvpr.thecvf.com/), [CVF open-access proceedings](https://openaccess.thecvf.com/)
  and [2026 author guidelines](https://cvpr.thecvf.com/Conferences/2026/AuthorGuidelines).
- [NeurIPS](https://neurips.cc/), [ICLR](https://iclr.cc/), [ICML](https://icml.cc/).

Before a submission, reopen the **target year and track** instructions and record
the date checked. Verify scope, template, page/word limits, anonymity, deadlines
and time zone, supplementary material, code/data policies, prior-publication and
concurrent-submission rules. Do not reuse a past year's limits or assume that
CVPR and NeurIPS use the same template. The linked 2026 pages are dated examples,
not evergreen instructions for the next cycle.

## Journal author guidelines (and LaTeX support)

- **Magnetic Resonance in Medicine (MRM, Wiley)** — guidelines:
  https://onlinelibrary.wiley.com/page/journal/15222594/homepage/author-guidelines
  · **Official MRM LaTeX class:**
  https://onlinelibrary.wiley.com/journal/15222594/la_tex_class_file
- **Journal of Magnetic Resonance Imaging (JMRI, Wiley)** —
  https://onlinelibrary.wiley.com/page/journal/15222586/homepage/forauthors.html
  (Word-based; no official LaTeX template).
- **NMR in Biomedicine (Wiley)** —
  https://analyticalsciencejournals.onlinelibrary.wiley.com/hub/journal/10991492/homepage/forauthors.html
  (use the generic Wiley LaTeX template).
- **MAGMA — Magn. Reson. Materials in Physics, Biology and Medicine (Springer)**
  — https://link.springer.com/journal/10334/submission-guidelines (accepts Word
  or the Springer Nature LaTeX template).
- **IEEE Transactions on Medical Imaging (TMI)** —
  https://ieeetmi.org/authors-instructions/ (use the IEEEtran LaTeX class).
- **Medical Image Analysis (Elsevier)** —
  https://www.sciencedirect.com/journal/medical-image-analysis/publish/guide-for-authors
  (LaTeX via elsarticle).
- **NeuroImage (Elsevier)** —
  https://www.sciencedirect.com/journal/neuroimage/publish/guide-for-authors
  (LaTeX via elsarticle).
- **Imaging Neuroscience (MIT Press)** —
  https://direct.mit.edu/imag/pages/guide_for_authors (single all-in-one PDF at
  initial submission; LaTeX accepted at revision).
- **Radiology (RSNA)** —
  https://pubs.rsna.org/page/radiology/author-instructions (Word-based).
- **Radiology: Artificial Intelligence (RSNA)** —
  https://pubs.rsna.org/page/ai/author-instructions (Word-based).

## LaTeX templates & classes

- **Wiley** (covers MRM/JMRI/NMR in Biomed): the MRM class file above, plus the
  general Wiley template:
  https://authors.wiley.com/author-resources/Journal-Authors/Prepare/latex-template.html
- **IEEEtran** (IEEE TMI and other IEEE venues): https://ctan.org/pkg/ieeetran
  (also on the IEEE Author Center and Overleaf).
- **elsarticle** (Elsevier — MedIA, NeuroImage): https://ctan.org/pkg/elsarticle
  · Elsevier LaTeX instructions:
  https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions
- **Springer Nature** (MAGMA):
  https://www.springernature.com/gp/authors/campaigns/latex-author-support
- **Overleaf template gallery** (many of the above, ready to fork):
  https://www.overleaf.com/gallery
- **arXiv submission help** (LaTeX source requirements):
  https://info.arxiv.org/help/submit/index.html

## Reporting & reproducibility standards

Increasingly expected — and often required — especially for ML/quantitative work:

- **COBIDAS** (OHBM) — best-practice reporting for (f)MRI studies:
  https://www.humanbrainmapping.org/COBIDAS/ (2016 MRI report PDF:
  https://www.humanbrainmapping.org/files/2016/COBIDASreport.pdf).
- **CLAIM** — Checklist for Artificial Intelligence in Medical Imaging (RSNA):
  https://pubs.rsna.org/page/ai/claim (2024 update: doi:10.1148/ryai.240300).
- **TRIPOD+AI** — reporting for clinical prediction models using AI:
  https://www.tripod-statement.org/
- **ISMRM Reproducible Research Study Group (RRSG)** — code-and-data sharing
  practices; partners with MRM on optional code review:
  https://ismrm.github.io/rrsg/ (MRM also states its reproducible-research
  policy in the author guidelines above).

## Abstracts & meetings

- **ISMRM Annual Meeting** — the field's main conference; abstracts are the
  primary way MR methods are first presented:
  https://www.ismrm.org/abstract-submission-and-review/ (choose the target year from the official site;
  https://www.ismrm.org/26m/call/ is the 2026 archive).

## Practical notes

- **Match venue to contribution:** a new recon algorithm → MRM or IEEE TMI; a
  clinical validation → JMRI/Radiology; a neuroimaging analysis → NeuroImage.
- **Share code and data** (respecting dataset DUAs — see [`data-and-formats.md`](data-and-formats.md)):
  a public repo with a fixed release/DOI (e.g., via Zenodo) strengthens review
  and satisfies reproducibility policies.
- **Cite primary methods** from [`recon-methods.md`](recon-methods.md) and tools from [`tools.md`](tools.md)
  correctly; many MR toolboxes request a specific citation.


## Summarize a journal issue or conference topic

Use this when asked for “recent MRM diffusion papers,” “MICCAI reconstruction
highlights,” or a cross-venue digest. This is an on-demand literature workflow;
it does not imply automatic monitoring or an exhaustive survey.

1. **Set scope:** topic, venues, date window and publication types. If unspecified,
   state the chosen scope. Distinguish online publication date, issue year and
   conference year. Search official journal tables of contents/proceedings, then
   use the [literature-access guide](literature-access.md) for discovery APIs.
2. **Verify each record:** title, authors, venue/year, DOI or proceedings URL,
   abstract/full-text access, and linked code/data. Do not invent missing values.
   Deduplicate preprint, abstract and journal versions; retain their relationship.
3. **Read proportionally:** label summaries based only on an abstract. Extract
   method, cohort/data, acquisition, baselines, metrics and limitations from the
   paper when accessible. Separate the authors' claims from your assessment.
4. **Synthesize across papers:** group by problem (e.g., EPI distortion,
   diffusion modeling, reconstruction), compare evidence and tradeoffs, then
   identify what to reproduce or read next. Do not compare numbers across
   incompatible datasets or treat missing code as proof the work is invalid.

A reusable evidence table:

| Paper / primary link | Type and version | Question and method | Data / baselines | Main finding | Limits / access | Next action |
|---|---|---|---|---|---|---|
| Verified citation | Journal, proceedings, abstract or preprint | What changed and why | Protocol/cohort and comparison | Quantitative result with context | Caveats; abstract-only if applicable | Read, reproduce, compare or defer |

For DWI/DTI papers, capture shells/directions, resolution, correction pipeline,
model, gradient handling and confounds. For EPI/DENSE papers, capture readout or
encoding parameters, correction/tracking, validation reference and motion effects.
End with a short synthesis and search date; store evidence-linked project notes
only when they belong to the user's research project.
