# Methods or statistics review of a manuscript

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`. Common rules: the workflow SKILL.md.

1. Work through the manuscript section by section, tables included, and record each problem under the ID of the
   paragraph or table that holds the faulty statement. Problems to look for:
   - independence: several measurements of one participant (voxels, slices, lesions, repeat scans) analysed as if
     they came from different participants;
   - data separation: the evaluation data shaped training, tuning, or the choice of model or cut-off, or the same
     participants appear in more than one split;
   - multiplicity: many tests without correction, and conclusions resting on the few with p < 0.05;
   - arithmetic: participant flow, sums, percentages and means that disagree between text and tables (recompute
     them in code);
   - units and magnitudes: a value or unit that is physically implausible for the quantity measured;
   - analysis choice: a test that ignores the design (pairing, repeated measures, clustering, small skewed samples);
   - exclusions: data removed by a rule chosen after the results were seen, or by no stated rule;
   - double dipping: a region, feature or threshold chosen with the outcome data it is later tested against;
   - assessment: readers aware of the method or the reference result; accuracy without a reference standard;
   - confounding or selection that the analysis leaves unaddressed;
   - conclusions about cause, diagnosis or practice that the design and endpoints cannot carry.
2. Raise a point only when it changes a result, a number, a unit, the validity of an analysis or the strength of a
   conclusion. Skip style and the limitations the authors already state.
3. Copy each quote by code as one unbroken passage of its paragraph's text: no "...", no paraphrase.
4. Run, fix every FAIL, run again:

       WC --quotes <review json> --source <paragraph json or manuscript md> [--min-quote <task minimum>] \
          --mentions <review json>=<review md> --words <review md>:<limit>

