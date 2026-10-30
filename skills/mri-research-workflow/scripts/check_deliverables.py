#!/usr/bin/env python3
"""Check deliverables against a small spec before finishing (python check_deliverables.py spec.json).

spec.json example:
{"files": ["outputs/results.json", "outputs/maps/sub-01_fa.nii.gz"],
 "json": {"outputs/results.json": {"required_paths": ["subjects/S01/tract1/fa", "methods_summary"]}},
 "npz": {"maps.npz": {"echo_images": [4, 48, 48], "t2_map_s": [48, 48]}}}
Paths in required_paths use '/' between nested keys. Shapes may use null for any length.
"""
import json,sys
from pathlib import Path
def get(d,path):
    for k in path.split('/'):
        if isinstance(d,dict) and k in d:d=d[k]
        elif isinstance(d,list) and k.isdigit() and int(k)<len(d):d=d[int(k)]
        else:raise KeyError(path)
    return d
def main(spec_path):
    spec=json.loads(Path(spec_path).read_text());root=Path(spec.get('root','.'));bad=[]
    for f in spec.get('files',[]):
        if not (root/f).exists():bad.append(f'missing file {f}')
    for f,rules in spec.get('json',{}).items():
        try:d=json.loads((root/f).read_text())
        except Exception as e:bad.append(f'{f}: unreadable JSON ({e})');continue
        for p in rules.get('required_paths',[]):
            try:get(d,p)
            except KeyError:bad.append(f'{f}: missing key path {p}')
    for f,shapes in spec.get('npz',{}).items():
        try:
            import numpy as np;z=np.load(root/f,allow_pickle=False)
        except Exception as e:bad.append(f'{f}: unreadable ({e})');continue
        for k,shape in shapes.items():
            if k not in z:bad.append(f'{f}: missing array {k}');continue
            s=z[k].shape
            if shape is not None and (len(s)!=len(shape) or any(a is not None and a!=b for a,b in zip(shape,s))):bad.append(f'{f}:{k} shape {s} != {shape}')
    print('\n'.join(bad) if bad else 'deliverables match spec');sys.exit(1 if bad else 0)
if __name__=='__main__':main(sys.argv[1])

