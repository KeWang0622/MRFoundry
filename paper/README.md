# MRFoundry paper

**MRFoundry: Knowledge-Guided Agent Loops for End-to-End MRI Research**

**WORKING DRAFT — 4 November 2026.** This author-side manuscript is not submitted or accepted. It introduces the MRFoundry toolbox, illustrates supervised MRI workflows, and reports a bounded comparison using [MRI Agent Bench](https://github.com/KeWang0622/MRIAgentBench).

- **[Read the manuscript](manuscript.pdf)** — 13 pages in the supplied MRM template, including figures, tables and references; 3,491 body words and a 174-word abstract.
- **Supporting Information:** [MRI demonstration evidence](supporting-information/SI-workflow-evidence.pdf), [offline comparison tables](supporting-information/SI-offline-evaluation.pdf), and [evaluation protocol](supporting-information/SI-offline-protocol.pdf).
- **[Download the portable source ZIP](MRFoundry-paper-source.zip)** — 68.9 MB; manuscript sources, editable figures, Supporting Information, and retained evidence.
- **[Package-verification receipt](package-verification.json)** — exact hashes and completed document/figure rebuild checks.

This revision improves the manuscript narrative and headings: Methods retains five subsections, and Results presents sequence checks, reconstruction comparison, the retained research lesson and the benchmark comparison as four direct subsections. Figure visuals, numerical result cells and original evidence are unchanged. Exact technical clarifications acknowledge helper scripts, distinguish host tools from frozen skill packages, update five current source-reference pins, correct caption and speaker-note wording, and identify the S0 value used for signal prediction. Only the workflow-evidence supplement and its receipt entry are rebuilt; the other two SI PDFs are unchanged. Two editorial and three technical author-side AI reviews closed the final manuscript. They do not represent human peer review or journal approval.

The [evidence archive](evidence/README.md) preserves original demonstration scripts, reports and input identities. The [historical evaluation record](evidence/evaluation/HISTORICAL-EXECUTION.md) documents retained settings and unavailable records; [input sources and licenses](evidence/INPUTS-AND-LICENSES.md) identify public datasets without duplicating full raw acquisitions. Private Hard tasks, scoring materials and per-task traces are excluded.

## Rebuild the paper

Extract the ZIP, install the dependencies in its `build/README.md` and `SOURCE-PACKAGE.md` (Python 3.9+, Tectonic and the listed support packages), then run inside `MRFoundry-paper/`:

```bash
bash build/build.sh --output-dir "$PWD" --figure-root "$PWD"
```

A fresh-extraction document build and all five figure rebuilds passed. This assembles saved text, tables and figures; it does not rerun agent trials, MRI experiments, grading or statistical resampling. Original scientific scripts retain historical workspace dependencies and have not been validated as portable scientific reproductions. Numerical outcomes are unchanged.

Author-generated code and documentation use the repository's [MIT license](../LICENSE); upstream software, templates and data retain their own terms.
