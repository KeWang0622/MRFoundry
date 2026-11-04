"""Verbatim statistical helpers from the frozen offline analysis source.

No source records are bundled here and no computation runs on import.
Original boot input fields: family, model, A (no skills), S (with skills).
Private Hard task identities and per-task records are not distributed.
This is archived implementation evidence, not a newly run analysis.
"""
import collections
import math
import random

def mcn(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def boot(Q, n=4000, seed=0):
    rng = random.Random(seed)
    F = sorted({p['family'] for p in Q}); M = sorted({p['model'] for p in Q})
    cell = collections.defaultdict(list)
    for p in Q:
        cell[(p['family'], p['model'])].append(p['S'] - p['A'])
    ds = []
    for _ in range(n):
        fs = [rng.choice(F) for _ in F]; ms = [rng.choice(M) for _ in M]
        v = [x for f in fs for m in ms for x in cell.get((f, m), [])]
        if v:
            ds.append(sum(v) / len(v))
    ds.sort()
    return [ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds)) - 1]]
