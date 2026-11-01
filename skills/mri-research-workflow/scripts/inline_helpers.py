#!/usr/bin/env python3
"""Copy tested MRFoundry helper functions into a standalone entrypoint (standard library only).

Tasks often require ONE self-contained script. Copy the tested helpers instead of retyping them (retyped copies
carried silent bugs in evaluation runs: a wrong acceleration factor, a conjugated covariance):

  python inline_helpers.py MODULE.py func1 func2 [CONSTANT ...] --into my_entrypoint.py
  python inline_helpers.py MODULE.py func1 ... > helpers_block.py      (print instead)

The block contains the module's imports, the module-level constants the functions use and the functions with
every helper they call (transitively), between '# >>> MRFoundry helpers' and '# <<< MRFoundry helpers'. With
--into, an existing block is replaced; otherwise the block goes after the last top-level import of the file.
Run the entrypoint once from a clean folder afterwards (finish_check.py --rerun does this).
"""
import ast, sys
from pathlib import Path

START, END = "# >>> MRFoundry helpers", "# <<< MRFoundry helpers"


def collect(module_path, names):
    src = Path(module_path).read_text(); tree = ast.parse(src); lines = src.splitlines()
    defs, consts, imports = {}, {}, []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defs[node.name] = node
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = node
    missing = [n for n in names if n not in defs and n not in consts]
    if missing:
        raise SystemExit(f"not defined at top level of {module_path}: {missing} (see --api)")
    used_consts = {n for n in names if n in consts}
    need, todo = [], [n for n in names if n in defs]
    while todo:
        n = todo.pop()
        if n in need:
            continue
        need.append(n)
        for sub in ast.walk(defs[n]):
            if isinstance(sub, ast.Name):
                if sub.id in defs and sub.id not in need:
                    todo.append(sub.id)
                elif sub.id in consts:
                    used_consts.add(sub.id)
    # constants may reference other constants
    changed = True
    while changed:
        changed = False
        for c in list(used_consts):
            for sub in ast.walk(consts[c]):
                if isinstance(sub, ast.Name) and sub.id in consts and sub.id not in used_consts:
                    used_consts.add(sub.id); changed = True
    seg = lambda node: "\n".join(lines[(node.decorator_list[0].lineno if getattr(node, 'decorator_list', None) else node.lineno) - 1:node.end_lineno])
    order = sorted(need, key=lambda n: defs[n].lineno)
    cnodes = sorted({id(consts[c]): consts[c] for c in used_consts}.values(), key=lambda n: n.lineno)
    out = [START, f"# Copied unchanged from MRFoundry {Path(module_path).name} (tested there): {', '.join(names)}"]
    out += [seg(n) for n in imports] + [seg(n) for n in cnodes] + [""]
    for n in order:
        out += [seg(defs[n]), ""]
    out.append(END)
    return "\n".join(out) + "\n"


def insert(block, target):
    p = Path(target); text = p.read_text() if p.exists() else ""
    if START in text and END in text:
        a = text.index(START); b = text.index(END) + len(END)
        new = text[:a] + block.rstrip("\n") + text[b:]
    else:
        tree = ast.parse(text) if text.strip() else None
        last = 0
        if tree is not None:
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last = node.end_lineno
                elif isinstance(node, ast.Expr) and isinstance(getattr(node, 'value', None), ast.Constant) and last == 0:
                    last = node.end_lineno
                elif not isinstance(node, (ast.Import, ast.ImportFrom)):
                    if last:
                        break
        lines = text.splitlines()
        new = "\n".join(lines[:last] + ["", block.rstrip("\n"), ""] + lines[last:]) + "\n"
    p.write_text(new)
    ast.parse(new)
    return str(p)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    into = None
    if "--into" in argv:
        i = argv.index("--into"); into = argv[i + 1]; del argv[i:i + 2]
    block = collect(argv[0], argv[1:])
    if into:
        print(f"inserted {len(block.splitlines())} lines into {insert(block, into)}")
    else:
        sys.stdout.write(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())

