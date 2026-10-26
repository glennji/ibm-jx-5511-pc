"""Clearance check: every pair of printed parts in their assembled positions,
and every hardware envelope against the case, rendered as OpenSCAD
intersections (see fitcheck.scad). Prints OVERLAP lines and clash volumes.

    python3 fitcheck.py
"""
import itertools
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor

import scadtools as S

MIN_VOL = 0.01   # mm^3; anything smaller is boolean noise at a shared face


def overlap(a, b, tmp):
    """volume of a ^ b in mm^3 (0 when OpenSCAD finds nothing)"""
    out = os.path.join(tmp, f"{abs(hash((a, b)))}.stl")
    try:
        S.openscad("fitcheck.scad", out, {"fit_a": a, "fit_b": b})
    except S.Empty:
        return 0.0
    return abs(S.volume(S.read_stl(out)[1]))


def shells(name, tmp):
    out = os.path.join(tmp, f"solid_{name}.stl")
    S.openscad("fitcheck.scad", out, {"fit_a": name, "fit_b": ""})
    return S.components(S.read_stl(out)[1])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        echo = os.path.join(tmp, "info.echo")
        S.openscad("fitcheck.scad", echo, {"fit_a": "info"})
        info = open(echo, encoding="utf-8").read()
        names = re.findall(r'"([^"]*)"', re.search(r"fit_solids = \[(.*?)\]", info).group(1))
        envs = re.findall(r'"([^"]*)"', re.search(r"envelopes = \[(.*?)\]", info).group(1))

        jobs = [(a, b) for a, b in itertools.combinations(names, 2)]
        jobs += [("parts", e) for e in envs]
        jobs.append(("floppy in A (147 deep)", "PSU 150 deep"))
        with ThreadPoolExecutor(os.cpu_count()) as ex:
            vols = dict(zip(jobs, ex.map(lambda j: overlap(*j, tmp), jobs)))
            comps = dict(zip(names, ex.map(lambda n: shells(n, tmp), names)))

    for a, b in itertools.combinations(names, 2):
        if vols[(a, b)] > MIN_VOL:
            print("OVERLAP", a, b, round(vols[(a, b)], 2))
    for e in envs:
        print(f"{e:34s} clash {round(vols[('parts', e)], 2)}")
    print("floppy vs PSU150", round(vols[("floppy in A (147 deep)", "PSU 150 deep")], 1))
    for line in info.splitlines():
        if line.startswith("ECHO:") and "fit_solids" not in line:
            print(line[len("ECHO: "):])
    print("components per part:", comps)


if __name__ == "__main__":
    main()
