"""Test inline_helpers.py: copied helpers run in a clean folder without the skill on sys.path."""
import os, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import inline_helpers as ih

MOD = '''"""toy module"""
import math
SCALE = 2.0
OFFSET = SCALE + 1.0

def _sq(x):
    return x * x

def area(r):
    """Uses a private helper and two constants."""
    return math.pi * _sq(r) * SCALE + OFFSET

def unused():
    return 0

if __name__ == "__main__":
    print("module main")
'''

ENTRY = '''#!/usr/bin/env python3
"""entrypoint"""
import sys

def main():
    print(round(area(float(sys.argv[1])), 6))

if __name__ == "__main__":
    main()
'''

with tempfile.TemporaryDirectory() as d:
    d = Path(d); (d / "toy.py").write_text(MOD); (d / "run.py").write_text(ENTRY)
    ih.main([str(d / "toy.py"), "area", "--into", str(d / "run.py")])
    clean = d / "clean"; clean.mkdir(); (clean / "run.py").write_text((d / "run.py").read_text())
    out = subprocess.run([sys.executable, "run.py", "1.5"], cwd=clean, capture_output=True, text=True)
    import math
    assert out.returncode == 0 and abs(float(out.stdout) - (math.pi * 2.25 * 2 + 3)) < 1e-6, out
    text = (clean / "run.py").read_text()
    assert "def unused" not in text and "module main" not in text and text.count(ih.START) == 1
    ih.main([str(d / "toy.py"), "area", "--into", str(d / "run.py")])          # replaces, does not duplicate
    assert (d / "run.py").read_text().count(ih.START) == 1
    # a real MRFoundry module: GRAPPA from a sampling mask, copied into a standalone file
    rec = HERE.parent.parent / "mri-reconstruction" / "scripts" / "mrfoundry_rawrecon.py"
    if rec.exists():
        try:
            import numpy  # noqa: F401
            block = ih.collect(str(rec), ["grappa_from_mask", "ifft2c"])
            assert "def sampling_pattern" in block and "def grappa_2d" in block and "import numpy as np" in block
            ns = {}; exec(compile(block, "block", "exec"), ns)
            assert callable(ns["grappa_from_mask"])
        except ImportError:
            pass
print("inline_helpers: transitive helpers and constants copied, clean-folder run ok, block replaced in place")

