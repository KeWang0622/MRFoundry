"""Tests for write_check.py on small synthetic fixtures (python test_write_check.py; standard library only)."""
import contextlib, io, json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_check as wc


def run(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = wc.main(list(args))
    return code, buf.getvalue()


def write(d, name, content):
    p = Path(d) / name
    p.write_text(content if isinstance(content, str) else json.dumps(content, indent=1))
    return str(p)


def test_results_writeup(d):
    src = write(d, "results.json", {"entries": [
        {"id": "E01", "estimate": -3.2, "ci": [-5.0, -1.4], "p": "<0.001", "n": 120},
        {"id": "E02", "estimate_pa": -80.0, "ci_pa": [-210.0, 50.0], "p_holm": 0.42, "n": 118},
        {"id": "E03", "estimate": -4.1, "ci": [-6.3, -1.9], "n": 41, "subgroup": "with condition"}]})
    bib = write(d, "refs.bib", "@article{smith2020,\n title={A}\n}\n@book{lee2019, title={B}}\n")
    claims = {"claims": [
        {"claim_id": "C1", "source_id": "E01", "estimate": -3.2, "unit": "percentage_points", "ci_lower": -5.0, "ci_upper": -1.4,
         "p_value": "<0.001", "n": 120, "interpretation": "effect_detected", "locations": ["abstract", "results"]},
        {"claim_id": "C2", "source_id": "E02", "estimate": -0.08, "unit": "kPa", "ci_lower": -0.21, "ci_upper": 0.05,
         "p_value": 0.42, "n": 118, "interpretation": "no_effect_detected", "locations": ["results"]},
        {"claim_id": "C3", "source_id": "E03", "estimate": -4.1, "unit": "percentage_points", "ci_lower": -6.3, "ci_upper": -1.9,
         "n": 41, "interpretation": "exploratory", "locations": ["results"]}]}
    cl = write(d, "claims.json", claims)
    ab = write(d, "abstract.md", "# Abstract\nThe primary endpoint differed by -3.2 percentage points (95% CI -5.0 to -1.4; p < 0.001; n = 120) [@smith2020].\n")
    good = ("The primary endpoint differed by -3.2 percentage points (95% CI -5.0 to -1.4, p < 0.001, n = 120).\n"
            "Stiffness did not differ between groups: -0.08 kPa (95% CI -0.21 to 0.05, Holm-adjusted p = 0.42, n = 118).\n"
            "In an exploratory subgroup analysis, the difference was -4.1 percentage points (95% CI -6.3 to -1.9, n = 41) [@lee2019].\n")
    rs = write(d, "results.md", good)
    base = ["--words", ab + ":250", "--texts", ab, rs, "--bib", bib, "--claims", cl, "--loc", "abstract=" + ab,
            "--loc", "results=" + rs, "--trace", src, "--scale", "0.001"]
    code, out = run(*base)
    assert code == 0, out
    # semicolon splits the clause: the second clause reports n without the label
    write(d, "results.md", good.replace("(95% CI -6.3 to -1.9, n = 41)", "(95% CI -6.3 to -1.9; n = 41)")
          .replace("In an exploratory subgroup analysis, the", "The"))
    code, out = run(*base)
    assert code == 1 and "exploratory estimate without" in out, out
    # CI includes zero but the sentence has no no-difference phrase
    write(d, "results.md", good.replace("Stiffness did not differ between groups:", "Stiffness was"))
    code, out = run(*base)
    assert code == 1 and "CI includes 0" in out, out
    # percentage points written as %, a missing n, a new statistic, an unknown key and a DOI
    write(d, "results.md", good.replace("-3.2 percentage points", "-3.2%").replace(", n = 118", "")
          .replace("[@lee2019]", "[@doe2021] (doi:10.1000/xyz), a 12.5% relative reduction"))
    code, out = run(*base)
    for frag in ("not '%'", "C2.n=118 not in results", "doe2021", "DOI", "numbers not found in the sources"):
        assert frag in out, (frag, out)
    # less precise text than ledger
    write(d, "results.md", good.replace("-0.08 kPa", "-0.1 kPa"))
    code, out = run(*base)
    assert "fewer decimals" in out or "not in results" in out, out
    # language rules from a task file
    task = write(d, "task.json", {"trend_words": ["trend", "tended"], "labels": ["exploratory", "post hoc"]})
    write(d, "results.md", good + "Stiffness tended to be lower.\n")
    code, out = run("--texts", rs, "--forbid-in", "stiffness::@" + task + ":trend_words",
                    "--require-in", "subgroup::@" + task + ":labels")
    assert code == 1 and "'tended' not allowed" in out, out
    code, out = run("--words", rs + ":20")
    assert code == 1 and "FAIL words" in out
    print("write_check: claims, null phrases, exploratory clauses, pp units, citations, trace, word limits ok")


def test_review(d):
    paras = write(d, "paragraphs.json", {"paragraphs": [
        {"id": "P01", "text": "We scanned 40 patients (age 61 \u00b1 8 years) and analysed 12,000 voxels with a t-test."},
        {"id": "P02", "text": "Because image quality improved, the method will reduce biopsies in routine practice."},
        {"id": "T1", "text": "| Group | ADC (mm\u00b2/s) |\n| A | 1.2 |"}]})
    issues = {"recommendation": "major_revision", "issues": [
        {"issue_id": "I1", "paragraph_id": "P01", "category": "statistical_unit_pseudoreplication", "quote": "analysed 12,000 voxels with a t-test"},
        {"issue_id": "I2", "paragraph_id": "P02", "category": "unsupported_causal_or_clinical_claim", "quote": "the method will reduce biopsies in routine practice"}]}
    rv = write(d, "review.json", issues)
    md = write(d, "review.md", "Major revision. P01: voxels as units. P02: clinical claim.\n")
    code, out = run("--quotes", rv, "--source", paras, "--mentions", rv + "=" + md, "--words", md + ":2000")
    assert code == 0, out
    issues["issues"][1]["quote"] = "Because image quality improved ... routine practice"
    issues["issues"].append({"issue_id": "I3", "paragraph_id": "P02", "quote": "analysed 12,000 voxels"})
    issues["issues"].append({"issue_id": "I4", "paragraph_id": "T1", "quote": "Group | ADC (mm2/s)"})
    write(d, "review.json", issues)
    code, out = run("--quotes", rv, "--source", paras, "--mentions", rv + "=" + md)
    assert code == 1 and "ellipsis" in out and "found in P01" in out and "T1" in out, out
    print("write_check: verbatim quotes, ellipsis, wrong paragraph, unicode, mentions ok")


def test_ids_and_schema(d):
    corpus = write(d, "corpus.json", {"records": [{"id": "R01", "n": 20}, {"id": "R02", "n": 31}, {"id": "R10", "n": 12}]})
    md = write(d, "proposal.md", "BOLD R2* rose [R01; R02]. The gap [R10] remains; see R99.\n")
    code, out = run("--texts", md, "--ids", corpus)
    assert code == 1 and "R99" in out and "'R2'" not in out, out
    task = write(d, "task.json", {
        "design_vocabulary": {"type": ["cross_sectional", "cohort"], "recruitment": ["consecutive", "convenience"]},
        "factor_vocabulary": ["field_strength", "vendor"],
        "codes_vocabulary": {"blinded": "blinded reading", "hydration": "standard hydration"},
        "schema": {"design": "{type, recruitment (values from design_vocabulary), description: string}",
                   "audit": "list of {record_ids: [..], factor: one value of factor_vocabulary, note: string (optional)}",
                   "controls": "list of {code (from codes_vocabulary), record_ids: [..]}",
                   "sample_size": "{n_per_group (integer), sd, sources: [..]}",
                   "risks": "list of at least two {risk, mitigation}"}})
    good = {"design": {"type": "cohort", "recruitment": "consecutive", "description": "x"},
            "audit": [{"record_ids": ["R01"], "factor": "vendor"}],
            "controls": [{"code": "blinded", "record_ids": []}],
            "sample_size": {"n_per_group": 23, "sd": 86.0, "sources": ["R02"]},
            "risks": [{"risk": "a", "mitigation": "b"}, {"risk": "c", "mitigation": "d"}]}
    out_f = write(d, "out.json", good)
    code, out = run("--schema", task + ":schema=" + out_f)
    assert code == 0, out
    bad = json.loads(json.dumps(good))
    bad["design"]["recruitment"] = ["consecutive"]; bad["audit"][0]["factor"] = "sample size"
    bad["controls"][0]["code"] = "blinding"; bad["sample_size"]["n_per_group"] = 22.4; del bad["sample_size"]["sd"]
    bad["risks"] = bad["risks"][:1]
    write(d, "out.json", bad)
    code, out = run("--schema", task + ":schema=" + out_f)
    for frag in ("single value", "'sample size' not in vocabulary", "'blinding' not in vocabulary", "integer expected",
                 "sample_size.sd: missing", "at least 2 items"):
        assert frag in out, (frag, out)
    plan = write(d, "plan.md", "We will enrol 46 participants (42 evaluable).\n")
    design = write(d, "design.json", {"a": {"n_enrol": 46, "n_evaluable": 42}, "b": {"n_enrol": 60}})
    code, out = run("--numbers-in", plan + "=" + design + ":a.n_enrol,a.n_evaluable,b.n_enrol")
    assert code == 1 and "b.n_enrol=60" in out, out
    print("write_check: record IDs, prose schema (keys, lists, integers, vocabularies), JSON numbers in text ok")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        test_results_writeup(d)
    with tempfile.TemporaryDirectory() as d:
        test_review(d)
    with tempfile.TemporaryDirectory() as d:
        test_ids_and_schema(d)

