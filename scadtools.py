"""Shared helpers for build.py, fitcheck.py and render.py: run OpenSCAD and
read binary STLs. Standard library only."""
import json
import os
import re
import struct
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OPENSCAD = os.environ.get("OPENSCAD", "openscad")
_seen = set()   # warnings already printed


class Empty(Exception):
    """OpenSCAD produced no geometry (e.g. an intersection with no overlap)."""


def scad_value(v):
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(scad_value(x) for x in v) + "]"
    return repr(v)


def openscad(src, out, defs=None, extra=()):
    """Render `src` to `out` (STL or PNG). Returns (stderr text, summary dict).
    Raises Empty if the result has no geometry, RuntimeError on other errors."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        summary_path = tf.name
    cmd = [OPENSCAD, "--backend=manifold", "--summary", "geometry", "--summary-file", summary_path]
    if out.endswith(".stl"):
        cmd += ["--export-format", "binstl"]
    for k, v in (defs or {}).items():
        cmd += ["-D", f"{k}={scad_value(v)}"]
    cmd += list(extra) + ["-o", out, src]
    try:
        p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        log = p.stderr
        if p.returncode != 0:
            if "top level object is empty" in log:
                raise Empty()
            raise RuntimeError(f"openscad failed ({' '.join(cmd)}):\n{log}")
        for line in log.splitlines():
            line = line.strip()
            if ("WARNING" in line or "ERROR" in line) and "Viewall and autocenter disabled" not in line:
                if line not in _seen:
                    _seen.add(line)
                    print(f"  {line}", flush=True)
        try:
            with open(summary_path) as fh:
                summary = json.load(fh)
        except (OSError, ValueError):
            summary = {}
        return log, summary
    finally:
        if os.path.exists(summary_path):
            os.unlink(summary_path)


# ---------------------------------------------------------------- binary STL
def read_stl(path):
    """-> (header bytes, list of triangles ((x,y,z),(x,y,z),(x,y,z)))"""
    with open(path, "rb") as fh:
        d = fh.read()
    n = struct.unpack_from("<I", d, 80)[0]
    if len(d) != 84 + 50 * n:
        raise ValueError(f"{path}: not a binary STL")
    tris = []
    for i in range(n):
        v = struct.unpack_from("<12f", d, 84 + 50 * i)
        tris.append((v[3:6], v[6:9], v[9:12]))
    return d[:80], tris


def write_stl(path, tris, header=b"JX-style ATX case"):
    out = bytearray(header.ljust(80, b" ")[:80])
    out += struct.pack("<I", len(tris))
    for a, b, c in tris:
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        ln = (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5 or 1.0
        out += struct.pack("<12fH", n[0] / ln, n[1] / ln, n[2] / ln, *a, *b, *c, 0)
    with open(path, "wb") as fh:
        fh.write(out)


def bbox(tris):
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def volume(tris):
    """mm^3, from the signed tetrahedra against the origin (closed mesh)"""
    v = 0.0
    for a, b, c in tris:
        v += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
              + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return v / 6.0


def translate(tris, off):
    dx, dy, dz = off
    return [tuple((p[0] + dx, p[1] + dy, p[2] + dz) for p in t) for t in tris]


def is_closed(tris):
    """every edge is shared by exactly two triangles, in opposite directions"""
    edges = {}
    for t in tris:
        k = [tuple(round(c, 4) for c in p) for p in t]
        for i in range(3):
            e = (k[i], k[(i + 1) % 3])
            edges[e] = edges.get(e, 0) + 1
    return all(n == 1 and edges.get((b, a)) == 1 for (a, b), n in edges.items())


def components(tris):
    """number of separate shells (triangles joined through shared vertices)"""
    parent = {}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for t in tris:
        keys = [tuple(round(c, 4) for c in p) for p in t]
        for k in keys:
            parent.setdefault(k, k)
        r0 = find(keys[0])
        for k in keys[1:]:
            r = find(k)
            if r != r0:
                parent[r] = r0
    return len({find(k) for k in parent})


def part_names(scad="jx_case.scad"):
    """The `part` choices listed on the Customizer line of jx_case.scad."""
    with open(os.path.join(HERE, scad), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r'\s*part\s*=\s*"[^"]*"\s*;\s*//\s*\[(.*)\]', line)
            if m:
                return [p.strip() for p in m.group(1).split(",")]
    raise SystemExit(f"no part list found in {scad}")
