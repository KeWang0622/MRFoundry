#!/usr/bin/env python3
"""Writing check: run before finishing any write-up, proposal, review or plan (standard library only).

Each flag adds one family of checks; every check prints PASS, FAIL or WARN and the exit code is 1 if any
check FAILs. Run it, fix every FAIL in the files (not in the checker), and run it again.

  --words FILE:MAX[:nohead]   word limit: every whitespace token counts (add :nohead to skip '#' lines)
  --texts FILE ...            prose files (.md/.txt) and JSON outputs checked by --bib, --ids and the rules
  --bib refs.bib              every citation key in --texts ([@key], @key, \cite{key}) must be in the .bib;
                              DOIs, URLs, PMIDs, arXiv IDs, 'et al.' and author-year citations FAIL
  --ids SOURCE.json           every record ID cited in --texts ([R04], "R04" in JSON) must exist in SOURCE
  --quotes REVIEW.json --source PARAGRAPHS.json|.md
                              each issue's quote must be ONE contiguous verbatim passage of the paragraph or
                              table it is filed under (case and whitespace are ignored; no ellipsis)
  --mentions REVIEW.json=REVIEW.md
                              every paragraph/table ID used in REVIEW.json is mentioned in REVIEW.md
  --claims CLAIMS.json --loc NAME=FILE ...
                              claim ledger against the texts: every number of a claim appears in each text
                              its 'locations' list names; a 95% CI that includes 0 needs a no-difference
                              phrase in the sentence with the estimate and interpretation no_effect_detected;
                              exploratory claims need 'exploratory' or 'post hoc' in the same sentence;
                              percentage-point claims must not be written with '%'
  --null-phrases LIST         comma list or @task.json:key (default: common no-difference phrases)
  --require-in TRIG::WORDS    every sentence of --texts/--loc files containing a trigger contains one of
                              WORDS (comma lists, or @task.json:key). TRIG '*' = every sentence
  --forbid-in TRIG::WORDS     no sentence containing a trigger contains any of WORDS
  --trace SOURCE.json         every number in the prose files must come from SOURCE (any number in it),
                              optionally times --scale factors (unit conversions), at the printed precision
  --allow N ...               numbers always allowed by --trace (default 95 for '95% CI')
  --numbers-in TEXT=JSON:path,path
                              the numbers at these JSON paths (a.b.0.c, '*' for every list item) appear in TEXT
  --schema TASK.json:KEY=OUT.json
                              keys, lists, integers and vocabulary values of OUT.json against a prose schema in
                              TASK.json[KEY] (strings like "{a, b: [..], c (integer)}" or "list of {..}")

Sentences are split at . ! ? ; and line breaks, and every table row is its own sentence: a label such as
'exploratory' must be repeated in every clause that reports a labelled estimate.
Example (results write-up):
  python write_check.py --words abstract.md:250 --texts abstract.md results.md --bib refs.bib \
      --claims claims.json --loc abstract=abstract.md --loc results=results.md --trace inputs/results.json
"""
import argparse, json, re, sys
from pathlib import Path

NULL_PHRASES = ["no significant", "not significant", "not statistically significant", "did not differ",
                "no evidence", "no detectable", "not detected", "no difference", "inconclusive",
                "did not reach statistical significance", "not different", "no statistically significant",
                "no clear difference", "was not detected"]
EXPLORATORY = ["exploratory", "post hoc", "post-hoc"]
EXTERNAL = [(r"\bdoi\s*:|doi\.org|\b10\.\d{4,9}/\S+", "DOI"), (r"https?://|www\.", "URL"), (r"\bPMID\b", "PMID"),
            (r"arXiv\s*:?\s*\d", "arXiv ID"), (r"\bet al\b", "'et al.'"),
            (r"\((?!(?:January|February|March|April|May|June|July|August|September|October|November|December)\b)"
             r"([A-Z][A-Za-z'\-]+(\s+(and|&)\s+[A-Z][A-Za-z'\-]+)?),?\s+(19|20)\d\d[a-z]?\)", "author-year citation")]
NUM_RE = re.compile(r"(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?(?:[eE][-+]?\d+)?")
OUT = []


def say(level, msg):
    OUT.append((level, msg)); print(f"{level} {msg}")


def norm_text(s):
    return (s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", " - ").replace("\u00a0", " ")
             .replace("\u2009", " ").replace("\u202f", " "))


def numbers(text):
    """(value, decimals, raw) for every number in text; thousands separators and unicode minus handled."""
    out = []
    for m in NUM_RE.finditer(norm_text(text)):
        raw = m.group(0)
        if not raw or raw in ("-", ".", "-.") or not re.search(r"\d", raw):
            continue
        s = raw.replace(",", "")
        try:
            v = float(s)
        except ValueError:
            continue
        dec = len(s.split(".")[1].split("e")[0].split("E")[0]) if "." in s else 0
        out.append((v, dec, raw))
    return out


def sentences(text):
    """Split prose into sentences/clauses: at . ! ? followed by space, at every ';', at line breaks;
    table rows are single sentences."""
    res = []
    for line in norm_text(text).splitlines():
        s = line.strip()
        if not s or set(s) <= set("|-: "):
            continue
        if s.startswith("|"):
            res.append(s); continue
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(\[\"'\-])|;", s):
            if part.strip():
                res.append(part.strip())
    return res


def decimals_of(v):
    s = repr(float(v))
    if "e" in s or "E" in s:
        return 6
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def num_matches(v, nums, signed=True):
    """True if v appears in nums with the same value at the more precise of the two printed precisions."""
    dv = decimals_of(v)
    for t, dec, raw in nums:
        a, b = (t, v) if signed else (abs(t), abs(v))
        d = max(dec, dv)
        if round(a, d) == round(b, d):
            return True
    return False


def rounded_only(v, nums):
    """The text shows v only at a coarser precision than the ledger (e.g. ledger 0.112, text 0.11)."""
    dv = decimals_of(v)
    return any(dec < dv and round(abs(v), dec) == abs(t) for t, dec, raw in nums)


def load_list(spec, default=None):
    if spec is None:
        return default
    if spec.startswith("@"):
        f, _, key = spec[1:].partition(":")
        d = json.loads(Path(f).read_text())
        for k in key.split("."):
            d = d[k]
        return [str(x).lower() for x in (d if isinstance(d, list) else d.keys())]
    return [w.strip().lower() for w in spec.split(",") if w.strip()]


def contains_any(sentence, words):
    s = " " + sentence.lower() + " "
    for w in words:
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", s):
            return w
    return None


# ---------------------------------------------------------------- word limits
def check_words(spec):
    """FILE:MAX counts every whitespace token (strictest reading); FILE:MAX:nohead skips lines starting with '#'."""
    parts = spec.split(":")
    nohead = parts[-1] == "nohead"
    if nohead:
        parts = parts[:-1]
    f, mx = ":".join(parts[:-1]), int(parts[-1])
    text = Path(f).read_text()
    n = sum(len(l.split()) for l in text.splitlines() if not (nohead and l.lstrip().startswith("#")))
    if n > mx:
        say("FAIL", f"words {f}: {n} / {mx} - shorten (cut repetition and generic text; keep every required number and ID)")
    elif n > 0.95 * mx:
        say("WARN", f"words {f}: {n} / {mx} - within 5% of the limit; other counting rules may exceed it")
    else:
        say("PASS", f"words {f}: {n} / {mx}")


# ---------------------------------------------------------------- citations
def bib_keys(path):
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", Path(path).read_text()))


def cited_keys(text):
    keys = set()
    for br in re.findall(r"\[([^\]]*@[^\]]*)\]", text):
        keys |= set(re.findall(r"@([\w:.\-/]+[\w])", br))
    for c in re.findall(r"\\(?:cite|citep|citet|parencite|textcite)\w*\{([^}]*)\}", text):
        keys |= {k.strip() for k in c.split(",") if k.strip()}
    return keys


def check_bib(texts, bib):
    known = bib_keys(bib)
    for f in texts:
        t = Path(f).read_text()
        if f.endswith(".json"):
            continue
        unknown = sorted(cited_keys(t) - known)
        say("FAIL" if unknown else "PASS", f"citation keys {f}: " + (f"not in {bib}: {unknown}" if unknown else f"{len(cited_keys(t))} keys, all in {bib}"))
        check_external(f, t)


def check_external(f, t):
    hits = []
    for pat, name in EXTERNAL:
        for m in re.finditer(pat, t, flags=re.I if name != "author-year citation" else 0):
            hits.append(f"{name}: '{m.group(0)[:40]}'")
    say("FAIL" if hits else "PASS", f"external citations {f}: " + ("; ".join(hits[:6]) if hits else "none"))


def source_ids(path):
    ids = set()
    def walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in ("id", "record_id", "entry_id", "ID") and isinstance(v, str):
                    ids.add(v)
                walk(v)
        elif isinstance(d, list):
            for v in d:
                walk(v)
    walk(json.loads(Path(path).read_text()))
    return ids


def check_ids(texts, src):
    known = source_ids(src)
    prefixes = sorted({re.match(r"[A-Za-z]+", i).group(0) for i in known if re.match(r"[A-Za-z]+\d", i)})
    if not prefixes:
        say("WARN", f"ids: no IDs like R01 found in {src}"); return
    mind = min(len(re.sub(r"^[A-Za-z]+", "", i)) for i in known if re.match(r"[A-Za-z]+\d+$", i))
    pat = re.compile(r"(?<![\w])(" + "|".join(map(re.escape, prefixes)) + r")(\d{%d,4})(?![\w*'])" % max(1, mind))
    for f in texts:
        t = Path(f).read_text()
        used = {m.group(1) + m.group(2) for m in pat.finditer(t)}
        unknown = sorted(u for u in used if u not in known)
        say("FAIL" if unknown else "PASS", f"record IDs {f}: " + (f"not in {src}: {unknown}" if unknown else f"{len(used)} cited, all exist"))
        if not f.endswith(".json"):
            check_external(f, t)


# ---------------------------------------------------------------- quotes in a review
def paragraphs(src):
    p = Path(src); text = p.read_text()
    out = {}
    if p.suffix == ".json":
        def walk(d):
            if isinstance(d, dict):
                i = d.get("id") or d.get("paragraph_id") or d.get("table_id")
                if isinstance(i, str):
                    parts = []
                    def strings(x):
                        if isinstance(x, str): parts.append(x)
                        elif isinstance(x, dict): [strings(v) for k, v in x.items() if k not in ("id", "section")]
                        elif isinstance(x, list): [strings(v) for v in x]
                    strings({k: v for k, v in d.items()})
                    out[i] = "\n".join(parts)
                for k, v in d.items():
                    if isinstance(v, (dict, list)): walk(v)
                    elif isinstance(v, str) and k not in ("id",) and re.fullmatch(r"[A-Z]{1,2}\d{1,3}", k): out[k] = v
            elif isinstance(d, list):
                for v in d: walk(v)
        walk(json.loads(text))
    else:
        marks = list(re.finditer(r"\[([A-Z]{1,2}\d{1,3})\]", text))
        for a, b in zip(marks, marks[1:] + [None]):
            out[a.group(1)] = text[a.end(): b.start() if b else len(text)]
    return out


def squash(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def fold(s):
    return squash(norm_text(s).replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
                  .replace("|", " ").replace("*", "").replace("\u00b2", "2").replace("\u00b3", "3"))


def find_issues(review):
    d = json.loads(Path(review).read_text())
    items = d.get("issues") if isinstance(d, dict) else d
    if items is None and isinstance(d, dict):
        items = next((v for v in d.values() if isinstance(v, list) and v and isinstance(v[0], dict) and "quote" in v[0]), [])
    return items or []


def loc_of(item):
    for k in ("paragraph_id", "location", "table_id", "paragraph", "location_id", "section_id"):
        if isinstance(item.get(k), str):
            return item[k]
    return None


def check_quotes(review, src, min_len=10):
    paras = paragraphs(src); bad = 0; items = find_issues(review)
    for n, it in enumerate(items):
        q = str(it.get("quote", "")); loc = loc_of(it); tag = f"{it.get('issue_id', n)}@{loc}"
        if loc not in paras:
            say("FAIL", f"quote {tag}: location {loc!r} is not a paragraph/table ID of {src}"); bad += 1; continue
        if "..." in q or "\u2026" in q or "[...]" in q:
            say("FAIL", f"quote {tag}: contains an ellipsis - copy ONE contiguous passage instead"); bad += 1; continue
        if len(q.strip()) < min_len:
            say("FAIL", f"quote {tag}: shorter than {min_len} characters"); bad += 1; continue
        if squash(q) in squash(paras[loc]):
            continue
        if fold(q) in fold(paras[loc]):
            say("FAIL", f"quote {tag}: matches only after normalizing quotes/dashes/markup - copy the exact characters"); bad += 1
        else:
            other = [k for k, v in paras.items() if squash(q) in squash(v)]
            say("FAIL", f"quote {tag}: not verbatim in {loc}" + (f" (found in {other[0]}: file it there)" if other else "")); bad += 1
    if items and not bad:
        say("PASS", f"quotes: {len(items)} issues, every quote verbatim in its own paragraph")
    elif not items:
        say("FAIL", f"quotes: no issues with a 'quote' found in {review}")


def check_mentions(spec):
    js, _, md = spec.partition("=")
    text = Path(md).read_text(); locs = sorted({loc_of(i) for i in find_issues(js) if loc_of(i)})
    missing = [l for l in locs if not re.search(r"(?<![\w])" + re.escape(l) + r"(?![\w])", text)]
    say("FAIL" if missing else "PASS", f"mentions {md}: " + (f"IDs from {js} not mentioned: {missing}" if missing else f"all {len(locs)} IDs mentioned"))


# ---------------------------------------------------------------- claim ledger against texts
FIELDS = ["estimate", "ci_lower", "ci_upper", "sd", "iqr_lower", "iqr_upper", "n", "p_value"]


def check_claims(claims_path, locs, null_phrases):
    d = json.loads(Path(claims_path).read_text())
    claims = d.get("claims", d) if isinstance(d, dict) else d
    texts = {k: Path(v).read_text() for k, v in locs.items()}
    sents = {k: sentences(v) for k, v in texts.items()}
    nfail = 0
    for c in claims:
        cid = c.get("claim_id") or c.get("id") or c.get("source_id")
        where = c.get("locations") or list(texts)
        where = [where] if isinstance(where, str) else where
        lo, hi = c.get("ci_lower"), c.get("ci_upper")
        spans0 = isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo <= 0 <= hi
        interp = c.get("interpretation")
        if interp in ("effect_detected", "no_effect_detected") and isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            want = "no_effect_detected" if spans0 else "effect_detected"
            if interp != want:
                say("FAIL", f"claim {cid}: interpretation {interp} but the 95% CI [{lo}, {hi}] {'includes' if spans0 else 'excludes'} 0"); nfail += 1
        for loc in where:
            if loc not in texts:
                say("FAIL", f"claim {cid}: location {loc!r} has no --loc {loc}=FILE"); nfail += 1; continue
            nums = numbers(texts[loc])
            for fld in FIELDS:
                v = c.get(fld)
                if v is None:
                    continue
                if fld == "p_value" and isinstance(v, str):
                    m = re.match(r"\s*([<>≤≥]=?)\s*(\d*\.?\d+)", v)
                    if m:
                        num = m.group(2)
                        pat = r"[<≤]\s*" + ("0?" + re.escape(num[1:]) if num.startswith("0.") else re.escape(num))
                        if not re.search(pat, norm_text(texts[loc])):
                            say("FAIL", f"claim {cid}.p_value '{v}' not written in {loc}"); nfail += 1
                    continue
                if not isinstance(v, (int, float)):
                    continue
                if not num_matches(float(v), nums):
                    if num_matches(float(v), nums, signed=False):
                        say("WARN", f"claim {cid}.{fld}={v} appears in {loc} only without its sign")
                    elif rounded_only(float(v), nums):
                        say("FAIL", f"claim {cid}.{fld}={v} is printed with fewer decimals in {loc}: use the same rounding in the ledger and the text"); nfail += 1
                    else:
                        say("FAIL", f"claim {cid}.{fld}={v} not in {loc} (write it there at the ledger's precision, or drop {loc} from locations)"); nfail += 1
            est = c.get("estimate")
            if isinstance(est, (int, float)):
                with_est = [s for s in sents[loc] if num_matches(float(est), numbers(s)) or num_matches(float(est), numbers(s), signed=False)]
                if spans0 and with_est and not any(contains_any(s, null_phrases) for s in with_est):
                    say("FAIL", f"claim {cid}: CI includes 0 but no sentence in {loc} that reports {est} says so ({', '.join(null_phrases[:4])}, ...)"); nfail += 1
                if (interp == "exploratory" or c.get("exploratory") is True) and with_est:
                    unl = [s for s in with_est if not contains_any(s, EXPLORATORY)]
                    if unl:
                        say("FAIL", f"claim {cid}: exploratory estimate without 'exploratory'/'post hoc' in the same clause in {loc}: '{unl[0][:90]}'"); nfail += 1
            if str(c.get("unit", "")).lower().replace(" ", "_") in ("percentage_points", "pp"):
                for fld in ("estimate", "ci_lower", "ci_upper"):
                    v = c.get(fld)
                    if isinstance(v, (int, float)):
                        for m in NUM_RE.finditer(norm_text(texts[loc])):
                            raw = m.group(0)
                            try:
                                if raw and round(float(raw.replace(",", "")), 6) == round(float(v), 6) and norm_text(texts[loc])[m.end():m.end() + 2].strip().startswith("%"):
                                    say("FAIL", f"claim {cid}.{fld}={v} in {loc} is a difference of percentages: write 'percentage points' (pp), not '%'"); nfail += 1; break
                            except ValueError:
                                pass
    if not nfail:
        say("PASS", f"claims: {len(claims)} claims consistent with {', '.join(locs)}")


def pp_lint(files):
    for f in files:
        for s in sentences(Path(f).read_text()):
            if re.search(r"\d\s*%", s) and re.search(r"\b(change|difference|differed|reduction|increase|decrease|lower|higher)\b", s, re.I) \
                    and not re.search(r"relative|percentage point|\bpp\b|95\s*%|CI", s, re.I):
                say("WARN", f"{f}: '%' used for a change or difference - absolute differences of percentages are 'percentage points'; label relative changes 'relative': '{s[:80]}'")


def check_rule(files, spec, forbid):
    trig, _, words = spec.partition("::")
    trig_l = ["*"] if trig.strip() == "*" else load_list(trig)
    words_l = load_list(words)
    bad = 0
    for f in files:
        for s in sentences(Path(f).read_text()):
            if trig_l != ["*"] and not contains_any(s, trig_l):
                continue
            hit = contains_any(s, words_l)
            if forbid and hit:
                say("FAIL", f"{f}: '{hit}' not allowed here: '{s[:100]}'"); bad += 1
            if not forbid and not hit:
                say("FAIL", f"{f}: needs one of {words_l[:4]}: '{s[:100]}'"); bad += 1
    if not bad:
        say("PASS", f"{'forbid' if forbid else 'require'} rule {trig[:30]}::{words[:30]}")


# ---------------------------------------------------------------- traceability of numbers
def source_numbers(path):
    vals = set()
    def walk(d):
        if isinstance(d, bool):
            return
        if isinstance(d, (int, float)):
            vals.add(float(d))
        elif isinstance(d, str):
            for v, _, _ in numbers(d):
                vals.add(v)
        elif isinstance(d, dict):
            for k, v in d.items():
                walk(v)
                for x, _, _ in numbers(str(k)): vals.add(x)
        elif isinstance(d, list):
            for v in d: walk(v)
    p = Path(path)
    if p.suffix == ".json":
        walk(json.loads(p.read_text()))
    else:
        for v, _, _ in numbers(p.read_text()): vals.add(v)
    return vals


def check_trace(files, sources, scales, allow):
    base = set()
    for s in sources:
        base |= source_numbers(s)
    pool = {v * f for v in base for f in [1.0] + list(scales)} | {abs(v * f) for v in base for f in [1.0] + list(scales)}
    pool |= set(allow)
    for f in files:
        bad = []
        text = Path(f).read_text()
        text = re.sub(r"\[[^\]]*@[^\]]*\]|\\cite\w*\{[^}]*\}|\b[A-Z]{1,3}\d{1,4}\b|\[[A-Z]{1,3}\d{1,4}(?:[,;\s]+[A-Z]{1,3}\d{1,4})*\]", " ", text)
        for v, dec, raw in numbers(text):
            if any(round(p, dec) == round(v, dec) or round(p, dec) == round(abs(v), dec) for p in pool):
                continue
            bad.append(raw)
        say("FAIL" if bad else "PASS", f"trace {f}: " + (f"numbers not found in the sources (new statistic, wrong conversion or typo?): {bad[:12]}" if bad else "every number traceable"))


# ---------------------------------------------------------------- numbers from JSON in a text
def get_paths(d, path):
    parts = path.split(".")
    cur = [d]
    for p in parts:
        nxt = []
        for x in cur:
            if p == "*" and isinstance(x, list): nxt += x
            elif isinstance(x, list) and p.isdigit() and int(p) < len(x): nxt.append(x[int(p)])
            elif isinstance(x, dict) and p in x: nxt.append(x[p])
        cur = nxt
    return cur


def check_numbers_in(spec):
    text_f, _, rest = spec.partition("=")
    js, _, paths = rest.partition(":")
    d = json.loads(Path(js).read_text()); nums = numbers(Path(text_f).read_text()); bad = []
    for p in [x for x in paths.split(",") if x]:
        vals = get_paths(d, p)
        if not vals:
            bad.append(f"{p} (missing in {js})")
        for v in vals:
            if isinstance(v, (int, float)) and not isinstance(v, bool) and not num_matches(float(v), nums):
                bad.append(f"{p}={v}")
    say("FAIL" if bad else "PASS", f"numbers of {js} in {text_f}: " + (f"not stated: {bad}" if bad else "all stated"))


# ---------------------------------------------------------------- prose schema
def split_top(s):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "{[(": depth += 1
        if ch in "}])": depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    if cur.strip(): parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def brace_body(desc):
    i = desc.find("{")
    if i < 0: return None
    depth = 0
    for j in range(i, len(desc)):
        if desc[j] == "{": depth += 1
        elif desc[j] == "}":
            depth -= 1
            if depth == 0: return desc[i + 1:j]
    return desc[i + 1:]


def vocab_for(seg, task, field):
    for name, voc in task.items():
        if not name.endswith("vocabulary"):
            continue
        if name in seg:
            if isinstance(voc, dict) and field in voc and isinstance(voc[field], list):
                return voc[field]
            return list(voc.keys()) if isinstance(voc, dict) and not all(isinstance(v, list) for v in voc.values()) else (voc if isinstance(voc, list) else None)
    for name, voc in task.items():
        if name.endswith("vocabulary") and isinstance(voc, dict) and isinstance(voc.get(field), list):
            return voc[field]
    return None


def check_value(v, seg, field, task, path, errs):
    plural = bool(re.search(r"\blist\b|\[\s*\.\.\s*\]|\[\]", seg))
    if "(integer)" in seg or "integer" == seg.strip():
        if not (isinstance(v, int) and not isinstance(v, bool)) and not (isinstance(v, float) and v.is_integer()):
            errs.append(f"{path}: integer expected, got {v!r}")
    voc = vocab_for(seg, task, field)
    if voc is not None:
        vals = v if isinstance(v, list) else [v]
        if isinstance(v, list) and not plural and len(v) != 1:
            errs.append(f"{path}: one vocabulary value expected, got a list {v!r}")
        elif isinstance(v, list) and not plural:
            errs.append(f"{path}: write the single value {v[0]!r}, not a list")
        for x in vals:
            if isinstance(x, str) and x not in voc:
                errs.append(f"{path}: {x!r} not in vocabulary {voc[:8]}")
    if plural and v is not None and not isinstance(v, list):
        errs.append(f"{path}: list expected, got {type(v).__name__}")


def check_desc(out, desc, task, path, errs):
    if isinstance(desc, dict):
        if not isinstance(out, dict):
            errs.append(f"{path or 'top level'}: object expected"); return
        for k, sub in desc.items():
            if k in ("other keys",) or (isinstance(sub, str) and "optional" in sub.lower()[:40]):
                continue
            if k not in out:
                errs.append(f"{path + '.' if path else ''}{k}: missing"); continue
            check_desc(out[k], sub, task, f"{path + '.' if path else ''}{k}", errs)
        return
    if not isinstance(desc, str):
        return
    body = brace_body(desc)
    is_list = desc.strip().lower().startswith("list")
    if body is None:
        check_value(out, desc, path.split(".")[-1], task, path, errs); return
    items = out if is_list else [out]
    if is_list and not isinstance(out, list):
        errs.append(f"{path}: list expected"); return
    if is_list and re.search(r"at least (\w+)", desc):
        w = re.search(r"at least (\w+)", desc).group(1)
        n = {"one": 1, "two": 2, "three": 3}.get(w, int(w) if w.isdigit() else 1)
        if len(out) < n: errs.append(f"{path}: at least {n} items expected, got {len(out)}")
    for i, item in enumerate(items):
        p = f"{path}[{i}]" if is_list else path
        if not isinstance(item, dict):
            errs.append(f"{p}: object expected"); continue
        for seg in split_top(body):
            m = re.match(r"([A-Za-z_][\w]*)", seg)
            if not m:
                continue
            k = m.group(1)
            if "(optional)" in seg or "optional" in seg.lower().split(":")[-1][:12]:
                if k not in item: continue
            if k not in item:
                errs.append(f"{p}.{k}: missing"); continue
            rest = seg[len(k):].lstrip(" :")
            if rest.startswith("{") or rest.lower().startswith("list of {"):
                check_desc(item[k], rest, task, f"{p}.{k}", errs)
            else:
                check_value(item[k], seg, k, task, f"{p}.{k}", errs)


def check_schema(spec):
    left, _, out_f = spec.partition("=")
    task_f, _, key = left.partition(":")
    task = json.loads(Path(task_f).read_text()); desc = task
    for k in key.split("."):
        desc = desc[k]
    out = json.loads(Path(out_f).read_text()); errs = []
    check_desc(out, desc, task, "", errs)
    for e in errs[:25]:
        say("FAIL", f"schema {out_f}: {e}")
    if not errs:
        say("PASS", f"schema {out_f}: keys, lists, integers and vocabulary values match {task_f}:{key}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", action="append", default=[])
    ap.add_argument("--texts", nargs="+", default=[])
    ap.add_argument("--bib"); ap.add_argument("--ids")
    ap.add_argument("--quotes"); ap.add_argument("--source"); ap.add_argument("--min-quote", type=int, default=10)
    ap.add_argument("--mentions", action="append", default=[])
    ap.add_argument("--claims"); ap.add_argument("--loc", action="append", default=[])
    ap.add_argument("--null-phrases")
    ap.add_argument("--require-in", action="append", default=[]); ap.add_argument("--forbid-in", action="append", default=[])
    ap.add_argument("--trace", action="append", default=[]); ap.add_argument("--scale", type=float, action="append", default=[])
    ap.add_argument("--allow", type=float, nargs="*", default=[95.0])
    ap.add_argument("--numbers-in", action="append", default=[])
    ap.add_argument("--schema", action="append", default=[])
    a = ap.parse_args(argv)
    OUT.clear()
    locs = dict(x.split("=", 1) for x in a.loc)
    prose = [f for f in list(dict.fromkeys(a.texts + list(locs.values()))) if not f.endswith(".json")]
    for w in a.words: check_words(w)
    if a.bib: check_bib(a.texts or prose, a.bib)
    if a.ids: check_ids(a.texts or prose, a.ids)
    if a.quotes:
        if not a.source: say("FAIL", "--quotes needs --source PARAGRAPHS.json|.md")
        else: check_quotes(a.quotes, a.source, a.min_quote)
    for m in a.mentions: check_mentions(m)
    if a.claims: check_claims(a.claims, locs, load_list(a.null_phrases, NULL_PHRASES))
    if a.claims or a.trace: pp_lint(prose)
    for r in a.require_in: check_rule(prose, r, False)
    for r in a.forbid_in: check_rule(prose, r, True)
    if a.trace:
        extra = [a.claims] if a.claims else []
        check_trace(prose, a.trace + extra, a.scale, a.allow)
    for s in a.numbers_in: check_numbers_in(s)
    for s in a.schema: check_schema(s)
    nf = sum(1 for l, _ in OUT if l == "FAIL")
    print(f"{'FAILED' if nf else 'OK'}: {nf} FAIL, {sum(1 for l, _ in OUT if l == 'WARN')} WARN, {sum(1 for l, _ in OUT if l == 'PASS')} PASS")
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())

