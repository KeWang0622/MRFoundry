#!/usr/bin/env python3
"""Check that the upstreams this repo points at still exist -- and are still alive.

This exists because of v0.7.0: BART, the toolbox at the centre of the
reconstruction agent, had migrated to Codeberg and its GitHub repository had been
archived. Every link still returned HTTP 200, so the link checker was happy while
the docs pointed at a frozen tree. A 200 is not evidence that a dependency is
maintained.

Two classes of finding, deliberately treated differently:

  HARD FAIL (a definite error in this repo)
    * a linked GitHub/Codeberg repository does not exist (404)
    * a named PyPI package does not exist
    * a cited DOI does not resolve in Crossref
  WARNING (upstream changed; a human decides what to do)
    * the repository is archived
    * the repository was renamed or transferred (the URL silently redirects)
  INFO
    * no pushes for >36 months. Paper code is archival by nature, so this is
      listed rather than warned about -- but it is the number to check before
      describing something as maintained tooling.

Network trouble is never a hard fail: an inconclusive check is reported as
skipped, so a flaky runner cannot block a pull request.

Usage:
  python3 .github/scripts/check_upstreams.py            # all checks
  python3 .github/scripts/check_upstreams.py --warn-only
  python3 .github/scripts/check_upstreams.py --report-dormant
Set GITHUB_TOKEN to avoid GitHub API rate limits.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA = "MRFoundry-upstream-check (+https://github.com/KeWang0622/MRFoundry)"
STALE_DAYS = 1095  # 36 months

failures: list[str] = []
warnings: list[str] = []
dormant: list[str] = []
skipped: list[str] = []


def get_json(url, headers=None, retries=2):
    """GET a JSON document. Returns (data, status). status is None on network error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8")), r.status
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < retries:
                time.sleep(5 * (attempt + 1))
                continue
            return None, e.code
        except Exception:  # noqa: BLE001 - DNS, TLS, timeouts
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return None, None
    return None, None


def collect_markdown():
    out = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
        out += [os.path.join(root, f) for f in files if f.endswith(".md")]
    return sorted(out)


def scan(files):
    gh, cb, pypi, dois = {}, {}, {}, {}
    for p in files:
        text = open(p, encoding="utf-8").read()
        for owner, repo in re.findall(
            r"https://github\.com/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)", text
        ):
            repo = repo.rstrip(".")
            if owner.lower() in {"sponsors", "orgs", "features", "apps"}:
                continue
            gh.setdefault(f"{owner}/{repo}", set()).add(p)
        for owner, repo in re.findall(
            r"https://codeberg\.org/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)", text
        ):
            cb.setdefault(f"{owner}/{repo.rstrip('.')}", set()).add(p)
        # Both forms of "this package exists": a PyPI link, and a pip install line.
        # (The `cfl.py` episode: BART's Python helper is *not* on PyPI, and the
        # `bartpy` name there belongs to an unrelated decision-tree library.)
        for pkg in re.findall(r"https://pypi\.org/project/([A-Za-z0-9._-]+)", text):
            pypi.setdefault(pkg.rstrip("./"), set()).add(p)
        for pkg in re.findall(
            r"pip install\s+(?:-U\s+|--upgrade\s+)?([A-Za-z][A-Za-z0-9._-]*)", text
        ):
            pypi.setdefault(pkg, set()).add(p)
        for doi in re.findall(r"doi:(10\.\d{4,9}/[^\s)\]}>,;]+)", text):
            dois.setdefault(doi.rstrip(".,;:"), set()).add(p)
    return gh, cb, pypi, dois


def where(paths):
    return ", ".join(sorted(paths))


def check_github(repos):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    now = time.time()
    for full, paths in sorted(repos.items()):
        data, status = get_json(f"https://api.github.com/repos/{full}", headers)
        if status == 404:
            failures.append(f"GitHub repo does not exist: {full}  ({where(paths)})")
            continue
        if data is None:
            skipped.append(f"GitHub {full} (HTTP {status})")
            continue
        actual = data.get("full_name", full)
        if actual.lower() != full.lower():
            warnings.append(
                f"GitHub repo renamed/transferred: {full} -> {actual}  ({where(paths)})"
            )
        if data.get("archived"):
            warnings.append(f"GitHub repo is ARCHIVED: {actual}  ({where(paths)})")
        pushed = data.get("pushed_at")
        if pushed:
            age = (now - time.mktime(time.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ"))) / 86400
            if age > STALE_DAYS:
                dormant.append(
                    f"{actual}: no push in {int(age / 30)} months  ({where(paths)})"
                )


def check_codeberg(repos):
    for full, paths in sorted(repos.items()):
        data, status = get_json(f"https://codeberg.org/api/v1/repos/{full}")
        if status == 404:
            failures.append(f"Codeberg repo does not exist: {full}  ({where(paths)})")
        elif data is None:
            skipped.append(f"Codeberg {full} (HTTP {status})")
        elif data.get("archived"):
            warnings.append(f"Codeberg repo is ARCHIVED: {full}  ({where(paths)})")


def check_pypi(packages):
    for pkg, paths in sorted(packages.items()):
        data, status = get_json(f"https://pypi.org/pypi/{pkg}/json")
        if status == 404:
            failures.append(f"PyPI package does not exist: {pkg}  ({where(paths)})")
        elif data is None:
            skipped.append(f"PyPI {pkg} (HTTP {status})")


def check_dois(dois):
    for doi, paths in sorted(dois.items()):
        data, status = get_json(f"https://api.crossref.org/works/{doi}")
        if status == 404:
            failures.append(f"DOI does not resolve: {doi}  ({where(paths)})")
        elif data is None:
            skipped.append(f"DOI {doi} (HTTP {status})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--warn-only",
        action="store_true",
        help="report hard failures as warnings and always exit 0",
    )
    ap.add_argument(
        "--report-dormant",
        action="store_true",
        help="also emit a CI warning per dormant repo (default: list them only)",
    )
    args = ap.parse_args()

    gh, cb, pypi, dois = scan(collect_markdown())
    print(
        f"Checking {len(gh)} GitHub repos, {len(cb)} Codeberg repos, "
        f"{len(pypi)} PyPI packages, {len(dois)} DOIs..."
    )
    check_github(gh)
    check_codeberg(cb)
    check_pypi(pypi)
    check_dois(dois)

    for w in warnings:
        print(f"::warning::{w}")
    for s in skipped:
        print(f"::notice::inconclusive, skipped: {s}")
    for f in failures:
        print(f"::{'warning' if args.warn_only else 'error'}::{f}")

    if dormant:
        print(f"\nDormant upstreams (>{STALE_DAYS // 30} months, informational):")
        for d in sorted(dormant):
            print(f"  - {d}")
            if args.report_dormant:
                print(f"::warning::dormant upstream: {d}")

    print(
        f"\n{len(failures)} failure(s), {len(warnings)} warning(s), "
        f"{len(dormant)} dormant, {len(skipped)} inconclusive."
    )
    if failures and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
