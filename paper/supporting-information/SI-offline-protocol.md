# Supporting Information S1: protocol addendum

S7. Evaluation protocol and retained analysis details

This addendum preserves the detailed protocol accompanying Tables S1-S6 in SI-offline-evaluation. It describes the same frozen offline comparison; no model execution, grading, bootstrap or token analysis was rerun. It does not replace or change the existing tables. Hard task identities and scoring materials are not disclosed.

## S7.1 Paired execution and isolation

The two arms compared the same agent without MRFoundry guidance and with MRFoundry 0.14.0 (commit bd49b95). Arms ran concurrently through Codex CLI 0.159.2 and one API gateway, with the same model, nominal medium reasoning setting, tools, inputs, network access and time limit within each pair. Each arm began with an empty Python environment and a separate Julia package depot in its own Linux namespace sandbox. Neither arm could read the other arm, earlier runs or grading files. Web search was disabled; network access was limited to package indexes. The control lacked both MRFoundry skills and their discovery instruction; common host system-skill catalogs were matched across arms. MRFoundry availability was the intervention; the agent decided whether to read the skills.

Nominal medium did not equalize internal reasoning budgets across vendors. A documented pre-run proxy probe found no reasoning for Claude Sonnet 5.5 at medium, reasoning for Claude Opus 5.5 at every tested setting, and more reasoning for Gemini 4 Argon at medium than at none. These probe observations do not establish identical reasoning behavior throughout the evaluation.

Core time caps were 45 min for the two relaxometry/QSM types, three writing/review types and pilot-study design, and 60 min for the other 18 types. Hard caps were 120, 150, 180 and 210 min for three, six, two and four types, respectively. Arms reaching their limit were graded as submitted.

## S7.2 Task construction, release freeze and coverage

Core comprises 24 task types across ten MRI domains. A type defines a problem structure; an instance is one frozen dataset and parameter setting; a trial is one agent attempt. Separate author agents without access to the skills wrote specifications and private graders and generated new data, parameters and wording. Reference solutions plus positive and negative controls were used to check instances before hashing and sealing them.

Guidance development used failures from development tasks without including task content. A separate agent checked release 0.14.0 for task-instance content; the release was frozen before the evaluated Core instances were opened. The evaluation used one sealed instance per Core type, not all 88 variants registered in the public MRI Agent Bench collection. Core still shares problem structure with earlier tasks of its families; the benchmark and guidance share an author, and independent external MRI-expert review is pending.

After the release freeze, a Hard tier was constructed with two validated instances for each of 15 types: 11 multi-stage workflows and four system-design types. Hard materials were not used to revise the frozen release. Ten models from five providers were accessed through one API gateway. Each Core type-model combination was attempted once, giving 24 x 10 = 240 paired trials. Hard coverage differed: three models attempted both instances of all 15 types (90 pairs); four further models attempted one instance of each of the 11 multi-stage types (44 pairs). The 134-pair Hard aggregate combines these unequal cohorts; model results are reported within cohorts in Table S4.

---

## S7.3 Grading and estimands

Graders evaluated submissions independently of agent reports by replaying exported sequences, rerunning code on hidden data, comparing numerical maps with ground truth, recomputing statistics and checking claims against supplied results. Verified completion required every automated check to pass. It measures those fixed checks, not clinical validity, researcher effort or unrestricted research competence. No language-model judge supplied the completion labels.

The paired completion effect is the difference in the proportion passing with versus without MRFoundry. The primary uncertainty summary is the saved 95% percentile interval from resampling task types and models. It describes sensitivity to the selected panel, not a probability sample of MRI tasks or models. Secondary exact two-sided McNemar tests pool discordant pairs, assuming independent discordant-pair signs. They are unadjusted trial-level comparisons conditional on the tested panel, not tests adjusted for task/model clustering. All trials reaching a model turn for the ten analysed models were retained. One attempt per combination does not establish repeated-run reliability. Exploratory domain/model breakdowns do not support a general ranking or multiplicity-corrected subgroup claims.

The original helper independently draws, with replacement, as many task-type labels and model labels as observed. Their Cartesian product repeats each observed cell by the product of its sampled multiplicities. Both arms remain paired through the difference (with minus without); every retained instance in a sampled cell is included together. Missing cells contribute no observations, rather than zeros. Each replicate averages all included paired differences. Thus Core weights task types equally, not domains; Hard retains the observed unequal instance/cohort weighting. The incomplete Hard design is not expanded into common coverage.

For each set, the helper initializes Python random.Random(0), performs 4,000 draws, sorts nonempty replicate means, and takes zero-based indices int(0.025*N) and int(0.975*N)-1. The exact historical Python patch version was not retained in the handoff. The verbatim functions and original-file digest are included in [original_statistics.py](https://github.com/KeWang0622/MRFoundry/blob/main/paper/evidence/evaluation/original_statistics.py) and [statistics-provenance.json](https://github.com/KeWang0622/MRFoundry/blob/main/paper/evidence/evaluation/statistics-provenance.json). The published result importer copies the saved intervals; it does not recompute them.

## Protocol incidents and interpretation

## S7.4 Exclusions, restarts and resource changes

Nine started pairs for an eleventh model were excluded because its API rejected the host's file-editing tool. A runner error caused 143 pair-setup failures before either arm reached a model turn: 94 Core and 49 Hard. These counts refer to paired launch events, not individual model attempts. These were restarted without changing task or model condition. These setup events are distinct from failed agent attempts included in the analysis.

An 8 GiB per-process memory limit was introduced for pairs prepared from approximately 00:45 UTC on 3 November 2026. A missing runner import caused pre-turn setup failures until approximately 02:45 UTC; the affected pair setups were then restarted. Recorded settings matched the limit within newly prepared pairs, but exposure records are incomplete and resources were not uniform across the complete study. One Hard instance allowed a zero-filled reconstruction to pass an image subcheck; that alone does not establish whole-task completion, and the original outcome was retained. These incidents limit interpretation of the paired comparison. The aggregate reports do not identify the private task or expose its scoring material.

One retained Core skill arm encountered recursive temporary-input copying in the finish_check helper, producing 232 GB of temporary data. Its pair completed and was graded before cleanup; the recorded outcome remains unchanged. From approximately 11:55 UTC on 2 November 2026, the runner moved temporary files outside the workspace and added a guard to stop arms exceeding 60 GiB of workspace-plus-temporary storage (called 60 GB in the incident log). This resource policy was introduced during evaluation; no effect on completion is inferred from the incident alone. The local handoff lacks a complete pair-by-policy exposure ledger, active-pair transition record and arm-specific guard-termination counts. Memory-cap settings were documented as matched within pairs; equivalent historical disk-policy exposure cannot be independently established from these records. Shared physical resources also permit interference between concurrent attempts. We therefore do not claim a uniform resource regime or that every affected run can be identified. The accompanying [historical-execution manifest](https://github.com/KeWang0622/MRFoundry/blob/main/paper/evidence/evaluation/HISTORICAL-EXECUTION.md) separates recorded settings from unavailable fields.

## S7.5 Retained outcome detail

Core completion rose from 162/240 to 188/240, with 39 with-only and 13 without-only pairs. Seven MRI domains improved, two were unchanged and diffusion declined (17/20 to 15/20). Sequence design gained 11 completions (34/70 to 45/70); relaxometry/QSM gained six (13/20 to 19/20). Seven models improved in aggregate Core count and three were unchanged. Full denominators and discordant counts remain in Tables S2 and S3.

Hard completion rose from 49/134 to 60/134, with 20 with-only and nine without-only pairs. Its saved 95% interval includes zero. The full-coverage cohort rose from 44/90 to 52/90; the multi-stage-only cohort rose from 5/44 to 8/44. System-design tasks remained largely unsolved (1/24 versus 3/24), as reported in Table S5. These cohorts are not directly rankable, and pooled improvements do not imply success on every domain or task.

The two diffusion regressions account for the domain decline; no pair improved in that subgroup. Saved summaries do not identify the failed subchecks or establish that a particular diffusion instruction caused the failures. No causal explanation is inferred from a score difference alone.

## S7.6 Token accounting and reproducibility

Total reported tokens with MRFoundry divided by total tokens without skills were 1.048 for Core and 1.062 for Hard. Tokens per verified completion divide all reported tokens, including unsuccessful attempts, by verified successes; the corresponding with/without ratios were 0.903 and 0.868. These are saved token-use measures, not monetary cost, latency, energy or uniform billing estimates across providers. The proxy reported zero reasoning tokens for non-OpenAI models even when reasoning items were present; this is an accounting limitation. Table S6 reports the with/without ratios.

Counts, intervals and token measures are copied from the frozen results. The approved figure-5-data.json contains aggregate publication data only. Supporting Information S1 records the SHA-256 digests of offline-summary.json and offline-pairs.json; raw private Hard records are not part of the public manuscript package. The public Core repository provides task specifications, graders and reproducible data packages; the public result snapshot documents the recorded comparison. Availability of guidance did not isolate individual skill effects, later memory reuse, community contributions or alternative host performance.

Sources: [MRFoundry](https://github.com/KeWang0622/MRFoundry), [MRI Agent Bench Core](https://github.com/KeWang0622/MRIAgentBench), and the frozen result/provenance records identified in SI-offline-evaluation. Protocol details are retained from the original study supplement, runner documentation and contemporaneous incident log.
