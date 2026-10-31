#!/usr/bin/env python3
"""Tests for finish_check.py (standard library only): python test_finish_check.py"""
import io, os, sys, tempfile, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import finish_check as fc

ENTRY = '''import argparse, json, pathlib
ap = argparse.ArgumentParser(); ap.add_argument('--input'); ap.add_argument('--outdir'); a = ap.parse_args()
out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
txt = pathlib.Path(a.input).read_text()
(out / 'result.json').write_text(json.dumps({'method': 'demo', 'n': len(txt), 'limitations': ['toy']}))
'''

def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fc.main(argv)
    return code, buf.getvalue()

def project(split=False, broken=False):
    d = Path(tempfile.mkdtemp())
    (d / 'inputs').mkdir(); (d / 'inputs' / 'data.txt').write_text('abc')
    (d / 'run.py').write_text(ENTRY if not broken else ENTRY + "\nimport not_a_real_module_xyz\n")
    out = d / ('out' if split else '.')
    out.mkdir(exist_ok=True)
    (out / 'result.json').write_text('{"method": "demo", "limitations": ["toy"]}')
    (d / 'README.md').write_text('readme'); (d / 'environment.txt').write_text('python 3')
    return d

cmd = 'python run.py --input {inputs}/data.txt --outdir {out}'
req = ['run.py', 'result.json', 'README.md']

d = project()
code, out = run(['--root', str(d), '--require', *req, '--rerun', cmd, '--inputs', 'inputs', '--expect', 'result.json',
                 '--json', 'result.json:method,limitations', '--python', sys.executable])
assert code == 0 and 'ALL PASS' in out, out
print('complete deliverables with a working entrypoint: ALL PASS')

d = project(split=True)
code, out = run(['--root', str(d), '--require', *req, '--python', sys.executable])
assert code == 1 and 'split across folders' in out, out
print('entrypoint in the root with outputs in out/: reported as a split (FAIL)')

d = project()
(d / 'README.md').unlink()
code, out = run(['--root', str(d), '--require', *req])
assert code == 1 and 'missing deliverable: README.md' in out, out
print('missing deliverable reported')

d = project(broken=True)
code, out = run(['--root', str(d), '--require', *req, '--rerun', cmd, '--inputs', 'inputs', '--python', sys.executable])
assert code == 1 and 'FAIL rerun exited' in out, out
print('entrypoint that fails in a clean folder reported with its error tail')

d = project()
code, out = run(['--root', str(d), '--require', *req, '--rerun', cmd, '--inputs', 'inputs', '--expect', 'maps.npz',
                 '--python', sys.executable])
assert code == 1 and "did not write ['maps.npz']" in out, out
print('expected output not written by the rerun: FAIL')

d = project(); (d / 'environment.txt').unlink()
code, out = run(['--root', str(d), '--require', *req])
assert code == 1 and 'no environment record' in out, out
print('missing environment record: FAIL')

try:
    import numpy as np
    d = project(); np.save(d / 'md.npy', np.full((4, 4), 0.8))
    code, out = run(['--root', str(d), '--require', *req, '--range', 'md.npy:0.0001:0.004'])
    assert code == 1 and 'FAIL median of md.npy' in out, out
    code, out = run(['--root', str(d), '--require', *req, '--range', 'md.npy:0.1:3'])
    assert code == 0, out
    print('median range check catches a unit error (x1000)')
except ImportError:
    print('numpy not installed: range check test skipped')
print('all finish_check tests passed')

