#!/usr/bin/env python3
"""Repo structure validation for CI (standard library only).

Every check here exists because something actually broke once.

  1. skills.sh.json is valid JSON.
  2. Every skills/<name>/SKILL.md has frontmatter with name, description,
     metadata.version, and metadata.author.
  3. The frontmatter `name` matches its directory name (they are two different
     identifiers and drifted apart before).
  4. `description` is at most 1024 characters -- the hard limit skill validators
     enforce. A too-long description fails silently at install time.
  5. One source of truth for the version: all seven SKILL.md files, CITATION.cff,
     and any optional README version fields must agree. v0.6.0 claimed to have "aligned all version
     numbers" while five skills sat at 0.1.0.
  6. The skills listed in skills.sh.json exactly match the skills/<name>/ folders.
  7. Every relative Markdown link inside skills/ resolves on disk, and every
     references/*.md file is reachable from the hub's routing table (an orphaned
     reference file is a file no agent will ever open).
  8. The README expert table lists every shipped skill.
"""
import json
import os
import re
import sys

errors = []
DESCRIPTION_LIMIT = 1024


def fail(msg):
    errors.append(msg)


def parse_frontmatter(text, path):
    """Minimal YAML-subset frontmatter parser (stdlib only).

    Handles exactly what these files use: top-level scalars, `>-` folded block
    scalars, and one level of nesting under `metadata:`. Folded scalars are
    joined with single spaces, which matches YAML for blocks without blank lines.
    """
    if not text.startswith("---"):
        fail(f"{path}: missing YAML frontmatter")
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        fail(f"{path}: unterminated YAML frontmatter")
        return None
    lines = parts[1].splitlines()
    data, i = {}, 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^(\S[^:]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value in (">-", ">", "|", "|-"):  # folded / literal block
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith(" ")):
                block.append(lines[i].strip())
                i += 1
            data[key] = " ".join(b for b in block if b)
        elif value == "":  # nested mapping, e.g. metadata:
            nested = {}
            while i < len(lines) and lines[i].startswith(" "):
                nm = re.match(r"^\s+(\S[^:]*):\s*(.*)$", lines[i])
                i += 1
                if nm:
                    nested[nm.group(1)] = nm.group(2).strip().strip('"').strip("'")
            data[key] = nested
        else:
            data[key] = value.strip('"').strip("'")
    return data


# 1) skills.sh.json valid JSON
try:
    reg = json.load(open("skills.sh.json", encoding="utf-8"))
except Exception as e:  # noqa: BLE001
    print(f"::error file=skills.sh.json::invalid JSON: {e}")
    sys.exit(1)

skill_dirs = sorted(
    d for d in os.listdir("skills") if os.path.isdir(os.path.join("skills", d))
)

# 2-5) frontmatter contents
versions = {}
for d in skill_dirs:
    p = os.path.join("skills", d, "SKILL.md")
    if not os.path.isfile(p):
        fail(f"{p}: missing SKILL.md")
        continue
    fm = parse_frontmatter(open(p, encoding="utf-8").read(), p)
    if fm is None:
        continue

    name = fm.get("name")
    desc = fm.get("description")
    meta = fm.get("metadata") or {}

    if not name:
        fail(f"{p}: frontmatter missing 'name'")
    elif name != d:
        fail(f"{p}: frontmatter name '{name}' does not match directory '{d}'")

    if not desc:
        fail(f"{p}: frontmatter missing 'description'")
    elif len(desc) > DESCRIPTION_LIMIT:
        fail(
            f"{p}: description is {len(desc)} chars, over the "
            f"{DESCRIPTION_LIMIT}-char limit (trim by {len(desc) - DESCRIPTION_LIMIT})"
        )

    if not meta.get("author"):
        fail(f"{p}: frontmatter missing 'metadata.author'")
    if not meta.get("version"):
        fail(f"{p}: frontmatter missing 'metadata.version'")
    else:
        versions[p] = meta["version"]

# 5) one version everywhere
distinct = sorted(set(versions.values()))
if len(distinct) > 1:
    fail("skill versions disagree: " + ", ".join(f"{p}={v}" for p, v in sorted(versions.items())))
elif distinct:
    version = distinct[0]

    cff = open("CITATION.cff", encoding="utf-8").read()
    m = re.search(r"^version:\s*(\S+)\s*$", cff, re.M)
    if not m:
        fail("CITATION.cff: no 'version:' field found")
    elif m.group(1).strip('"').strip("'") != version:
        fail(f"CITATION.cff version {m.group(1)} != skill version {version}")

    readme = open("README.md", encoding="utf-8").read()
    badge = re.search(r"badge/version-([0-9][^-\s)]*)-", readme)
    if badge and badge.group(1) != version:
        fail(f"README.md badge version {badge.group(1)} != skill version {version}")
    bibtex = re.search(r"version\s*=\s*\{([^}]+)\}", readme)
    if bibtex and bibtex.group(1) != version:
        fail(f"README.md BibTeX version {bibtex.group(1)} != skill version {version}")

# 6) registry <-> folder consistency
listed = {s for g in reg.get("groupings", []) for s in g.get("skills", [])}
folders = set(skill_dirs)
for miss in sorted(folders - listed):
    fail(f"skills.sh.json: folder '{miss}' is not listed in any grouping")
for miss in sorted(listed - folders):
    fail(f"skills.sh.json: lists '{miss}' but skills/{miss}/ does not exist")

# 7a) relative Markdown links inside skills/ resolve on disk
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
for root, _dirs, files in os.walk("skills"):
    for fn in files:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(root, fn)
        for target in LINK_RE.findall(open(p, encoding="utf-8").read()):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            resolved = os.path.normpath(os.path.join(root, target.split("#")[0]))
            if not os.path.exists(resolved):
                fail(f"{p}: relative link '{target}' does not resolve ({resolved})")

# 7b) every references/*.md is reachable from the hub routing table
hub = os.path.join("skills", "mri-research", "SKILL.md")
ref_dir = os.path.join("skills", "mri-research", "references")
if os.path.isfile(hub) and os.path.isdir(ref_dir):
    hub_text = open(hub, encoding="utf-8").read()
    routed = set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", hub_text))
    on_disk = {f for f in os.listdir(ref_dir) if f.endswith(".md")}
    for orphan in sorted(on_disk - routed):
        fail(f"{hub}: references/{orphan} exists but is not routed to from the hub")
    for dangling in sorted(routed - on_disk):
        fail(f"{hub}: routes to references/{dangling}, which does not exist")

# 8) README expert table lists every skill
readme = open("README.md", encoding="utf-8").read()
for d in skill_dirs:
    if f"skills/{d}/SKILL.md" not in readme:
        fail(f"README.md: skill '{d}' is not linked in the expert table")

if errors:
    for e in errors:
        print(f"::error::{e}")
    sys.exit(1)

print(
    f"OK: {len(skill_dirs)} skills at version {distinct[0] if distinct else '?'}; "
    "skills.sh.json valid; frontmatter complete and within the description limit; "
    "versions aligned; registry matches folders; relative links and routing table resolve."
)
