# From MRI evidence to a manuscript

Use this guide when planning, drafting or revising a paper. Start from the user's
question and available evidence; a venue name alone is not a scientific claim.
The study-design suggestions below are editorial guidance, not venue mandates.
Official instructions were checked on **2026-10-07**; fetch the target article
type, conference year and track's current rules before formatting a submission.

## Build the evidence packet before polished prose

1. Read the relevant project notebook and actual results. Separate planned,
   executed, independently checked and superseded experiments. Ask only for
   missing information that changes the argument; draft around explicit gaps.
2. Map each proposed claim to a run/configuration, dataset split, analysis and
   figure or table. Record the independent sampling unit, effect size and
   uncertainty. A plausible sentence or an attractive image is not evidence.
3. Verify the closest prior work and original method/software sources. Record
   which specific comparison supports the gap. Do not claim “first” from a quick
   search. Never invent references, participant counts, results or approvals.
4. Make a figure plan: question → comparison → observation → supported claim.
   Generate scientific plots from recorded outputs; identify simulated and
   acquired data, units, display windows, exclusions and uncertainty. Do not use
   image generation to fabricate scientific results.
5. Draft Methods and Results from that packet, then the introduction, discussion,
   title and abstract. Use `[RESULT NEEDED: ...]` where evidence is missing.
   Match the user's requested scope: a paragraph edit does not require a new study.

Copy the [paper plan](../assets/paper-plan.md) into the user's project without
overwriting an existing manuscript. It is an editable planning aid, not an
upstream journal template.

## Choose the argument, then the venue

### MICCAI — a focused computational contribution

**Writing strategy:** Make the technical idea and its medical-imaging relevance
clear early. Separate the proposed mechanism from implementation changes.
For learning methods, compare matched training/data/compute conditions and
include a component ablation and a failure or shift test that challenges the
claim. These are recommended experiment choices, not universal requirements.

**Suggested narrative:** Problem and gap → method → experimental protocol →
main comparison and ablation → limitations. Give the key evidence space before
adding many secondary benchmarks.

**Submission source:** [MICCAI 2026 guidelines](https://conferences.miccai.org/2026/en/PAPER-SUBMISSION-GUIDELINES.html)
and [FAQ](https://conferences.miccai.org/2026/en/PAPER-SUBMISSION-FAQ.html).
The 2026 rules specify supplied templates and double-blind review; check identity
leaks in supplements, code links and PDF metadata. These are archived-year
pointers, not the next deadline or a guarantee about a future edition.

### MRM — explain the MR mechanism and demonstrate it

**Writing strategy:** Connect the signal model, acquisition or reconstruction
change to the measurement it improves. Report relevant sequence parameters,
coil/calibration assumptions and sampling conventions. Choose simulation,
phantom or in-vivo experiments according to the claim; label feasibility as
feasibility. Assess bias, repeatability or artifacts when image similarity alone
cannot answer the question.

**Format source:** [MRM author guidelines](https://onlinelibrary.wiley.com/page/journal/15222594/homepage/author-guidelines).
Research articles use Purpose / Methods / Results / Conclusion in the abstract;
an optional Theory section can support the mechanism. Article types differ.
Disclose and cite overlapping conference work; do not treat an ISMRM abstract
as equivalent to a full conference paper. Consult the source for exact rules.

### JMRI — organize around the imaging question and study design

**Writing strategy:** Define the population, intended measurement or clinical
question, comparator and reference standard. Explain inclusion/exclusion,
reader assessments, missing data and independent validation as relevant. An
improvement in reconstruction metrics does not establish diagnostic benefit.

**Format source:** [JMRI author guidelines](https://onlinelibrary.wiley.com/page/journal/15222586/homepage/forauthors.html).
For original research, the structured abstract makes study type, population,
field strength/sequence, assessment and statistical tests explicit. Follow the
current article-type headings. Describe ethics/consent as actually documented;
never fill them in from a template assumption. Discuss study-design limitations
and keep the conclusion within the tested population and endpoint.

### IEEE TMI — establish methodological innovation and rigorous evaluation

**Writing strategy:** Identify the methodological contribution beyond applying
an established model. Present the formulation and assumptions, isolate the
mechanism with controlled comparisons, and explain robustness and computational
cost. Pick validation that challenges the claimed generalization.

**Policy source:** [TMI author instructions](https://ieeetmi.org/authors-instructions/).
TMI explicitly requires methodological innovation. For a conference extension,
cite the original and document substantial additional rigor and thoroughness;
provide the required supporting material. The current instructions distinguish
initial submissions from resubmissions and discourage routine cover letters
except specified cases. Check formatting and AI-use disclosure at submission.

## Worked planning example — accelerated diffusion MRI

**Illustrative proposal only; no experiments or results are asserted.**

- User question: “Can we accelerate acquisition without changing the diffusion
  measurements we intend to interpret?”
- Knowledge needed: diffusion modeling for FA/MD endpoints; sequence design for
  EPI and b-value/b-vector conventions; reconstruction for noise/aliasing and
  phase assumptions; workflow guidance for comparisons and uncertainty.
- Claim to test: at a prespecified acquisition budget, a candidate method has
  acceptable parameter bias and repeatability relative to a justified reference.
  Define acceptable bounds before testing, with domain input; a nonsignificant
  difference alone cannot establish equivalence.
- Design: use an established processing pipeline, matched preprocessing and a
  justified reference; separate development subjects from evaluation subjects.
  Report scan time, exclusions, per-subject endpoint errors and uncertainty.
  Test susceptibility/motion or low-SNR failure cases when supported by the data.
- Figure plan: acquisition/analysis diagram; paired parameter maps with units;
  agreement and bias plots; failure examples. Image metrics are supporting
  measurements, not substitutes for the parameter endpoint.
- Venue decision: a new computational method may suit MICCAI/TMI; an MR-method
  or measurement study may suit MRM; a sufficiently designed clinical imaging
  study may suit JMRI. Changing the venue does not create missing evidence.

## Revision and final checks

For each reviewer point, produce: concern → response → supporting evidence →
exact manuscript location. Distinguish completed new analyses from proposed
ones. If a request cannot be met, explain the limitation and narrow the claim.
Use the [response template](../assets/reviewer-response.md).

Before handing over a submission package, check abstract/table/text agreement,
source attribution, figure provenance, anonymization where required, ethics and
availability statements, prior-publication disclosure, and current AI policies.
Record unresolved items instead of claiming the paper is submission-ready.
Preparing a manuscript does not authorize uploading, emailing, submitting or
publishing it; perform those actions only within the user's authorization.

## Methodological sources

Use the [annotated reading list](reading-list.md) for CLAIM 2024, COBIDAS and
MRI physics references. Use CLAIM for imaging AI reporting and COBIDAS within
its neuroimaging scope; neither is a universal venue checklist. The shared
[evaluation guide](https://github.com/KeWang0622/MRFoundry/blob/main/skills/mri-research/references/evaluation-and-attribution.md)
explains endpoint selection and original-source attribution. Consult original
papers for the particular diffusion/reconstruction method used in a manuscript.
