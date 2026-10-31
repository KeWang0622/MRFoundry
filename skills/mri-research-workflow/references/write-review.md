# Methods or statistics review of a manuscript

`WC` = `python .agents/skills/mri-research-workflow/scripts/write_check.py`. Common rules: the workflow SKILL.md.

1. Read every paragraph and table in order and test each against this list; file each problem under the ID of
   the paragraph or table that contains the flawed statement:
   - statistical unit: voxels, slices, lesions or repeated scans counted as independent subjects;
   - leakage: test data used for training, tuning, model or threshold selection; subjects shared across splits;
   - many tests without correction, with conclusions drawn from the nominally significant ones;
   - numbers: recompute sums, percentages, participant flow and means in code; compare text with tables;
   - units: every quantity has a physically plausible value and unit for what it measures;
   - test versus design (unpaired test on paired data, repeated measures, tiny non-normal samples);
   - exclusions decided after seeing outputs, or without a prespecified objective rule;
   - circularity: regions, features or thresholds chosen on the same data and outcome that are then tested;
   - unblinded readers where knowledge could bias them; accuracy claims without a reference standard;
   - causal, diagnostic or practice-changing conclusions beyond the design and endpoints.
2. Report only problems that invalidate a result, misstate a number or unit, use an unsuitable analysis or
   overstate a conclusion. Leave sound paragraphs and acknowledged generic limitations alone.
3. Quote ONE contiguous passage copied by code from that paragraph's text: no "...", no paraphrase.
4. Run, fix every FAIL, run again:

       WC --quotes review.json --source <paragraphs json or manuscript md> --mentions review.json=review.md \
          --words review.md:<limit>

