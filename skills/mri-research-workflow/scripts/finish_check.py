#!/usr/bin/env python3
"""Finish check: run this before you report a task as done.

It catches the packaging failures that most often make correct work unusable:
missing or misnamed deliverables, an entrypoint stored apart from its outputs, a missing
environment record, and an entrypoint that only works in your own working copy.

  python finish_check.py --require fit.py report.json README.md cbf.nii.gz \
      --rerun "python fit.py --input {inputs}/data.nii.gz --outdir {out}" \
      --inputs inputs --expect cbf.nii.gz report.json --json report.json:method,limitations

  --require   every deliverable name the task lists (files or folders). All must sit in ONE folder:
              the folder the task names, else the workspace root (--root). A script in the root with
              its outputs in out/ is reported as a split and fails.
  --rerun     the documented command. It is run in a fresh temporary folder that contains only the
              entrypoint script(s) named in the command and a copy of --inputs; {inputs} and {out}
              are replaced by paths in that folder. "python" is replaced by --python (default:
              .venv/bin/python if it exists, else this interpreter).
  --expect    files the rerun must create inside {out} (default: {out} must not be empty).
  --json      FILE:key1,key2/sub : keys (nested with /) that must exist in a JSON deliverable.
  --range     FILE:LOW:HIGH : the median of the finite non-zero values of a NIfTI/NPY/NPZ output must
              lie in [LOW, HIGH] (a cheap unit check, e.g. MD in mm^2/s, CBF in ml/100 g/min).
Exit code 0 only if every check passes. Standard library only (numpy/nibabel are used for --range).
"""
import argparse, json, os, shlex, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ENV_PATTERNS = ("environment*", "requirements*", "*freeze*", "env*.txt", "env*.json", "*versions*",
                "pyproject.toml", "uv.lock", "environment.yml")
SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", ".agents", ".cache", ".julia"}


def find_all(root, name):
    """Every path below root (depth <= 3, skipping tool folders) whose relative path ends with name."""
    root = Path(root); hits = []
    direct = root / name
    if direct.exists():
        hits.append(direct)
    for dirpath, dirnames, _ in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        if len(rel.parts) >= 3:
            dirnames[:] = []
        cand = Path(dirpath) / name
        if Path(dirpath) != root and cand.exists():
            hits.append(cand)
    return hits


def check_location(root, required):
    """Return (ok, lines, folder) for the required names; ok only if all are in one folder."""
    lines = []; folders = {}
    for name in required:
        hits = find_all(root, name)
        if not hits:
            lines.append(f"FAIL missing deliverable: {name}")
            continue
        parent = hits[0].parent.relative_to(root) if Path(name).parent == Path('.') else Path('.')
        folders.setdefault(str(parent), []).append(name)
        if len(hits) > 1:
            lines.append(f"NOTE {name} exists in several places: " + ", ".join(str(h.relative_to(root)) for h in hits[:4]))
    ok = not any(l.startswith('FAIL') for l in lines)
    if len(folders) > 1:
        ok = False
        desc = "; ".join(f"{k or '.'}: {', '.join(v)}" for k, v in folders.items())
        lines.append("FAIL deliverables are split across folders (" + desc + "). Put the entrypoint and every "
                     "output in the one folder the task names (workspace root if none), and rerun there.")
    folder = next(iter(folders)) if len(folders) == 1 else None
    if ok:
        lines.append(f"PASS all {len(required)} required deliverables in ./{folder if folder not in (None, '.') else ''}")
    return ok, lines, folder


def check_env_record(root, folder):
    for d in {Path(root), Path(root) / (folder or '.')}:
        for p in ENV_PATTERNS:
            for f in d.glob(p):
                if f.is_file() and f.stat().st_size > 0:
                    return True, f"PASS environment record: {f.relative_to(root)}"
    return False, "FAIL no environment record (write environment.txt with the interpreter path, python and package versions, and the run command)"


def default_python(root):
    for cand in (Path(root) / ".venv/bin/python", Path(root) / ".venv/Scripts/python.exe"):
        if cand.exists():
            return str(cand.resolve())
    return sys.executable


def check_json(root, folder, spec):
    lines = []; ok = True
    for item in spec or []:
        fname, _, keys = item.partition(':')
        path = Path(root) / (folder or '.') / fname
        if not path.exists():
            hits = find_all(root, fname); path = hits[0] if hits else path
        try:
            data = json.loads(path.read_text())
        except Exception as e:  # noqa: BLE001
            lines.append(f"FAIL {fname}: unreadable JSON ({e})"); ok = False; continue
        missing = []
        for key in [k for k in keys.split(',') if k]:
            d = data
            for part in key.split('/'):
                if isinstance(d, dict) and part in d:
                    d = d[part]
                elif isinstance(d, list) and part.isdigit() and int(part) < len(d):
                    d = d[int(part)]
                else:
                    missing.append(key); break
        if missing:
            ok = False; lines.append(f"FAIL {fname}: missing keys {missing}")
        else:
            lines.append(f"PASS {fname}: keys present")
    return ok, lines


def _median_of(path):
    import numpy as np
    p = str(path)
    if p.endswith(('.nii', '.nii.gz')):
        import nibabel as nib
        a = np.asarray(nib.load(p).dataobj, dtype=float)
    elif p.endswith('.npz'):
        z = np.load(p); a = np.asarray(z[z.files[0]], dtype=float)
    else:
        a = np.asarray(np.load(p), dtype=float)
    a = a[np.isfinite(a) & (a != 0)]
    return float(np.median(a)) if a.size else float('nan')


def check_ranges(root, folder, spec):
    lines = []; ok = True
    for item in spec or []:
        fname, lo, hi = item.rsplit(':', 2)
        hits = find_all(root, fname)
        if not hits:
            lines.append(f"FAIL range {fname}: file not found"); ok = False; continue
        try:
            med = _median_of(hits[0])
        except Exception as e:  # noqa: BLE001
            lines.append(f"FAIL range {fname}: unreadable ({e})"); ok = False; continue
        good = float(lo) <= med <= float(hi)
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'} median of {fname} = {med:.4g} (expected {lo}..{hi}; check units and scaling)")
    return ok, lines


def rerun(root, folder, command, inputs, expect, python, timeout):
    """Run the command in a fresh folder holding only the scripts it names and a copy of the inputs."""
    root = Path(root); lines = []
    tmp = Path(tempfile.mkdtemp(prefix="finish_check_"))
    out = tmp / "out"
    tokens = shlex.split(command)
    scripts = {}
    for t in tokens:
        if t.endswith(('.py', '.jl', '.m', '.sh', '.R')):
            for base in (root, root / (folder or '.')):
                if (base / t).is_file():
                    scripts[t] = base / t; break
    if not scripts:
        return False, [f"FAIL rerun: no script named in the command exists in {root} or ./{folder or ''}"]
    for t, src in scripts.items():
        shutil.copy2(src, tmp / Path(t).name)
    in_dst = tmp / "inputs"
    if inputs:
        src = root / inputs
        if src.is_dir():
            shutil.copytree(src, in_dst)
        elif src.is_file():
            in_dst.mkdir(); shutil.copy2(src, in_dst / src.name)
        else:
            return False, [f"FAIL rerun: inputs {inputs} not found"]
    parts = [t.replace('{inputs}', str(in_dst)).replace('{out}', str(out)) for t in tokens]
    parts = [str(tmp / Path(t).name) if t in scripts else t for t in parts]
    if parts and parts[0] in ('python', 'python3'):
        parts[0] = python
    t0 = time.time()
    try:
        r = subprocess.run(parts, cwd=tmp, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, [f"FAIL rerun timed out after {timeout:.0f} s: {' '.join(parts)}"]
    dt = time.time() - t0
    if r.returncode != 0:
        tail = (r.stderr or r.stdout).strip().splitlines()[-6:]
        return False, [f"FAIL rerun exited {r.returncode} in a clean folder ({dt:.0f} s):"] + ["     " + t for t in tail]
    if expect:
        missing = [e for e in expect if not (out / e).exists() and not (tmp / e).exists()]
        if missing:
            return False, [f"FAIL rerun finished but did not write {missing} into {{out}} ({dt:.0f} s)"]
    elif not (out.exists() and any(out.iterdir())):
        return False, [f"FAIL rerun finished but wrote nothing into {{out}} ({dt:.0f} s); pass --expect to name the outputs"]
    lines.append(f"PASS rerun in a clean folder with {Path(python).name} ({dt:.0f} s): {' '.join(parts)[:160]}")
    return True, lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default='.')
    ap.add_argument('--require', nargs='+', default=[])
    ap.add_argument('--rerun')
    ap.add_argument('--inputs')
    ap.add_argument('--expect', nargs='*')
    ap.add_argument('--json', nargs='*')
    ap.add_argument('--range', nargs='*', dest='ranges')
    ap.add_argument('--python')
    ap.add_argument('--timeout', type=float, default=1800)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve(); results = []
    ok_loc, lines, folder = check_location(root, a.require) if a.require else (True, [], '.')
    results.append(ok_loc); print("\n".join(lines))
    ok_env, line = check_env_record(root, folder); results.append(ok_env); print(line)
    if a.json:
        ok, lines = check_json(root, folder, a.json); results.append(ok); print("\n".join(lines))
    if a.ranges:
        ok, lines = check_ranges(root, folder, a.ranges); results.append(ok); print("\n".join(lines))
    if a.rerun:
        ok, lines = rerun(root, folder, a.rerun, a.inputs, a.expect, a.python or default_python(root), a.timeout)
        results.append(ok); print("\n".join(lines))
    else:
        print("NOT RUN rerun: pass --rerun with the documented command to prove the entrypoint works from a clean folder")
    print("ALL PASS" if all(results) else "FIX THE FAIL LINES, then run this check again")
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())

