"""
JX-style desktop case for a standard ATX motherboard + ATX PSU.
Printable on a 256 x 256 mm bed (every part <= 250 mm).

Coordinates (assembled case):
  X = width, left -> right as seen from the front   (0 .. W)
  Y = depth, front -> rear                           (0 .. D)
  Z = height, bottom of floor -> top                 (0 .. H)

Requires the `manifold3d` Python bindings. Run:  python3 jx_case.py
Writes one STL per part into ./stl and an assembly STL for previewing.

Hardware (see README.md for the full list): M3 heat-set inserts (M3 x 5.7),
M3 bolts + nuts, 9 x M3 10 mm female-female brass standoffs.
"""
import math
import os
import sys

import numpy as np
import manifold3d as m3
from manifold3d import Manifold as M, CrossSection as CS, OpType

m3.set_circular_segments(48)

# ---------------------------------------------------------------- parameters
W, D = 495.0, 324.0          # exterior width / depth
WALL_TOP = 162.0             # top of the walls (lid sits on this)
LID_T = 3.0                  # lid plate thickness
FLOOR_T = 5.0
SIDE_T = 3.0                 # left / right / rear wall
FRONT_T = 6.0                # front wall (thicker, carries the JX face details)
SPLIT_X = W / 2              # quadrant split lines
SPLIT_Y = D / 2

# Motherboard (ATX 305 x 244). Board coords: u along the rear edge from the
# slot-side edge, v from the rear edge toward the front.
BOARD_W, BOARD_D = 304.8, 243.84
BOARD_X0 = 15.0                       # case X of the slot-side board edge
INSERT_Y0, INSERT_Y1 = 316.8, 320.8   # rear inserts (slot + I/O panels) sit here
BOARD_REAR_Y = INSERT_Y0 - 1.65       # board rear edge 1.65 mm inside the panel
RING_H = 2.0                          # printed locating ring under each standoff
STANDOFF_H = 10.0                     # brass M3 F-F standoff
BOARD_BOTTOM = FLOOR_T + RING_H + STANDOFF_H
BOARD_TOP = BOARD_BOTTOM + 1.57

# ATX mounting holes (mm, board coords) A C F G H J K L M
ATX_HOLES = {
    "A": (16.69, 10.16), "C": (141.15, 10.16), "F": (298.63, 33.02),
    "G": (16.69, 165.10), "H": (141.15, 165.10), "J": (298.63, 165.10),
    "K": (16.69, 237.49), "L": (141.15, 237.49), "M": (298.63, 237.49),
}
# Rear I/O aperture (ATX: 158.75 x 44.45, bottom 3.81 below board top)
IO_U0 = 146.0                          # <- best estimate, verify with the fit-check template
IO_W, IO_H = 158.75, 44.45
# Expansion slots: bracket centre of the slot nearest the I/O, 0.8" pitch
SLOT7_U = 131.8                        # <- best estimate
SLOT_PITCH = 20.32
N_SLOTS = 7
SLOT_OPEN_W = 14.0
SLOT_OPEN_Z = (10.0, BOARD_TOP + 102.0)
RAIL_LEDGE_Z = BOARD_TOP + 108.0       # nominal bracket-flange rest, adjustable +-6

# PSU (standard ATX 150 x 86, 140-160 deep), rear face against the rear wall
PSU_X0 = 337.0
PSU_W, PSU_H = 150.0, 86.0
PSU_CX, PSU_CZ = PSU_X0 + PSU_W / 2, FLOOR_T + PSU_H / 2

# Rear opening for the two inserts (wall removed here, full height)
REAR_OPEN_X = (13.0, 326.0)

# JX front layout (traced from a photo, scaled to this case)
UNIT_GAP_Z = (91.0, 94.0)             # line between the two stacked units
BADGE_UP = (18.3, 146.0, 56.5, 157.3)  # x0, z0, x1, z1 badge recesses
BADGE_LO = (18.3, 71.3, 56.5, 83.0)
BAY_X = (368.7, 470.9)                 # real 3.5" bay behind drive "A"
BAY_Z = (49.4, 75.4)

FAN92 = 82.5      # hole spacing
FAN80 = 71.5

def board_xy(u, v):
    return BOARD_X0 + u, BOARD_REAR_Y - v

STANDOFFS = {k: board_xy(*uv) for k, uv in ATX_HOLES.items()}
SLOT_X = [BOARD_X0 + SLOT7_U - i * SLOT_PITCH for i in range(N_SLOTS)]
IO_X = (BOARD_X0 + IO_U0, BOARD_X0 + IO_U0 + IO_W)
IO_Z = (BOARD_TOP - 3.81, BOARD_TOP - 3.81 + IO_H)

# ---------------------------------------------------------------- helpers
def box(x0, y0, z0, x1, y1, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def cylz(x, y, z0, z1, d, fn=40, d2=None):
    r2 = (d2 if d2 is not None else d) / 2
    return M.cylinder(z1 - z0, d / 2, r2, fn).translate([x, y, z0])

def cylx(x0, x1, y, z, d, fn=32):
    return M.cylinder(x1 - x0, d / 2, d / 2, fn).rotate([0, 90, 0]).translate([x0, y, z])

def cyly(y0, y1, x, z, d, fn=32):
    return M.cylinder(y1 - y0, d / 2, d / 2, fn).rotate([-90, 0, 0]).translate([x, y0, z])

def hexx(x0, x1, y, z, af=5.7):          # nut trap, bolt axis along X
    r = af / math.sqrt(3)
    return M.cylinder(x1 - x0, r, r, 6).rotate([0, 0, 30]).rotate([0, 90, 0]).translate([x0, y, z])

def hexy(y0, y1, x, z, af=5.7):          # nut trap, bolt axis along Y
    r = af / math.sqrt(3)
    return M.cylinder(y1 - y0, r, r, 6).rotate([0, 0, 30]).rotate([-90, 0, 0]).translate([x, y0, z])

def union(parts):
    parts = [p for p in parts if p is not None]
    return M.batch_boolean(parts, OpType.Add) if parts else M()

def diff(a, cutters):
    cutters = [c for c in cutters if c is not None]
    return M.batch_boolean([a] + cutters, OpType.Subtract) if cutters else a

def gusset(x0, x1, y0, y1, z0, z1, wall):
    """Block on a wall face with a 45-degree support wedge underneath so it
    prints without supports. `wall` = side the wall is on: -x,+x,-y,+y."""
    blk = box(x0, y0, z0, x1, y1, z1)
    if wall in ("-x", "+x"):
        d = x1 - x0
        xs = x0 if wall == "-x" else x1 - 0.01
        foot = box(xs, y0, z0 - d, xs + 0.01, y1, z0)
    else:
        d = y1 - y0
        ys = y0 if wall == "-y" else y1 - 0.01
        foot = box(x0, ys, z0 - d, x1, ys + 0.01, z0)
    return M.batch_hull([blk, foot])

def extrude_poly(pts, z0, z1):
    return M.extrude(CS([pts]), z1 - z0).translate([0, 0, z0])

def bowtie(cx, cy, along, shrink=0.0, z0=0.0, z1=1.0):
    """Butterfly key outline; long axis across the seam."""
    L, Wd, w = 15.0 - shrink, 7.0 - shrink, 3.5 - shrink
    pts = [(-L, -Wd), (0, -w), (L, -Wd), (L, Wd), (0, w), (-L, Wd)]
    if along == "y":
        pts = [(b, a) for a, b in reversed(pts)]   # keep CCW winding
    pts = [(cx + a, cy + b) for a, b in pts]
    return extrude_poly(pts, z0, z1)

# ---------------------------------------------------------------- lower shell
def lower_shell():
    adds, cuts = [], []
    outer = box(0, 0, 0, W, D, WALL_TOP)
    cavity = box(SIDE_T, FRONT_T, FLOOR_T, W - SIDE_T, D - SIDE_T, WALL_TOP + 10)
    shell = diff(outer, [cavity])

    # --- standoff locating rings
    for (x, y) in STANDOFFS.values():
        adds.append(cylz(x, y, FLOOR_T - 0.01, FLOOR_T + RING_H, 9.0))

    # --- 3.5" bay cage behind drive "A" (lower unit, right drive)
    bx0, bx1 = BAY_X
    cage_y1 = 100.0
    sz0, sz1 = BAY_Z[0] - 4, BAY_Z[0]                                     # shelf
    adds.append(box(bx0 - 3, FRONT_T - 0.01, FLOOR_T - 0.01, bx0, cage_y1, BAY_Z[1] + 10))
    adds.append(box(bx1, FRONT_T - 0.01, FLOOR_T - 0.01, bx1 + 3, cage_y1, BAY_Z[1] + 10))
    adds.append(box(bx0, FRONT_T - 0.01, sz0, bx1, cage_y1, sz1))
    for x in np.linspace(bx0 + 22, bx1 - 22, 4):                          # shelf ribs
        adds.append(box(x - 1, FRONT_T - 0.01, FLOOR_T - 0.01, x + 1, cage_y1, sz0 + 0.01))
    for y in range(20, 95, 10):                                           # device screw holes
        cuts.append(cylx(bx0 - 4, bx0 + 0.5, y, BAY_Z[0] + 6.35, 3.4))
        cuts.append(cylx(bx1 - 0.5, bx1 + 4, y, BAY_Z[0] + 6.35, 3.4))

    # --- seam tabs (bolt + nut) on the front and side walls
    for zc in (28.0, 83.0, 105.0, 138.0):
        z0, z1 = zc - 8, zc + 8
        if zc != 105.0:
            # front wall, seam at SPLIT_X
            adds.append(gusset(SPLIT_X - 10, SPLIT_X + 10, FRONT_T - 0.01, FRONT_T + 8, z0, z1, "-y"))
            cuts.append(cylx(SPLIT_X - 11, SPLIT_X + 11, FRONT_T + 4, zc, 3.4))
            cuts.append(hexx(SPLIT_X + 6.5, SPLIT_X + 10.5, FRONT_T + 4, zc))
        # left + right walls, seam at SPLIT_Y (right side stays above the PSU)
        walls = []
        if zc != 105.0:
            walls.append((SIDE_T - 0.01, SIDE_T + 8, "-x"))
        if zc > 100:
            walls.append((W - SIDE_T - 8, W - SIDE_T + 0.01, "+x"))
        for xw0, xw1, side in walls:
            adds.append(gusset(xw0, xw1, SPLIT_Y - 10, SPLIT_Y + 10, z0, z1, side))
            xc = (xw0 + xw1) / 2
            cuts.append(cyly(SPLIT_Y - 11, SPLIT_Y + 11, xc, zc, 3.4))
            cuts.append(hexy(SPLIT_Y + 6.5, SPLIT_Y + 10.5, xc, zc))

    # --- lid bosses (heat-set inserts from the top)
    for b in lid_boss_list():
        x0, y0, x1, y1, side, hx, hy = b
        adds.append(gusset(x0, x1, y0, y1, WALL_TOP - 10, WALL_TOP, side))
        cuts.append(cylz(hx, hy, WALL_TOP - 7, WALL_TOP + 1, 4.0))

    # --- rear: big opening for the two inserts (wall removed full height)
    cuts.append(box(REAR_OPEN_X[0], D - SIDE_T - 1, FLOOR_T, REAR_OPEN_X[1], D + 1, WALL_TOP + 1))
    # insert fixing bolts through the columns either side
    for zc in (30.0, 90.0, 150.0):
        cuts.append(cyly(INSERT_Y0 - 1, D + 1, 8.5, zc, 3.4))
        cuts.append(cyly(INSERT_Y0 - 1, D + 1, 330.5, zc, 3.4))
    # PSU opening + screw holes (union of upright / flipped mounting patterns)
    cuts.append(box(PSU_CX - 62, D - SIDE_T - 1, PSU_CZ - 30, PSU_CX + 62, D + 1, PSU_CZ + 30))
    for sx in (-1, 1):
        for sz in (-1, 1):
            for (hx, hz) in ((69, 37), (69, 27), (45, 37)):
                cuts.append(cyly(D - SIDE_T - 1, D + 1, PSU_CX + sx * hx, PSU_CZ + sz * hz, 3.6))

    # --- floor
    for (x, y) in STANDOFFS.values():
        cuts.append(cylz(x, y, -1, FLOOR_T + RING_H + 1, 3.4))
        cuts.append(cylz(x, y, -1, 2.5, 6.6))              # M3 head counterbore underneath
    for xc in SLOT_X:                                        # bracket tab slots
        cuts.append(box(xc - 6, INSERT_Y0 - 5, -1, xc + 6, INSERT_Y0, FLOOR_T + 1))
    for x in np.arange(347, 480, 8):                         # PSU vent (fan-down option)
        cuts.append(box(x, 192, -1, x + 4, 306, FLOOR_T + 1))
    for x in (200.0, 290.0):                                 # I/O insert floor lip inserts
        cuts.append(cylz(x, INSERT_Y0 - 2.5, 0.8, FLOOR_T + 0.1, 4.0))
    for (x, y) in ((30, 30), (W - 30, 30), (30, D - 30), (W - 30, D - 30), (150, 205), (345, 125)):
        cuts.append(cylz(x, y, -0.1, 4.2, 4.0))             # feet (heat-set from below)
    for y in (40, 115, 215, 290):                            # butterfly keys, X seam
        cuts.append(bowtie(SPLIT_X, y, "x", 0, FLOOR_T - 3, FLOOR_T + 0.1))
    for x in (70, 200, 285, 380, 450):                       # butterfly keys, Y seam
        cuts.append(bowtie(x, SPLIT_Y, "y", 0, FLOOR_T - 3, FLOOR_T + 0.1))

    # --- corners + the line between the two stacked "units"
    c = 3.0
    cuts.append(extrude_poly([(-1, -1), (c, -1), (-1, c)], -1, WALL_TOP + 1))
    cuts.append(extrude_poly([(W + 1, -1), (W + 1, c), (W - c, -1)], -1, WALL_TOP + 1))
    c2 = 2.0
    cuts.append(extrude_poly([(-1, D + 1), (-1, D - c2), (c2, D + 1)], -1, WALL_TOP + 1))
    cuts.append(extrude_poly([(W + 1, D + 1), (W - c2, D + 1), (W + 1, D - c2)], -1, WALL_TOP + 1))
    gz0, gz1 = UNIT_GAP_Z
    cuts.append(box(-1, -1, gz0, W + 1, 2.0, gz1))                 # front
    cuts.append(box(-1, -1, gz0, 1.0, D + 1, gz1))                 # left side
    cuts.append(box(W - 1.0, -1, gz0, W + 1, D + 1, gz1))          # right side
    cuts.append(box(BAY_X[0] + 0.1, -1, BAY_Z[0], BAY_X[1] - 0.1, FRONT_T + 1, BAY_Z[1]))  # real 3.5" bay

    # --- left wall: two 92 mm intake fans aimed at the GPU
    for yc in (105.0, 230.0):
        zc = 90.0
        for y in np.arange(yc - 42, yc + 42, 6):
            dy = abs(y + 1.75 - yc)
            if dy > 43:
                continue
            hz = math.sqrt(44 ** 2 - dy ** 2)
            cuts.append(box(-1, y, zc - hz, SIDE_T + 1, y + 3.5, zc + hz))
        for sy in (-1, 1):
            for sz in (-1, 1):
                cuts.append(cylx(-1, SIDE_T + 1, yc + sy * FAN92 / 2, zc + sz * FAN92 / 2, 3.4))
    # right wall: vertical vent slots above the PSU / beside the CPU
    for y in np.arange(194, 290, 6):
        cuts.append(box(W - SIDE_T - 1, y, 100, W + 1, y + 3, 150))
    for y in np.arange(20, 140, 6):
        cuts.append(box(W - SIDE_T - 1, y, 30, W + 1, y + 3, 90))

    body = union([shell] + adds)
    body = diff(body, cuts)
    return front_relief(body)

def front_relief(body):
    """JX front, traced from a photo of a JX system unit with its expansion
    unit on top. Recess first, then raised details, then the fine cuts."""
    R = lambda x0, z0, x1, z1, d: box(x0, -1, z0, x1, d, z1)        # recess from the face, depth d
    U = lambda x0, z0, x1, z1, y: box(x0, y - 0.01, z0, x1, FRONT_T - 0.5, z1)  # raise back to face-y
    rec, raise_, fine = [], [], []
    # ---------------- upper unit (expansion unit)
    rec.append(R(*BADGE_UP, 1.5))
    # blank cover panel: outline groove only
    x0, z0, x1, z1 = 91.7, 113.6, 187.0, 158.2
    rec += [R(x0, z0, x1, z0 + 1.0, 0.8), R(x0, z1 - 1.0, x1, z1, 0.8),
            R(x0, z0, x0 + 1.0, z1, 0.8), R(x1 - 1.0, z0, x1, z1, 0.8)]
    # big drive bay recess with end blocks and a 5.25" drive face
    rec.append(R(221.6, 115.5, 487.7, 159.6, 3.5))
    raise_ += [U(224.0, 118.0, 261.0, 157.0, 2.0), U(448.5, 118.0, 485.5, 157.0, 2.0),
               U(264.0, 117.5, 445.5, 158.0, 2.6)]
    fine.append(R(268.0, 136.0, 439.0, 143.0, 4.6))                   # disk slot
    raise_.append(U(297.0, 143.5, 342.0, 156.0, 1.6))                  # door lever
    fine.append(cyly(-1, FRONT_T + 1, 412.0, 149.3, 3.2))              # LED (3 mm)
    # ---------------- lower unit (system unit)
    rec.append(R(*BADGE_LO, 1.5))
    # power switch housing + rectangular switch cut-out (13 x 19, e.g. KCD1)
    rec.append(R(19.0, 8.9, 57.0, 49.2, 1.5))
    rec.append(R(32.5, 9.8, 56.2, 48.4, 3.0))
    fine.append(box(45.0 - 6.6, -1, 35.0 - 9.6, 45.0 + 6.6, FRONT_T + 1, 35.0 + 9.6))
    # IR window -> power LED window (glue in smoked acrylic)
    fine.append(box(163.8, -1, 12.2, 187.7, FRONT_T + 1, 31.1))
    # drive / cartridge recess
    rec.append(R(221.6, 8.1, 487.7, 85.7, 2.0))
    # drive B (decorative)
    rec.append(R(223.2, 42.4, 348.1, 82.4, 3.5))
    fine.append(R(231.0, 67.6, 345.0, 77.1, 5.0))                      # slot
    raise_.append(U(322.0, 50.0, 344.0, 55.5, 2.0))                    # eject button
    fine.append(cyly(-1, FRONT_T + 1, 245.8, 51.4, 3.2))               # HDD LED
    # drive A frame around the real bay (opening cut in lower_shell)
    rec.append(R(356.1, 42.4, 483.4, 82.4, 3.5))
    # cartridge strip with two cartridge doors and the mode switch
    rec.append(R(224.0, 10.0, 484.5, 32.5, 3.5))
    raise_ += [U(266.7, 11.5, 344.0, 31.0, 2.5), U(364.0, 11.5, 437.0, 31.0, 2.5)]
    fine.append(R(455.0, 19.0, 471.0, 23.0, 5.0))                      # mode switch slot
    body = diff(body, rec)
    body = union([body] + raise_)
    return diff(body, fine)

def lid_boss_list():
    """(x0, y0, x1, y1, wall-side, hole_x, hole_y)"""
    out = []
    for y in (25.0, 140.0, 184.0, 300.0):
        out.append((SIDE_T - 0.01, y - 5, SIDE_T + 8, y + 5, "-x", SIDE_T + 4, y))
        out.append((W - SIDE_T - 8, y - 5, W - SIDE_T + 0.01, y + 5, "+x", W - SIDE_T - 4, y))
    for x in (25.0, 215.0, 280.0, 470.0):
        out.append((x - 5, FRONT_T - 0.01, x + 5, FRONT_T + 8, "-y", x, FRONT_T + 4))
    for x in (360.0, 465.0):
        out.append((x - 5, D - SIDE_T - 8, x + 5, D - SIDE_T + 0.01, "+y", x, D - SIDE_T - 4))
    return out

# ---------------------------------------------------------------- lid
def lid():
    z0, z1 = WALL_TOP, WALL_TOP + LID_T
    plate = M.batch_hull([box(0, 0, z0, W, D, z1 - 1), box(2, 2, z1 - 0.01, W - 2, D - 2, z1)])
    adds, cuts = [], []
    # locating lip just inside the walls / inserts
    lz0 = z0 - 6
    def lip_seg(x0, y0, x1, y1):
        adds.append(box(x0, y0, lz0, x1, y1, z0 + 0.01))
    g = 0.4
    lip_seg(SIDE_T + g, FRONT_T + g, W - SIDE_T - g, FRONT_T + g + 2)               # front
    lip_seg(SIDE_T + g, FRONT_T + g, SIDE_T + g + 2, INSERT_Y0 - g)                 # left
    lip_seg(W - SIDE_T - g - 2, FRONT_T + g, W - SIDE_T - g, D - SIDE_T - g)        # right
    lip_seg(336, D - SIDE_T - g - 2, W - SIDE_T - g, D - SIDE_T - g)                # rear (PSU part)
    lip_seg(SIDE_T + g, INSERT_Y0 - g - 2, 336, INSERT_Y0 - g)                      # rear (inserts)
    # seam ribs (bolted), the Y rib stops short of the GPU zone
    rz0 = z0 - 10
    adds.append(box(SPLIT_X - 4, FRONT_T + g, rz0, SPLIT_X + 4, 312, z0 + 0.01))
    adds.append(box(160, SPLIT_Y - 4, rz0, W - SIDE_T - g, SPLIT_Y + 4, z0 + 0.01))
    for y in (40.0, 120.0, 205.0, 290.0):
        cuts.append(cylx(SPLIT_X - 5, SPLIT_X + 5, y, z0 - 5, 3.4))
        cuts.append(hexx(SPLIT_X + 1.4, SPLIT_X + 4.1, y, z0 - 5))
    for x in (200.0, 300.0, 400.0, 470.0):
        cuts.append(cyly(SPLIT_Y - 5, SPLIT_Y + 5, x, z0 - 5, 3.4))
        cuts.append(hexy(SPLIT_Y + 1.4, SPLIT_Y + 4.1, x, z0 - 5))
    # clear the lip around the wall bosses + screw holes
    for b in lid_boss_list():
        x0, y0, x1, y1, side, hx, hy = b
        cuts.append(box(x0 - 0.6, y0 - 0.6, lz0 - 1, x1 + 0.6, y1 + 0.6, z0))
        cuts.append(cylz(hx, hy, z0 - 1, z1 + 1, 3.4))
        cuts.append(cylz(hx, hy, z1 - 1.7, z1 + 0.01, 3.4, d2=6.8))
    # vents: over the CPU and over the PSU
    for x in np.arange(168, 326, 7):
        if SPLIT_X - 7 < x < SPLIT_X + 4:
            continue
        cuts.append(box(x, 198, z0 + 0.2, x + 3.5, 300, z1 + 1))
    for x in np.arange(346, 482, 7):
        cuts.append(box(x, 192, z0 + 0.2, x + 3.5, 306, z1 + 1))
    # vent cuts must not cut the ribs: they start just above the rib tops
    body = union([plate] + adds)
    return diff(body, cuts)

# ---------------------------------------------------------------- rear inserts
INS_Z = (FLOOR_T, WALL_TOP)

def slot_insert():
    p = box(3.6, INSERT_Y0, INS_Z[0], 157.8, INSERT_Y1, INS_Z[1])
    cuts = []
    for xc in SLOT_X:
        cuts.append(box(xc - SLOT_OPEN_W / 2, INSERT_Y0 - 1, SLOT_OPEN_Z[0],
                        xc + SLOT_OPEN_W / 2, INSERT_Y1 + 1, SLOT_OPEN_Z[1]))
    for zc in (30.0, 90.0, 150.0):
        cuts.append(cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, 8.5, zc, 3.4))
    for x in RAIL_BOLT_X[:2]:
        cuts.append(cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, x, RAIL_LEDGE_Z + 12, 3.4))
    # a few vent slots above the rail
    return diff(p, cuts)

RAIL_BOLT_X = (60.0, 110.0, 180.0)

def io_insert():
    x0, x1 = 158.2, 335.0
    p = box(x0, INSERT_Y0, INS_Z[0], x1, INSERT_Y1, INS_Z[1])
    lip = box(170, INSERT_Y0 - 6, FLOOR_T, 320, INSERT_Y0 + 0.01, FLOOR_T + 3)
    body = union([p, lip])
    k = 0.13                                   # small oversize so the shield snaps in
    cuts = [box(IO_X[0] - k, INSERT_Y0 - 1, IO_Z[0] - k, IO_X[1] + k, INSERT_Y1 + 1, IO_Z[1] + k)]
    # thin the rim to 1.2 mm so a standard I/O shield can clip in (keep-out 2.5 mm)
    m = 3.0
    cuts.append(box(IO_X[0] - m, INSERT_Y0 - 1, IO_Z[0] - m, IO_X[1] + m, INSERT_Y1 - 1.2, IO_Z[1] + m))
    for x in (200.0, 290.0):
        cuts.append(cylz(x, INSERT_Y0 - 2.5, FLOOR_T - 1, FLOOR_T + 4, 3.4))
    for zc in (30.0, 90.0, 150.0):
        cuts.append(cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, 330.5, zc, 3.4))
    cuts.append(cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, RAIL_BOLT_X[2], RAIL_LEDGE_Z + 12, 3.4))
    # 80 mm exhaust fan above the I/O
    fx, fz = 240.0, 105.0
    for z in np.arange(fz - 37, fz + 37, 6):
        dz = abs(z + 1.75 - fz)
        hx = math.sqrt(max(38 ** 2 - dz ** 2, 0))
        if hx > 3:
            cuts.append(box(fx - hx, INSERT_Y0 - 1, z, fx + hx, INSERT_Y1 + 1, z + 3.5))
    for sx in (-1, 1):
        for sz in (-1, 1):
            cuts.append(cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, fx + sx * FAN80 / 2, fz + sz * FAN80 / 2, 3.4))
    return diff(body, cuts)

def bracket_rail():
    """Card-bracket screw rail. Bolts to both inserts through vertical slots so
    the ledge height can be set with a card fitted (+-6 mm). Also ties the two
    inserts together."""
    zl = RAIL_LEDGE_Z
    ledge = box(14, INSERT_Y0 - 10, zl - 4, 157, INSERT_Y0 - 0.2, zl)
    back = box(14, INSERT_Y0 - 4.2, zl - 4, 196, INSERT_Y0 - 0.2, zl + 22)
    body = union([ledge, back])
    cuts = []
    for x in RAIL_BOLT_X:
        cuts.append(M.batch_hull([cyly(INSERT_Y0 - 5, INSERT_Y0 + 1, x, zl + 6, 3.4),
                                  cyly(INSERT_Y0 - 5, INSERT_Y0 + 1, x, zl + 18, 3.4)]))
    for xc in SLOT_X:
        cuts.append(M.batch_hull([cylz(xc - 4, INSERT_Y0 - 6.5, zl - 5, zl + 1, 3.6),
                                  cylz(xc + 4, INSERT_Y0 - 6.5, zl - 5, zl + 1, 3.6)]))
    return diff(body, cuts)

# ---------------------------------------------------------------- small parts
def butterfly_key():
    return bowtie(0, 0, "x", 0.15, 0, 2.8)

def foot():
    f = cylz(0, 0, 0, 10, 30, fn=64, d2=26)
    return diff(f, [cylz(0, 0, -1, 11, 3.4), cylz(0, 0, -1, 6, 6.8)])

def badge_plate():
    w, h = BADGE_UP[2] - BADGE_UP[0] - 0.4, BADGE_UP[3] - BADGE_UP[1] - 0.4
    return box(0, 0, 0, w, h, 2.0)   # glue into the badge recess (1.5 deep), add your logo

def bay_blank():
    """JX-style face for drive A when the 3.5" bay is empty: plugs the opening
    flush with the drive recess (2.5 mm deep) and adds slot, LED and button."""
    w, h = BAY_X[1] - BAY_X[0] - 0.4, BAY_Z[1] - BAY_Z[0] - 0.4
    plate = box(0, 0, 0, w, h, 2.5)
    btn = box(w - 26, 2, 2.5 - 0.01, w - 6, 7, 4.0)        # eject button stands proud
    body = union([plate, btn])
    return diff(body, [box(6, h - 9, 1.2, w - 6, h - 3, 3), cylz(14, 6, 1.5, 3, 3.2)])

def fit_template(half):
    """1.2 mm flat template of the board: hole positions + I/O and slot marks.
    Lay it on your motherboard before printing anything big."""
    u0, u1 = (0.0, BOARD_W / 2 + 6) if half == 0 else (BOARD_W / 2 - 6, BOARD_W)
    plate = box(u0, 0, 0, u1, BOARD_D, 1.2)
    cuts = []
    for (u, v) in ATX_HOLES.values():
        cuts.append(cylz(u, v, -1, 2, 3.4))
    # lightening windows
    for (a0, a1) in ((u0 + 12, u1 - 12),):
        cuts.append(box(a0, 30, -1, a1, 140, 2))
        cuts.append(box(a0, 182, -1, a1, 225, 2))
    # rear-edge marks: I/O aperture edges and bracket centres (V notches)
    for u in (IO_U0, IO_U0 + IO_W) + tuple(SLOT7_U - i * SLOT_PITCH for i in range(N_SLOTS)):
        cuts.append(extrude_poly([(u - 2, -1), (u + 2, -1), (u, 4)], -1, 2))
    # half-overlap so the two halves can be taped together
    t = diff(plate, cuts)
    return t

# ---------------------------------------------------------------- output
def write_stl(man, path):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float32)[:, :3]
    f = np.asarray(mesh.tri_verts, dtype=np.int64)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    n = (n / ln).astype(np.float32)
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as fh:
        fh.write(b"JX-style ATX case".ljust(80, b" "))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(rec.tobytes())

def to_bed(man, rot=None):
    """Optionally rotate for printing, then drop onto the bed at the origin."""
    if rot is not None:
        man = man.rotate(rot)
    (x0, y0, z0, x1, y1, z1) = man.bounding_box()
    return man.translate([-x0, -y0, -z0])

def build(outdir="stl"):
    os.makedirs(outdir, exist_ok=True)
    print("building lower shell ...", flush=True)
    shell = lower_shell()
    print("building lid ...", flush=True)
    lidm = lid()
    sins, iins, rail = slot_insert(), io_insert(), bracket_rail()

    q = {  # quadrant boxes
        "front_left": (0, SPLIT_X, 0, SPLIT_Y),
        "front_right": (SPLIT_X, W, 0, SPLIT_Y),
        "rear_left": (0, SPLIT_X, SPLIT_Y, D),
        "rear_right": (SPLIT_X, W, SPLIT_Y, D),
    }
    parts = {}
    for name, (x0, x1, y0, y1) in q.items():
        parts[f"base_{name}"] = (shell ^ box(x0, y0, -10, x1, y1, 300), None)
        # lid tiles print upside down (top face on the bed)
        parts[f"lid_{name}"] = (lidm ^ box(x0, y0, -10, x1, y1, 300), [180, 0, 0])
    parts["rear_slot_panel"] = (sins, [-90, 0, 0])      # outer face down
    parts["rear_io_panel"] = (iins, [-90, 0, 0])        # outer face down (thin rim on top side)
    parts["bracket_rail"] = (rail, [-90, 0, 0])
    parts["butterfly_key_x9"] = (butterfly_key(), None)
    parts["foot_x6"] = (foot(), None)
    parts["badge_plate_x2"] = (badge_plate(), None)
    parts["drive_a_face"] = (bay_blank(), None)
    parts["fit_template_left"] = (fit_template(0), None)
    parts["fit_template_right"] = (fit_template(1), None)

    report = []
    for name, (man, rot) in parts.items():
        pm = to_bed(man, rot)
        bb = pm.bounding_box()
        size = (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2])
        write_stl(pm, os.path.join(outdir, f"{name}.stl"))
        report.append((name, size, man.volume() / 1000.0, pm.status(), man.genus()))
    # assembly for previews
    asm = union([shell, lidm, sins, iins, rail])
    write_stl(asm, os.path.join(outdir, "_assembly_preview.stl"))
    write_stl(union([shell, sins, iins, rail]), os.path.join(outdir, "_assembly_open_preview.stl"))
    return report

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "stl"
    rep = build(out)
    tot = 0
    print(f"{'part':28s} {'X':>7s} {'Y':>7s} {'Z':>7s}  vol(cm3)  status")
    for name, s, vol, st, g in rep:
        mult = 9 if "x9" in name else 6 if "x6" in name else 2 if "x2" in name else 1
        tot += vol * mult
        flag = "  <-- TOO BIG" if max(s[0], s[1]) > 250 or s[2] > 250 else ""
        print(f"{name:28s} {s[0]:7.1f} {s[1]:7.1f} {s[2]:7.1f}  {vol:8.1f}  {st}{flag}")
    print(f"total solid volume {tot:.0f} cm3")
