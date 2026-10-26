"""Render every printable part of jx_case.scad into ./stl (one OpenSCAD run per
part, in parallel), drop each onto the bed, and print a size / volume report.

    python3 build.py [outdir] [part ...]

Needs OpenSCAD 2025 or later on the PATH (or set OPENSCAD=/path/to/openscad).
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import scadtools as S

BED = 250.0
# these keep the case coordinates of their base, so each label inlay loads onto
# its base as one two-colour object
PAIRED = {"labels_JP_inlay": "base_front_left_JP", "labels_EN_inlay": "base_front_left_EN"}
ASSEMBLIES = {"assembly": "_assembly_preview", "assembly_open": "_assembly_open_preview"}


def multiplier(name):
    for suffix, n in (("_x9", 9), ("_x6", 6), ("_x2", 2)):
        if name.endswith(suffix):
            return n
    return 1


# parts that carry the switch labels: a fallback font can lack the glyphs and
# cut "missing glyph" boxes into the face, so these are not written without it
LABEL_PARTS = {"base_front_left_JP", "base_front_left_EN", "labels_JP_inlay", "labels_EN_inlay"}
FONT_MISSING = "not found, labels use a fallback font"


def render(name, outdir):
    path = os.path.join(outdir, ASSEMBLIES.get(name, name) + ".stl")
    log, _ = S.openscad("jx_case.scad", path, {"part": name})
    if name in LABEL_PARTS and FONT_MISSING in log:
        os.unlink(path)
        return name, None
    return name, path


def main():
    args = sys.argv[1:]
    outdir = args.pop(0) if args and not args[0] in S.part_names() else "stl"
    names = args or [p for p in S.part_names() if not p.startswith("asm_")]
    os.makedirs(outdir, exist_ok=True)
    print(f"rendering {len(names)} parts into {outdir}/ ...", flush=True)
    with ThreadPoolExecutor(os.cpu_count()) as ex:
        done = dict(ex.map(lambda n: render(n, outdir), names))
    skipped = sorted(n for n, p in done.items() if p is None)
    done = {n: p for n, p in done.items() if p is not None}
    names = [n for n in names if n in done]

    # drop onto the bed at the origin; paired inlays move with their base
    offsets = {}
    for name, path in done.items():
        if name in ASSEMBLIES or name in PAIRED:
            continue
        tris = S.read_stl(path)[1]
        b = S.bbox(tris)
        offsets[name] = (-b[0], -b[1], -b[2])
        S.write_stl(path, S.translate(tris, offsets[name]))
    for name, base in PAIRED.items():
        if name in done:
            if base not in offsets:
                raise SystemExit(f"{name} needs {base} in the same run (and its label font)")
            path = done[name]
            S.write_stl(path, S.translate(S.read_stl(path)[1], offsets[base]))

    total = 0.0
    print(f"{'part':28s} {'X':>7s} {'Y':>7s} {'Z':>7s}  vol(cm3)  mesh")
    for name in names:
        if name in ASSEMBLIES:
            continue
        tris = S.read_stl(done[name])[1]
        b = S.bbox(tris)
        size = (b[3] - b[0], b[4] - b[1], b[5] - b[2])
        vol = S.volume(tris) / 1000.0
        total += vol * multiplier(name)
        flag = "  <-- TOO BIG" if max(size) > BED else ""
        n = S.components(tris)
        mesh = ("closed" if S.is_closed(tris) else "OPEN") + (f", {n} shells" if n > 1 else "")
        print(f"{name:28s} {size[0]:7.1f} {size[1]:7.1f} {size[2]:7.1f}  {vol:8.2f}  {mesh}{flag}")
    print(f"total solid volume {total:.0f} cm3")
    if skipped:
        print(f"\nNOT WRITTEN (label font missing, see the warning above): {', '.join(skipped)}\n"
              "Install the font (IPA Gothic: `brew install --cask font-ipafont`), or set\n"
              "LABEL_FONT / LABEL_FONT_EN in jx_case.scad to a font you have.")
        sys.exit(1)


if __name__ == "__main__":
    main()
