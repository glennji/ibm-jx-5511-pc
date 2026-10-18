"""Small numpy z-buffer renderer for previews (no OpenGL needed)."""
import sys
import numpy as np
from PIL import Image

import jx_case as J

def tris(man):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return v[f]

def look_at(eye, target, up=(0, 0, 1)):
    eye, target, up = map(np.asarray, (eye, target, up))
    f = target - eye; f = f / np.linalg.norm(f)
    s = np.cross(f, up); s /= np.linalg.norm(s)
    u = np.cross(s, f)
    return eye, s, u, f

def render(items, path, eye, target, fov=30, size=(1400, 900), bg=(246, 246, 244), depth_shade=0.0, crop=True):
    Wp, Hp = size
    eye, s, u, f = look_at(eye, target)
    focal = 0.5 * Hp / np.tan(np.radians(fov) / 2)
    zbuf = np.full((Hp, Wp), np.inf)
    col = np.zeros((Hp, Wp, 3)); col[:] = np.array(bg) / 255
    nbuf = np.zeros((Hp, Wp, 3))
    idbuf = np.full((Hp, Wp), -1, dtype=np.int32)
    L1 = np.array([0.45, -0.7, 0.85]); L1 /= np.linalg.norm(L1)
    L2 = np.array([-0.6, 0.4, 0.3]); L2 /= np.linalg.norm(L2)
    for pid, (man, color) in enumerate(items):
        t = tris(man)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        base = np.array(color)
        shade = 0.30 + 0.55 * np.clip(n @ L1, 0, 1) + 0.18 * np.clip(n @ L2, 0, 1)
        rel = t - eye
        cx = rel @ s; cy = rel @ u; cz = rel @ f
        sx = Wp / 2 + focal * cx / cz
        sy = Hp / 2 - focal * cy / cz
        for i in range(len(t)):
            x, y, z = sx[i], sy[i], cz[i]
            if (z <= 1).any():
                continue
            x0 = max(int(np.floor(x.min())), 0); x1 = min(int(np.ceil(x.max())), Wp - 1)
            y0 = max(int(np.floor(y.min())), 0); y1 = min(int(np.ceil(y.max())), Hp - 1)
            if x1 < x0 or y1 < y0:
                continue
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-9:
                continue
            px, py = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            a = ((y[1] - y[2]) * (px - x[2]) + (x[2] - x[1]) * (py - y[2])) / den
            b = ((y[2] - y[0]) * (px - x[2]) + (x[0] - x[2]) * (py - y[2])) / den
            c = 1 - a - b
            m = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
            if not m.any():
                continue
            iz = a / z[0] + b / z[1] + c / z[2]       # perspective-correct depth
            depth = 1.0 / iz
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = m & (depth < sub)
            if not upd.any():
                continue
            sub[upd] = depth[upd]
            col[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(base * shade[i], 0, 1)
            nbuf[y0:y1 + 1, x0:x1 + 1][upd] = n[i]
            idbuf[y0:y1 + 1, x0:x1 + 1][upd] = pid
    # outline pass: normal / depth / part discontinuities
    edge = np.zeros((Hp, Wp), bool)
    for dy, dx in ((0, 1), (1, 0)):
        n2 = np.roll(nbuf, (-dy, -dx), (0, 1)); z2 = np.roll(zbuf, (-dy, -dx), (0, 1))
        i2 = np.roll(idbuf, (-dy, -dx), (0, 1))
        both = np.isfinite(zbuf) & np.isfinite(z2)
        dn = np.where(both, 1 - (nbuf * n2).sum(2), 0)
        zz = np.where(both, np.abs(np.where(both, zbuf - z2, 0)) / np.where(both, zbuf, 1), 0)
        e = (dn > 0.15) | (np.abs(np.where(both, zbuf - z2, 0)) > 0.6) | (np.isfinite(zbuf) != np.isfinite(z2)) | ((idbuf != i2) & both)
        edge |= e
    if depth_shade:
        facing = (nbuf @ (-f)) > 0.95
        zmin = zbuf[facing].min() if facing.any() else 0
        k = np.clip(1 - depth_shade * (zbuf - zmin), 0.45, 1)
        col[facing] *= k[facing][:, None]
    col[edge] *= 0.35
    img = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))
    img = img.resize((Wp // 2 * 2 // 2, Hp // 2 * 2 // 2), Image.LANCZOS) if False else img
    if crop:
        a = np.asarray(img).astype(int); m = (np.abs(a - np.array(bg)).sum(2) > 6)
        ys, xs = np.where(m); pad = 30
        img = img.crop((max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, Wp), min(ys.max() + pad, Hp)))
    img.save(path)

GREY = (0.50, 0.50, 0.49); LIDC = (0.53, 0.53, 0.52); INS = (0.36, 0.36, 0.36)
ACC = (0.80, 0.60, 0.15); GREEN = (0.20, 0.50, 0.25); PSUC = (0.55, 0.55, 0.55); RED = (0.55, 0.12, 0.12)

if __name__ == "__main__":
    shell, lid = J.lower_shell(), J.lid()
    si, io, rail = J.slot_insert(), J.io_insert(), J.bracket_rail()
    B = J.box
    tgt = np.array([J.W / 2, J.D / 2, 70])
    which = sys.argv[1:] or ["front", "rear", "open", "exploded"]
    if "front" in which:
        render([(shell, GREY), (lid, LIDC), (si, INS), (io, INS)], "preview_front.png",
               eye=tgt + np.array([-520, -1050, 520]), target=tgt)
    if "flat" in which:
        t2 = np.array([J.W / 2, 0, (J.WALL_TOP + 3) / 2])
        render([(shell, GREY), (lid, LIDC), (si, INS), (io, INS), (J.box(J.BAY_X[0]+0.2, 2.5, J.BAY_Z[0]+0.2, J.BAY_X[1]-0.2, 5, J.BAY_Z[1]-0.2), INS)],
               "preview_front_flat.png", eye=t2 + np.array([0, -3000, 0]), target=t2, fov=7, size=(2000, 800), depth_shade=0.09)
    if "rear" in which:
        render([(shell, GREY), (lid, LIDC), (si, INS), (io, INS), (rail, ACC)], "preview_rear.png",
               eye=tgt + np.array([600, 1050, 420]), target=tgt)
    if "open" in which:
        board = B(J.BOARD_X0, J.BOARD_REAR_Y - J.BOARD_D, J.BOARD_BOTTOM, J.BOARD_X0 + J.BOARD_W, J.BOARD_REAR_Y, J.BOARD_TOP)
        psu = B(J.PSU_X0, 321 - 150, J.FLOOR_T, J.PSU_X0 + 150, 321, J.FLOOR_T + 86)
        gpu = B(J.SLOT_X[0] - 40, J.INSERT_Y0 - 280, J.BOARD_TOP + 2, J.SLOT_X[0] + 4, J.INSERT_Y0 - 1, J.BOARD_TOP + 120)
        render([(shell, GREY), (si, INS), (io, INS), (rail, ACC), (board, GREEN), (psu, PSUC), (gpu, RED)],
               "preview_open.png", eye=tgt + np.array([-300, -800, 950]), target=tgt)
    if "exploded" in which:
        q = {"fl": (0, J.SPLIT_X, 0, J.SPLIT_Y), "fr": (J.SPLIT_X, J.W, 0, J.SPLIT_Y),
             "rl": (0, J.SPLIT_X, J.SPLIT_Y, J.D), "rr": (J.SPLIT_X, J.W, J.SPLIT_Y, J.D)}
        off = {"fl": (-30, -30), "fr": (30, -30), "rl": (-30, 30), "rr": (30, 30)}
        items = []
        for k, (x0, x1, y0, y1) in q.items():
            dx, dy = off[k]
            items.append(((shell ^ B(x0, y0, -10, x1, y1, 300)).translate([dx, dy, 0]), GREY))
            items.append(((lid ^ B(x0, y0, -10, x1, y1, 300)).translate([dx, dy, 110]), LIDC))
        items += [(si.translate([0, 110, 0]), INS), (io.translate([0, 110, 0]), INS), (rail.translate([0, 75, 0]), ACC)]
        render(items, "preview_exploded.png", eye=tgt + np.array([-650, -1100, 800]), target=tgt + np.array([0, 0, 40]))
    print("ok")
