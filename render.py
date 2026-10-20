"""Small numpy z-buffer renderer for previews (no OpenGL needed)."""
import sys, math
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
    tgt = np.array([J.W / 2, J.D / 2, 80])
    cB, cA = J.bay_cage(J.BAY_B_X0), J.bay_cage(J.BAY_A_X0)
    bA = J.bay_blank(J.BAY_A_X0)
    shelf = J.dvd_shelf()
    cx, zb = J.ODD_CX, J.ODD_BOTTOM
    dvd = J.union([B(cx - 73.0, 13, zb, cx + 73.0, 190, zb + 41.3),
                   B(cx - 74.0, 1.6 + J.DVD_PLATE_T, J.ODD_CZ - 21.15, cx + 74.0, 13, J.ODD_CZ + 21.15)])
    usb = B(J.BAY_B_X0 + 0.3, 3.6, J.BAY_Z[0] + 0.05, J.BAY_B_X0 + 101.9, 60, J.BAY_Z[0] + 25.4)
    DVDC = (0.16, 0.16, 0.17); DEV = (0.22, 0.22, 0.24)
    fF, fT = J.dvd_fascia()
    inside = [(cB, INS), (cA, INS), (bA, GREY), (shelf, ACC), (dvd, DVDC), (usb, DEV), (fF, GREY), (fT, GREY)]
    which = sys.argv[1:] or ["front", "rear", "open", "exploded"]
    if "front" in which:
        render([(shell, GREY), (lid, LIDC), (si, INS), (io, INS)] + inside, "preview_front.png",
               eye=tgt + np.array([-520, -1050, 520]), target=tgt)
    if "flat" in which:
        t2 = np.array([J.W / 2, 0, (J.WALL_TOP + 3) / 2])
        render([(shell, GREY), (lid, LIDC), (si, INS), (io, INS)] + inside,
               "preview_front_flat.png", eye=t2 + np.array([0, -3000, 0]), target=t2, fov=7, size=(2000, 800), depth_shade=0.09)
    if "dvd" in which:
        t3 = np.array([cx, 0, J.ODD_CZ - 5])
        render([(shell, GREY), (lid, LIDC)] + inside, "preview_dvd_fascia.png",
               eye=t3 + np.array([-180, -900, 260]), target=t3, fov=17, size=(1600, 900), depth_shade=0.0)
    if "rear" in which:
        render([(shell, GREY), (lid, LIDC), (si, INS), (io, INS), (rail, ACC)], "preview_rear.png",
               eye=tgt + np.array([600, 1050, 420]), target=tgt)
    if "open" in which:
        board = B(J.BOARD_X0, J.BOARD_REAR_Y - J.BOARD_D, J.BOARD_BOTTOM, J.BOARD_X0 + J.BOARD_W, J.BOARD_REAR_Y, J.BOARD_TOP)
        psu = B(J.PSU_X0, 321 - 150, J.FLOOR_T, J.PSU_X0 + 150, 321, J.FLOOR_T + 86)
        gpu = B(J.SLOT_X[0] - 40, J.INSERT_Y0 - 280, J.BOARD_TOP + 2, J.SLOT_X[0] + 4, J.INSERT_Y0 - 1, J.BOARD_TOP + 120)
        render([(shell, GREY), (si, INS), (io, INS), (rail, ACC), (board, GREEN), (psu, PSUC), (gpu, RED)] + inside,
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

def power_views():
    """Close-up of the JX power slider: front, and a cutaway from behind."""
    B = J.box
    shell, lid = J.lower_shell(), J.lid()
    fr = J.power_frame()
    RED = (0.75, 0.12, 0.10); SW = (0.15, 0.15, 0.17)
    X = J.PSW_X
    sw = B(X + 12.4 - 9.9, J.PSW_BACK[0] - 6.5, 61.5, X + 12.4 + 9.9, J.PSW_BACK[0] - 0.1, 71.7)
    lever = B(X + 4.0, J.PSW_BACK[0] - 5.0, 59.6, X + 17.5, J.PSW_BACK[0] - 1.5, 60.4)
    zc = J.PSW_ON
    items = [(shell, GREY), (fr, ACC), (J.power_slider(zc), INS), (J.power_knob(zc), RED), (sw, SW), (lever, (0.7, 0.7, 0.7))]
    t = np.array([X + 10, 0, 45])
    render(items[:1] + items[3:4] + [(lid, LIDC)], "preview_power_front.png", eye=t + np.array([-120, -420, 90]), target=t, fov=22, size=(1400, 1000))
    cut = B(-5, -5, -5, 120, J.PSW_BACK[0] - 0.01, 100)
    items_c = [(m ^ cut, c) for m, c in items]
    t2 = np.array([X + 6, 8, 45])
    render(items_c, "preview_power_inside.png", eye=t2 + np.array([90, 380, 60]), target=t2, fov=24, size=(1400, 1000))

if __name__ == "__main__" and "power" in sys.argv:
    power_views()

def paddle_views():
    B = J.box
    shell, lid = J.lower_shell(), J.lid()
    fr = J.paddle_frame()
    RED = (0.75, 0.12, 0.10); SW = (0.15, 0.15, 0.17); MAG = (0.65, 0.65, 0.7)
    X = J.PSW_X
    sw = B(X - 2.2, J.PSW_SW_Y - 9.9, 8.6, X + 4.2, J.PSW_SW_Y + 9.9, 18.8)
    t = J.PSW_ON
    mags = [J.cylx(X + 6.0, X + 9.0, *J._pt(tt, J.PSW_MAG_R, 0), 8.0) for tt in (J.PSW_OFF, J.PSW_ON)]
    items = [(shell, GREY), (fr, ACC), (J.paddle_lever(t), INS), (J.paddle_head(t), RED), (sw, SW)] + [(m, MAG) for m in mags]
    tt = np.array([X + 10, 0, 40])
    render([(shell, GREY), (lid, LIDC), (J.paddle_head(t), RED)], "preview_power_front.png",
           eye=tt + np.array([-150, -400, 90]), target=tt + np.array([-6, 0, -4]), fov=16, size=(1400, 1000))
    cut = B(X - 3.15, -30, -5, X + 30, 60, 100)     # slice off the left cheek to show the inside
    items_c = [(m ^ cut, c) for m, c in items]
    t2 = np.array([X, 18, 33])
    render(items_c, "preview_power_inside.png", eye=t2 + np.array([-330, 40, 70]), target=t2, fov=24, size=(1400, 1000))

if __name__ == "__main__" and "paddle" in sys.argv:
    paddle_views()

def brs_views():
    B = J.box
    shell, lid = J.lower_shell(), J.lid()
    fr = J.paddle_frame()
    RED = (0.78, 0.13, 0.10); SW = (0.15, 0.15, 0.17); MAG = (0.65, 0.65, 0.7)
    X = J.PSW_X
    sw = B(X - 3.2, J.PSW_SW[0], J.PSW_SW[1], X + 3.2, J.PSW_SW[0] + 10.2, J.PSW_SW[2])
    r = math.hypot(*J.LEVER_MAG)
    mags = [J.cylx(X + 10.6, X + 13.6, *J._pt(t, r), 8.0) for t in (J.PSW_OFF, J.PSW_ON)]
    out = {}
    for nm, t in (("on", J.PSW_ON), ("off", J.PSW_OFF)):
        tt = np.array([X + 6, 0, 36])
        render([(shell, GREY), (lid, LIDC), (J.paddle_lever(t), RED)], f"preview_power_{nm}.png",
               eye=tt + np.array([-170, -330, 110]), target=tt, fov=19, size=(1200, 1000))
    items = [(shell, GREY), (fr, ACC), (J.paddle_lever(J.PSW_ON), RED), (sw, SW)] + [(m, MAG) for m in mags]
    cut = B(X - 10.3, -40, -5, X + 40, 60, 100)
    t2 = np.array([X, 20, 36])
    render([(m ^ cut, c) for m, c in items], "preview_power_inside.png",
           eye=t2 + np.array([-340, 30, 60]), target=t2, fov=24, size=(1200, 1000))

if __name__ == "__main__" and "brs" in sys.argv:
    import math
    brs_views()

def label_views():
    import math
    lid = J.lid()
    WHITE = (0.93, 0.93, 0.9); RED = (0.78, 0.13, 0.10)
    X = J.PSW_X
    lev = J.paddle_lever(J.PSW_ON)
    tt = np.array([X - 10, 0, 36])
    for st in J.LABEL_STYLES:
        shell = J.lower_shell(st)
        items = [(shell, GREY), (lev, RED)]
        if st != "BLANK":
            items.append((J.union(J.label_solids(st)), WHITE))
        render(items, f"preview_labels_{st}.png", eye=tt + np.array([-40, -420, 40]), target=tt, fov=10, size=(1000, 1000))

if __name__ == "__main__" and "labels" in sys.argv:
    label_views()
