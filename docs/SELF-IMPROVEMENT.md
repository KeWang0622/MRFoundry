# From research experience to better skills

MRFoundry connects two activities: using an agent to investigate an MRI question, and using evidence from that investigation to improve how future work is done. Here, **recursive self-improvement (RSI)** means researcher-guided changes to project knowledge and shared agent instructions. The next research cycle can test those changes and produce further lessons.

The package provides memory templates, instructions and scientific helpers. The researcher and agent carry out the loop; there is no background service that automatically collects experiments, rewrites skills or trains model weights.

This loop can support a broader [scientific-discovery agenda](AI-FOR-SCIENCE.md): use better guidance to formulate and test new MRI ideas. A guidance improvement and a scientific discovery are separate outcomes. The first needs evidence of better research behavior; the second needs a contribution assessed against prior work and independently validated.

## Keep local experience useful

Use the [project-memory guide](../skills/mri-research/references/project-memory.md) to initialize a private `.mrfoundry/` notebook. The initializer preserves existing notes and excludes the notebook from Git by default.

1. **Retrieve.** Read the project index and relevant lessons before choosing an approach. Check whether the data, software and assumptions still match.
2. **Investigate.** State the question and checks, run established tools, and retain the commands, versions, artifacts and unsuccessful attempts.
3. **Record a lesson.** Describe the observation, supporting evidence, scope and conditions that would require revalidation. Separate observed findings, verified findings and hypotheses.
4. **Use it again.** Let the lesson change a concrete decision in a later task. Record whether it helped, needed narrowing or was contradicted; preserve the earlier record.

User preferences belong in their own file. A preferred plotting style is not a scientific finding; a result from one sequence or dataset is not a universal rule.

## Example: measure the sequence that was exported

The following illustrates an improvement workflow using existing repository helpers and regression fixtures. It is not a reported end-to-end RSI experiment.

| Step | EPI timing example |
|---|---|
| **Research question** | Does the exported EPI sequence implement the requested echo time? |
| **Experiment** | Build and export the sequence, then read back the `.seq` artifact. |
| **Evidence** | Measure TE from the excitation center to the kx = ky = 0 sample. A delay rounded to the block raster can miss a tighter timing tolerance. |
| **Local lesson** | Check realized timing in the exported file. Account for the RF center, the ADC sample at k-space center, and raster constraints when assigning delays. |
| **Reusable change** | Pair a concise instruction with a regression fixture that detects the timing error and a corrected example. |
| **Further check** | Recheck the requested timing and sampling constraints after changing TE, matrix size or field of view; document the tested scope. |

The [sequence skill](../skills/pulse-sequence-design/SKILL.md#rules-the-checker-enforces) explains the timing rule. The [export checker](../skills/pulse-sequence-design/scripts/check_exported_seq.py) measures the artifact. The [regression examples](../skills/pulse-sequence-design/scripts/test_check_exported_seq.py) include both a raster-rounded EPI delay that fails the stated tolerance and a corrected construction using `split_interval` and `center_shift`.

This pattern also applies to data conventions, reconstruction controls and analysis assumptions: identify the decision that caused a problem, attach evidence, and test a correction that can be reused.

## Turn a local lesson into a contribution

Share the smallest useful change, with enough context to assess it:

- **Trigger:** the task or observation that exposed a missing instruction, incorrect assumption or unreliable step.
- **Change:** the proposed instruction, reference or helper correction, and when it should apply.
- **Evidence:** a minimal shareable example, commands and output checks; include unsuccessful attempts and known exceptions that affect the conclusion.
- **Validation:** behavior before and after the change, plus a new case when claiming reuse beyond the original example.

An agent can help draft the patch and explanation. A maintainer reviews the evidence and scope before merging; other users then update their installed skills. Review the proposed patch for project-specific data and credentials rather than copying a private notebook into the repository.

Use the [contribution guide](../CONTRIBUTING.md) and PR template. Repository CI checks structure, memory preservation, shell scripts, links, upstream availability and skill discovery. Scientific changes also need the relevant task-specific checks; a green CI run alone does not establish scientific validity.

## Evaluating an improvement

For a proposed skill revision, compare the previous and revised guidance with the same model, inputs, tools and execution budget. Define the success checks first and record all attempts, including regressions. When execution is stochastic, repeat trials and report the variation. Keep development examples separate from cases used to assess generalization.

To study memory reuse, compare subsequent tasks with and without access to prior lessons while holding the skill revision fixed. Keep the task order and information available at each stage explicit. This separates the benefit of project memory from a change to the shared package.

[MRI Agent Bench](https://github.com/KeWang0622/MRIAgentBench) provides MRI tasks and a with/without-MRFoundry comparison. Those results evaluate the package; they do not establish gains from repeated memory reuse or successive skill revisions.

## Try it in your project

> Use MRFoundry to investigate this MRI question. Start by checking the project memory and defining the outputs we should inspect. Record the commands, evidence and unsuccessful attempts. After reviewing the result with me, propose one scoped lesson for the next task. If it could help other researchers, draft a small skill change with a reproducible check for maintainer review.
