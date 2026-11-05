# MRFoundry paper

**MRFoundry: Knowledge-Guided Agent Loops for End-to-End MRI Research**

Ke Wang · Atakan Topcu · Hossein Momeni · Molin Zhang

Ke Wang and Molin Zhang: Independent Researcher. Atakan Topcu and Hossein Momeni: Department of Electrical Engineering and Computer Sciences, University of California, Berkeley. Ke Wang remains the corresponding author.

**WORKING DRAFT — 4 November 2026.** This author-side manuscript is not submitted or accepted. It introduces the MRFoundry toolbox, illustrates supervised MRI workflows, and reports a bounded comparison using [MRI Agent Bench](https://github.com/KeWang0622/MRIAgentBench).

- **[Read the manuscript](manuscript.pdf)** — 13 pages in the supplied MRM template, including figures, tables and references; 3,491 body words and a 174-word abstract.
- **Supporting Information:** [MRI demonstration evidence](supporting-information/SI-workflow-evidence.pdf), [offline comparison tables](supporting-information/SI-offline-evaluation.pdf), and [evaluation protocol](supporting-information/SI-offline-protocol.pdf).
- **[Download the portable source ZIP](MRFoundry-paper-source.zip)** — 73.3 MB; manuscript sources, editable figures, Supporting Information, and retained evidence.
- **[Package-verification receipt](package-verification.json)** — exact hashes and completed document/figure rebuild checks.

Figure 3 now connects a framed Researcher source to the KomaMRI check panel and separates the outgoing artifact connection. The corrected manuscript, editable PowerPoint and publication exports are included together in the source ZIP. Manuscript prose, scientific-panel content, numerical results, tables, references, Supporting Information and all other figures remain unchanged.

The package preserves the earlier editorial and technical author-side AI reviews as historical records. Separate amendment receipts bind the earlier connector correction and the current author update with their scoped checks; these checks do not represent human peer review or journal approval.

The [evidence archive](evidence/README.md) preserves original demonstration scripts, reports and input identities. The [historical evaluation record](evidence/evaluation/HISTORICAL-EXECUTION.md) documents retained settings and unavailable records; [input sources and licenses](evidence/INPUTS-AND-LICENSES.md) identify public datasets without duplicating full raw acquisitions. Private Hard tasks, scoring materials and per-task traces are excluded.

## Rebuild the paper

Extract the ZIP, install the dependencies in its `build/README.md` and `SOURCE-PACKAGE.md` (Python 3.9+, Tectonic and the listed support packages), then run inside `MRFoundry-paper/`:

```bash
bash build/build.sh --output-dir "$PWD" --figure-root "$PWD"
```

The current source archive passes 545 integrity and author-amendment checks. A fresh manuscript build passes 299 further checks, including identical rendered pages. Scientific manuscript content and all figure bytes remain unchanged by the author update. Earlier Figure 3 and five-figure rebuild checks are retained as history for the unchanged inputs. These operations assemble saved text, tables and figures; they do not rerun agent trials, MRI experiments, grading or statistical resampling. Original scientific scripts retain historical workspace dependencies and have not been validated as portable scientific reproductions. Numerical outcomes are unchanged.

Author-generated code and documentation use the repository's [MIT license](../LICENSE); upstream software, templates and data retain their own terms.
