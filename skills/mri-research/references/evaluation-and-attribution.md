# Evaluation and attribution in MRI research

Use this guide when choosing reconstruction evidence, comparing methods, or
writing scientific claims. Scale the evaluation to the stated task; a format
conversion or demonstration does not require a clinical study.

## Scientific basis

Haldar JP. **The “State of the Art” in MR Image Reconstruction? Knowledge,
Culture, and What We Leave Behind in An Era of Big Data and Machine Learning.**
Magnetic Resonance in Medicine, 2026;96:7–12.
[Publisher full text](https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.70377).
This editorial argues for multidimensional evaluation, explicit trade-offs,
active investigation of failures, and independent testing. It is a perspective,
not a validated evaluation protocol or an endorsement of this project.

The procedures below are this project's operational guidance. Cite the editorial
for its arguments; cite original experimental or methodological sources for
specific empirical claims rather than treating this guide as their origin.

## Before selecting a metric

Write a short evaluation plan with these fields, using stated assumptions when
the user has not specified them:

- **Question and intended use:** what decision will these images support?
- **Evidence needed:** endpoint, reference standard, comparator and relevant
  population/acquisition conditions. State what result would contradict the claim.
- **Scope:** exploratory demo, benchmark reproduction, technical validation or
  clinical evaluation. Keep conclusions within the evidence actually collected.
- **Known gaps:** missing reference data, untested conditions and resources needed
  for further validation. Do not silently replace an unavailable endpoint with
  an easy image metric and retain the original claim.

Retain benchmark metrics when requested for comparability, but label that purpose.
For each reported NRMSE/NMSE, PSNR or SSIM result, record the implementation,
normalization/data range, mask/crop, complex-versus-magnitude convention,
reference construction and aggregation unit. Check alignment and reference noise.
A reference reconstruction is not automatically ground truth. Perceptual metrics
trained on natural images also need justification for the MRI task.

## Examples of evidence matched to a question

| Question | Candidate evidence | Boundary on the claim |
|---|---|---|
| Does a pipeline reproduce a published benchmark? | Match the published preprocessing and metrics; identify code, weights and data versions | Demonstrates reproduction under those conditions |
| Does reconstruction preserve a quantitative parameter? | Parameter bias and precision against a justified reference; stratify relevant tissue/conditions | Image similarity alone does not establish quantitative accuracy |
| Can subtle structure be recovered? | Controlled feature/contrast tests with known objects and matched acquisitions; document the reconstruction's response | Phantom or simulated findings need separate validation on real data |
| Does a method improve diagnosis? | Task-specific reader study with an appropriate reference standard and uncertainty estimates | Appearance ratings alone do not establish diagnostic accuracy |

For comparisons, keep acquisition, preprocessing and tuning conditions explicit.
Use subject-level summaries and uncertainty appropriate to the study design;
avoid treating correlated slices as independent subjects. Show failures and
relevant subgroups alongside averages, with sample counts and uncertainty.

## Stress tests and interpretation

Choose perturbations relevant to the intended use: noise, motion, calibration
error, sampling changes, scanner shifts or unusual anatomy. Identify which are
simulated and which are observed. Keep test cases separate from tuning data.
Compare against justified, established baselines; neither a learned nor a
classical method is universally superior.

Inspect measurement residuals using the stated forward/noise model. A small
residual cannot resolve ambiguity in unmeasured information or establish that
all reconstructed features are supported by measurements; see Haldar’s
[entrywise ambiguity analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC10299746/)
(*IEEE Transactions on Signal Processing*, 2023;71:1083–1092,
“On Ambiguity in Linear Inverse Problems: Entrywise Bounds on Nearly
Data-Consistent Solutions and Entrywise Condition Numbers”). Record sensitivity to
regularization or learned priors, and whether failures are visible or misleading.

Label evidence as **same-code/data reproduction**, **independent implementation**,
**external-data evaluation**, or a combination. State what actually changed and
which assumptions remain shared. Propose additional tests when needed; do not
present proposed tests as completed validation.

## Attribution in the delivered output

For each substantive method or scientific claim:

1. Find the original methodological or experimental source. Follow references
   from reviews and software documentation; credit later extensions separately.
2. Check authors, title and publication details against the primary record, then
   inspect the relevant passage, equation or experiment. A resolving DOI proves
   neither relevance nor priority. Avoid “first” claims without historical evidence.
3. Cite near the supported statement. Credit software, version and reused code
   separately from the origin of the method; preserve license/attribution notices.
4. Distinguish the paper's reported result, the agent's inference and results
   observed in the current run. If only an abstract is accessible, state that
   limitation; do not invent quotations, page numbers or verification.

For a substantial comparison or manuscript, keep a compact claim–source table:
`claim | primary source | supporting location/evidence | access/verification limits`.
Audit the delivered report for missing original credit, unsupported claims and
sources that merely repeat the claim. An instruction to cite is not evidence
that the agent actually did so correctly.
