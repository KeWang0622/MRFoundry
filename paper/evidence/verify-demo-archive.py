"""Verify demonstration archive bytes only; no scientific imports or execution."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'demo-manifest.json').read_text())
for item in manifest['files']:
    path = root / item['path']
    if root not in path.resolve().parents:
        raise SystemExit('Manifest path escapes the evidence folder')
    content = path.read_bytes()
    if len(content) != item['bytes'] or hashlib.sha256(content).hexdigest() != item['sha256']:
        raise SystemExit('Archive mismatch: ' + item['path'])
print(f"Verified {len(manifest['files'])} original demonstration files; no scientific calculation performed.")
