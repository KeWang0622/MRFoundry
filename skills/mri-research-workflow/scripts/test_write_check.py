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
    # a fictional imaging trial: primary endpoint in percentage points, a secondary endpoint recorded in seconds and
    # reported in ms, and a post hoc age subgroup; the ledger uses its own key names
    src = write(d, "trial_numbers.json", {"rows": [
        {"key": "Q1", "est": -6.4, "lo": -9.8, "hi": -3.0, "p": "<0.001", "n": 88},
        {"key": "Q2", "est_s": -0.0048, "ci_s": [-0.0099, 0.0003], "p_bonf": 0.19, "n": 85},
        {"key": "Q3", "est": -7.9, "lo": -13.1, "hi": -2.7, "n": 29, "group": "age over 65"}]})
    bib = write(d, "fixture.bib", "@article{kim2018,\n title={A}\n}\n@book{roe2017, title={B}}\n")
    ledger = {"items": [
        {"id": "L1", "entry": "Q1", "value": -6.4, "unit": "pp", "ci": [-9.8, -3.0], "p": "<0.001", "n": 88,
         "conclusion": "difference", "where": ["summary", "body"]},
        {"id": "L2", "entry": "Q2", "value": -4.8, "unit": "ms", "conf_low": -9.9, "conf_high": 0.3, "p": 0.19, "n": 85,
         "conclusion": "null", "where": ["body"]},
        {"id": "L3", "entry": "Q3", "value": -7.9, "unit": "percentage points", "ci": [-13.1, -2.7], "n": 29,
         "conclusion": "exploratory", "where": ["body"]}]}
    led = write(d, "ledger.json", ledger)
    sm = write(d, "summary.md", "# Summary\nThe artefact rate differed by -6.4 percentage points (95% CI -9.8 to -3.0; p < 0.001; n = 88) [@kim2018].\n")
    good = ("The artefact rate differed by -6.4 percentage points (95% CI -9.8 to -3.0, p < 0.001, n = 88).\n"
            "Lesion T2 did not differ between arms: -4.8 ms (95% CI -9.9 to 0.3, Bonferroni-adjusted p = 0.19, n = 85).\n"
            "In a post hoc analysis of participants older than 65 years, the difference was -7.9 percentage points (95% CI -13.1 to -2.7, n = 29) [@roe2017].\n")
    bd = write(d, "body.md", good)
    base = ["--words", sm + ":300", "--texts", sm, bd, "--bib", bib, "--claims", led, "--loc", "summary=" + sm,
            "--loc", "body=" + bd, "--trace", src, "--scale", "1000"]
    code, out = run(*base)
    assert code == 0, out
    # a semicolon starts a new clause: the clause with n has no label, and the label sentence is gone
    write(d, "body.md", good.replace("(95% CI -13.1 to -2.7, n = 29)", "(95% CI -13.1 to -2.7; n = 29)")
          .replace("In a post hoc analysis of participants older than 65 years, the", "In participants older than 65 years, the"))
    code, out = run(*base)
    assert code == 1 and "exploratory estimate without" in out, out
    # CI includes zero but the sentence has no no-difference phrase
    write(d, "body.md", good.replace("Lesion T2 did not differ between arms:", "Lesion T2 was"))
    code, out = run(*base)
    assert code == 1 and "CI includes 0" in out, out
    # percentage points written as %, a missing n, a new statistic, an unknown key and a DOI
    write(d, "body.md", good.replace("-6.4 percentage points", "-6.4%").replace(", n = 85", "")
          .replace("[@roe2017]", "[@poe2016] (doi:10.1000/xyz), a 14.2% relative reduction"))
    code, out = run(*base)
    for frag in ("not '%'", "L2.n=85 not in body", "poe2016", "DOI", "numbers not found in the sources"):
        assert frag in out, (frag, out)
    # less precise text than ledger
    write(d, "body.md", good.replace("-4.8 ms", "-5 ms"))
    code, out = run(*base)
    assert "fewer decimals" in out or "not in body" in out, out
    # interpretation that contradicts the CI
    bad = json.loads(json.dumps(ledger)); bad["items"][1]["conclusion"] = "difference"
    write(d, "ledger.json", bad); write(d, "body.md", good)
    code, out = run(*base)
    assert code == 1 and "interpretation reads as an effect" in out, out
    write(d, "ledger.json", ledger)
    # language rules from a task file
    spec = write(d, "spec.json", {"hedge_terms": ["suggestive", "somewhat"], "labels": ["exploratory", "post hoc"]})
    write(d, "body.md", good + "Lesion T2 was somewhat lower.\n")
    code, out = run("--texts", bd, "--forbid-in", "lesion t2::@" + spec + ":hedge_terms",
                    "--require-in", "older than::@" + spec + ":labels")
    assert code == 1 and "'somewhat' not allowed" in out, out
    code, out = run("--words", bd + ":20")
    assert code == 1 and "FAIL words" in out
    print("write_check: claims (own key names), null phrases, exploratory clauses, pp units, citations, trace, word limits ok")


def test_review(d):
    secs = write(d, "sections.json", {"sections": [
        {"id": "S01", "text": "We enrolled 52 participants (age 58 \u00b1 9 years) and compared 9,400 voxels with a t-test."},
        {"id": "S02", "text": "Since the images appeared sharper, the protocol should replace the routine examination everywhere."},
        {"id": "TB1", "text": "| Arm | ADC (mm\u00b2/s) |\n| A | 1.1 |"}]})
    notes = {"verdict": "revise", "problems": [
        {"location": "S01", "kind": "unit_of_analysis", "quote": "compared 9,400 voxels with a t-test"},
        {"location": "S02", "kind": "overreach", "quote": "the protocol should replace the routine examination everywhere"}]}
    rv = write(d, "notes.json", notes)
    md = write(d, "notes.md", "Revise. S01: voxels as units. S02: claim beyond the data.\n")
    code, out = run("--quotes", rv, "--source", secs, "--mentions", rv + "=" + md, "--words", md + ":1800")
    assert code == 0, out
    code, out = run("--quotes", rv, "--source", secs, "--min-quote", "40")
    assert code == 1 and "shorter than 40" in out, out
    notes["problems"][1]["quote"] = "Since the images appeared sharper ... everywhere"
    notes["problems"].append({"location": "S02", "quote": "compared 9,400 voxels"})
    notes["problems"].append({"location": "TB1", "quote": "Arm | ADC (mm2/s)"})
    write(d, "notes.json", notes)
    code, out = run("--quotes", rv, "--source", secs, "--mentions", rv + "=" + md)
    assert code == 1 and "ellipsis" in out and "found in S01" in out and "TB1" in out, out
    print("write_check: verbatim quotes, minimum length, ellipsis, wrong paragraph, unicode, mentions ok")


def test_ids_and_schema(d):
    recs = write(d, "records.json", {"records": [{"id": "R101", "n": 20}, {"id": "R102", "n": 31}, {"id": "R110", "n": 12}]})
    md = write(d, "draft.md", "Mean R2* increased [R101; R102]. The open question [R110] remains; see R188.\n")
    code, out = run("--texts", md, "--ids", recs)
    assert code == 1 and "R188" in out and "'R2'" not in out, out
    spec = write(d, "spec.json", {
        "allowed": {"arm": ["single_site", "multi_site"], "sampling": ["random", "sequential"]},
        "factor_options": ["coil_type", "readout"],
        "action_options": {"masked": "masked scoring", "fasting": "overnight fasting"},
        "layout": {"plan": "{arm, sampling (values from allowed), summary: string}",
                   "factors": "list of {ids: [..], factor: one value of factor_options, comment: string (optional)}",
                   "actions": "list of {code (from action_options), ids: [..]}",
                   "power": "{n_each (integer), spread, refs: [..]}",
                   "hazards": "list of at least three {hazard, response}"}})
    good = {"plan": {"arm": "multi_site", "sampling": "sequential", "summary": "x"},
            "factors": [{"ids": ["R101"], "factor": "readout"}],
            "actions": [{"code": "masked", "ids": []}],
            "power": {"n_each": 21, "spread": 37.0, "refs": ["R102"]},
            "hazards": [{"hazard": "a", "response": "b"}, {"hazard": "c", "response": "d"}, {"hazard": "e", "response": "f"}]}
    out_f = write(d, "answer.json", good)
    code, out = run("--schema", spec + ":layout=" + out_f)
    assert code == 0, out
    bad = json.loads(json.dumps(good))
    bad["plan"]["sampling"] = ["sequential"]; bad["factors"][0]["factor"] = "sample size"
    bad["actions"][0]["code"] = "masking"; bad["power"]["n_each"] = 20.4; del bad["power"]["spread"]
    bad["hazards"] = bad["hazards"][:2]
    write(d, "answer.json", bad)
    code, out = run("--schema", spec + ":layout=" + out_f)
    for frag in ("single value", "'sample size' not in vocabulary", "'masking' not in vocabulary", "integer expected",
                 "power.spread: missing", "at least 3 items"):
        assert frag in out, (frag, out)
    outline = write(d, "outline.md", "We will recruit 113 people (102 analysable).\n")
    nums = write(d, "numbers.json", {"a": {"recruit": 113, "analysable": 102}, "b": {"recruit": 125}})
    code, out = run("--numbers-in", outline + "=" + nums + ":a.recruit,a.analysable,b.recruit")
    assert code == 1 and "b.recruit=125" in out, out
    print("write_check: record IDs, prose schema (keys, lists, integers, named value lists), JSON numbers in text ok")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        test_results_writeup(d)
    with tempfile.TemporaryDirectory() as d:
        test_review(d)
    with tempfile.TemporaryDirectory() as d:
        test_ids_and_schema(d)

