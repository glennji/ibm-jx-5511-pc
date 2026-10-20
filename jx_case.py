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
WALL_TOP = 196.0             # top of the walls (lid sits on this); 199 overall = JX photo ratio
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

# JX front layout. Features are traced in pixels from a photo of a JX (system
# unit with the expansion unit on top) and mapped uniformly onto the front.
PHOTO_X0, PHOTO_X1, PHOTO_Y0 = 39.0, 1561.0, 69.0   # case left/right/top edges in the photo
PX = W / (PHOTO_X1 - PHOTO_X0)                       # mm per photo pixel
H_TOTAL = WALL_TOP + LID_T

def P(x0, y0, x1, y1):
    """photo pixel box -> (x0, z0, x1, z1) on the front face (mm)"""
    return ((x0 - PHOTO_X0) * PX, H_TOTAL - (y1 - PHOTO_Y0) * PX,
            (x1 - PHOTO_X0) * PX, H_TOTAL - (y0 - PHOTO_Y0) * PX)

GROOVE_Z = (107.4, 111.4)              # line between the two "units" (photo rows 340-349)
GROOVE_D = 4.0                         # groove depth (walls are thickened behind it)
BADGE_UP = P(93, 102, 210, 145)
BADGE_LO = P(93, 377, 210, 420)
DRIVE_B_FRAME = P(712, 380, 1098, 528)
DRIVE_A_FRAME = P(1108, 380, 1500, 528)
UPPER_FACE = P(832, 105, 1380, 255)    # 5.25" drive face in the upper unit

# Functional 3.5" bays (drive B = USB panel, drive A = floppy / card reader)
BAY_W, BAY_H = 102.2, 26.0
BAY_Z = (DRIVE_B_FRAME[3] - 9.0 - BAY_H, DRIVE_B_FRAME[3] - 9.0)
BAY_B_X0 = (DRIVE_B_FRAME[0] + DRIVE_B_FRAME[2]) / 2 - BAY_W / 2
BAY_A_X0 = (DRIVE_A_FRAME[0] + DRIVE_A_FRAME[2]) / 2 - BAY_W / 2
BAY_X = (BAY_A_X0, BAY_A_X0 + BAY_W)   # (kept for the renderer)

# Functional 5.25" bay for an optical drive (bezel 148 x 42.3, body 146.05 x 41.3)
ODD_CX = (UPPER_FACE[0] + UPPER_FACE[2]) / 2
ODD_CZ = (UPPER_FACE[1] + UPPER_FACE[3]) / 2
ODD_OPEN = (ODD_CX - 74.3, ODD_CZ - 21.45, ODD_CX + 74.3, ODD_CZ + 21.45)
ODD_BOTTOM = ODD_CZ - 41.3 / 2         # drive body bottom = shelf top
SHELF_T = 5.0
LEDGE_TOP = ODD_BOTTOM - SHELF_T

# JX-style power paddle: a red paddle tilting on an axle behind the switch channel.
#   切 OFF (tilted down) and 入 ON (tilted up) are held by magnets;
#   START (pushed further up) presses a microswitch and springs back to 入.
PSW_X = 44.2                           # paddle centre (middle of the JX switch channel)
PSW_PIVOT = (11.5, 35.0)               # axle (y, z), axis along X
PSW_OFF, PSW_ON, PSW_START = -25.0, 25.0, 36.0     # paddle angles (deg, + = up)
PSW_STOPS = (-28.0, 37.0)              # slot ends act as hard stops
PSW_EARS = ((-12.6, 13.5), (-12.6, 55.0), (14.7, 13.5), (14.7, 55.0))  # rel. to PSW_X, abs z
LABEL_FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

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

    # --- bosses for the power-slider frame (heat-set inserts)
    for (ex, ez) in PSW_EARS:                      # power-paddle frame bosses
        adds.append(cyly(FRONT_T - 0.01, FRONT_T + 2.0, PSW_X + ex, ez, 9.0))
        cuts.append(cyly(FRONT_T - 4.0, FRONT_T + 2.1, PSW_X + ex, ez, 4.0))

    # --- groove backing bands (the unit groove is deeper than the walls)
    bz0, bz1 = GROOVE_Z[0] - 2, GROOVE_Z[1] + 2
    adds.append(gusset(SIDE_T, W - SIDE_T, FRONT_T - 0.01, FRONT_T + 4, bz0, bz1, "-y"))
    adds.append(gusset(SIDE_T - 0.01, SIDE_T + 4.2, FRONT_T, D - SIDE_T + 0.01, bz0, bz1, "-x"))
    adds.append(gusset(W - SIDE_T - 4, W - SIDE_T + 0.01, FRONT_T, D - SIDE_T + 0.01, bz0, bz1, "+x"))

    # --- ledges carrying the optical-drive shelf (front-right quadrant)
    adds.append(gusset(285, W - SIDE_T, FRONT_T - 0.01, FRONT_T + 14, LEDGE_TOP - 8, LEDGE_TOP, "-y"))
    adds.append(gusset(W - SIDE_T - 8, W - SIDE_T + 0.01, 20, 146, LEDGE_TOP - 8, LEDGE_TOP, "+x"))
    for (x, y) in SHELF_INSERTS:
        cuts.append(cylz(x, y, LEDGE_TOP - 6, LEDGE_TOP + 0.1, 4.0))

    # --- seam tabs (bolt + nut) on the front and side walls
    def tab_x(zc):      # front wall, seam at SPLIT_X
        adds.append(gusset(SPLIT_X - 10, SPLIT_X + 10, FRONT_T - 0.01, FRONT_T + 8, zc - 8, zc + 8, "-y"))
        cuts.append(cylx(SPLIT_X - 11, SPLIT_X + 11, FRONT_T + 4, zc, 3.4))
        cuts.append(hexx(SPLIT_X + 6.5, SPLIT_X + 10.5, FRONT_T + 4, zc))
    def tab_y(zc, left):  # side walls, seam at SPLIT_Y
        xw0, xw1, side = ((SIDE_T - 0.01, SIDE_T + 8, "-x") if left else
                          (W - SIDE_T - 8, W - SIDE_T + 0.01, "+x"))
        adds.append(gusset(xw0, xw1, SPLIT_Y - 10, SPLIT_Y + 10, zc - 8, zc + 8, side))
        xc = (xw0 + xw1) / 2
        cuts.append(cyly(SPLIT_Y - 11, SPLIT_Y + 11, xc, zc, 3.4))
        cuts.append(hexy(SPLIT_Y + 6.5, SPLIT_Y + 10.5, xc, zc))
    for zc in (28.0, 106.0, 130.0, 165.0):
        tab_x(zc)
        tab_y(zc, True)
    for zc in (130.0, 165.0):          # right side: above the PSU only
        tab_y(zc, False)

    # --- lid bosses (heat-set inserts from the top)
    for b in lid_boss_list():
        x0, y0, x1, y1, side, hx, hy = b
        adds.append(gusset(x0, x1, y0, y1, WALL_TOP - 10, WALL_TOP, side))
        cuts.append(cylz(hx, hy, WALL_TOP - 7, WALL_TOP + 1, 4.0))

    # --- rear: big opening for the two inserts (wall removed full height)
    cuts.append(box(REAR_OPEN_X[0], D - SIDE_T - 1, FLOOR_T, REAR_OPEN_X[1], D + 1, WALL_TOP + 1))
    # insert fixing bolts through the columns either side
    for zc in INS_BOLT_Z:
        cuts.append(cyly(INSERT_Y0 - 1, D + 1, 10.2, zc, 3.4))
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
    for x0 in (BAY_B_X0, BAY_A_X0):                          # 3.5" bay cage inserts
        for x in (x0 - 7.5, x0 + BAY_W + 7.5):
            for y in CAGE_HOLE_Y:
                cuts.append(cylz(x, y, FLOOR_T - 4.5, FLOOR_T + 0.1, 4.0))
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
    gz0, gz1 = GROOVE_Z
    cuts.append(box(-1, -1, gz0, W + 1, GROOVE_D, gz1))                  # front
    cuts.append(box(-1, -1, gz0, GROOVE_D, D + 1, gz1))                  # left side
    cuts.append(box(W - GROOVE_D, -1, gz0, W + 1, D + 1, gz1))           # right side

    # --- left wall: two 92 mm intake fans aimed at the GPU
    for yc in (105.0, 230.0):
        zc = 55.0
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
        cuts.append(box(W - SIDE_T - 1, y, 117, W + 1, y + 3, 172))
    for y in np.arange(20, 140, 6):
        cuts.append(box(W - SIDE_T - 1, y, 30, W + 1, y + 3, 90))

    body = union([shell] + adds)
    body = diff(body, cuts)
    return front_relief(body)

def front_relief(body):
    """JX front, traced from a photo of a JX system unit with its expansion
    unit on top. Recess first, then raised details, then the cuts through."""
    def R(b, d):            # recess box b=(x0,z0,x1,z1) to depth d
        return box(b[0], -1, b[1], b[2], d, b[3])
    def U(b, y):            # raise inside a recess back up to face-y
        return box(b[0], y - 0.01, b[1], b[2], FRONT_T - 0.5, b[3])
    def thru(b):
        return box(b[0], -1, b[1], b[2], FRONT_T + 1, b[3])
    rec, raise_, fine = [], [], []
    # ---------------- upper unit (expansion unit)
    rec.append(R(BADGE_UP, 1.5))
    x0, z0, x1, z1 = P(316, 100, 603, 264)            # blank cover panel: outline groove
    rec += [R((x0, z0, x1, z0 + 1.0), 0.8), R((x0, z1 - 1.0, x1, z1), 0.8),
            R((x0, z0, x0 + 1.0, z1), 0.8), R((x1 - 1.0, z0, x1, z1), 0.8)]
    rec.append(R(P(706, 95, 1507, 258), 3.5))          # drive bay recess
    raise_ += [U(P(712, 105, 826, 255), 1.5), U(P(1388, 105, 1500, 255), 1.5),  # end blocks
               U(UPPER_FACE, 0.9)]                     # drive face, framing the optical drive
    fine.append(thru(ODD_OPEN))                        # 5.25" optical drive bezel opening
    # ---------------- lower unit (system unit)
    rec.append(R(BADGE_LO, 1.5))
    rec.append(R(P(95, 503, 212, 652), 1.5))           # power switch housing
    rec.append(R(P(140, 505, 210, 650), 3.0))          # switch channel
    fine.append(paddle_slot())                         # power paddle slot
    for ch, (px, py) in (("入", (115, 525)), ("切", (115, 578))):  # raised labels, as on the JX
        lx, lz = (px - PHOTO_X0) * PX, H_TOTAL - (py - PHOTO_Y0) * PX
        raise_.append(glyph(ch, lx, lz, 4.6, 1.5, 0.5))
    fine.append(thru(P(532, 569, 606, 640)))           # IR window -> power LED window
    rec.append(R(P(706, 372, 1507, 650), 2.0))         # drive / cartridge recess
    rec.append(R(DRIVE_B_FRAME, 3.5))
    rec.append(R(DRIVE_A_FRAME, 3.5))
    for x0 in (BAY_B_X0, BAY_A_X0):                     # functional 3.5" bays
        fine.append(thru((x0, BAY_Z[0], x0 + BAY_W, BAY_Z[1])))
    for (lx, lz) in ((DRIVE_B_FRAME[0] + 12, BAY_Z[0] - 6.5), (DRIVE_A_FRAME[0] + 12, BAY_Z[0] - 6.5)):
        fine.append(cyly(-1, FRONT_T + 1, lx, lz, 3.2))   # 3 mm LEDs (HDD / spare)
    rec.append(R(P(712, 563, 1500, 645), 3.5))         # cartridge strip
    raise_ += [U(P(852, 572, 1072, 637), 2.5), U(P(1135, 572, 1355, 637), 2.5)]  # cartridge doors
    fine.append(R(P(1400, 598, 1450, 612), 5.0))       # mode switch slot
    body = diff(body, rec)
    body = union([body] + raise_)
    return diff(body, fine)

def lid_boss_list():
    """(x0, y0, x1, y1, wall-side, hole_x, hole_y)"""
    out = []
    for y in (25.0, 140.0, 184.0, 300.0):
        out.append((SIDE_T - 0.01, y - 5, SIDE_T + 8, y + 5, "-x", SIDE_T + 4, y))
        out.append((W - SIDE_T - 8, y - 5, W - SIDE_T + 0.01, y + 5, "+x", W - SIDE_T - 4, y))
    for x in (25.0, 200.0, 445.0, 475.0):
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
    lip_seg(SIDE_T + 4.2 + g, FRONT_T + g, SIDE_T + 4.2 + g + 2, INSERT_Y0 - g)     # left (inside band)
    lip_seg(W - SIDE_T - g - 2, FRONT_T + g, W - SIDE_T - g, D - SIDE_T - g)        # right
    lip_seg(336, D - SIDE_T - g - 2, W - SIDE_T - g, D - SIDE_T - g)                # rear (PSU part)
    lip_seg(SIDE_T + g, INSERT_Y0 - g - 2, 336, INSERT_Y0 - g)                      # rear (inserts)
    # seam ribs (bolted), the Y rib stops short of the GPU zone
    rz0 = z0 - 8
    adds.append(box(SPLIT_X - 4, FRONT_T + g, rz0, SPLIT_X + 4, 312, z0 + 0.01))
    adds.append(box(160, SPLIT_Y - 4, rz0, W - SIDE_T - g, SPLIT_Y + 4, z0 + 0.01))
    for y in (40.0, 120.0, 205.0, 290.0):
        cuts.append(cylx(SPLIT_X - 5, SPLIT_X + 5, y, z0 - 4, 3.4))
        cuts.append(hexx(SPLIT_X + 1.4, SPLIT_X + 4.1, y, z0 - 4))
    for x in (200.0, 300.0, 400.0, 470.0):
        cuts.append(cyly(SPLIT_Y - 5, SPLIT_Y + 5, x, z0 - 4, 3.4))
        cuts.append(hexy(SPLIT_Y + 1.4, SPLIT_Y + 4.1, x, z0 - 4))
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
INS_BOLT_Z = (30.0, 100.0, 175.0)

def slot_insert():
    p = box(7.6, INSERT_Y0, INS_Z[0], 157.8, INSERT_Y1, INS_Z[1])
    cuts = []
    for xc in SLOT_X:
        cuts.append(box(xc - SLOT_OPEN_W / 2, INSERT_Y0 - 1, SLOT_OPEN_Z[0],
                        xc + SLOT_OPEN_W / 2, INSERT_Y1 + 1, SLOT_OPEN_Z[1]))
    for zc in INS_BOLT_Z:
        cuts.append(cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, 10.2, zc, 3.4))
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
    for zc in INS_BOLT_Z:
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

CAGE_Y0 = FRONT_T + 0.5
CAGE_HOLE_Y = (CAGE_Y0 + 8.5, CAGE_Y0 + 48.5)
SHELF_INSERTS = ((300.0, FRONT_T + 11.5), (400.0, FRONT_T + 11.5), (462.0, FRONT_T + 6.0),
                 (W - SIDE_T - 4, 40.0), (W - SIDE_T - 4, 95.0), (W - SIDE_T - 4, 140.0))

def bay_cage(x0):
    """Removable 3.5" bay cage, screws to the floor behind a bay opening.
    Takes any 3.5" device (USB panel, floppy, card reader) via side slots.
    The rear 36 mm is raised so it can overhang the motherboard's front edge."""
    x1 = x0 + BAY_W
    y0, top, zlow = CAGE_Y0, BAY_Z[1] + 4, 50.0
    parts, cuts = [], []
    for wx0 in (x0 - 3, x1):
        parts.append(box(wx0, y0, FLOOR_T, wx0 + 3, y0 + 58, top))
        parts.append(box(wx0, y0 + 57.9, zlow, wx0 + 3, y0 + 94, top))
    parts.append(box(x0 - 0.01, FRONT_T + 6, BAY_Z[0] - 4, x1 + 0.01, y0 + 94, BAY_Z[0]))   # shelf
    parts.append(box(x0 - 12, y0, FLOOR_T, x0 - 2.99, y0 + 58, FLOOR_T + 3))                 # flanges
    parts.append(box(x1 + 2.99, y0, FLOOR_T, x1 + 12, y0 + 58, FLOOR_T + 3))
    for x in (x0 - 7.5, x1 + 7.5):
        for y in CAGE_HOLE_Y:
            cuts.append(cylz(x, y, FLOOR_T - 1, FLOOR_T + 4, 3.4))
    zs = BAY_Z[0] + 6.35                                   # 3.5" device side-hole height
    for (ya, yb) in ((14, 40), (46, 74), (80, 96)):
        for (xa, xb) in ((x0 - 4, x0 + 0.5), (x1 - 0.5, x1 + 4)):
            cuts.append(M.batch_hull([cylx(xa, xb, y0 + ya, zs, 3.4), cylx(xa, xb, y0 + yb, zs, 3.4)]))
    return diff(union(parts), cuts)

def bay_blank(x0):
    """Clip-in 3.5" bay cover with a JX drive face. Two snap hooks catch behind
    the front wall; squeeze them from inside to remove. Fits either bay."""
    a0, a1 = x0 + 0.2, x0 + BAY_W - 0.2
    b0, b1 = BAY_Z[0] + 0.2, BAY_Z[1] - 0.2
    cx = (a0 + a1) / 2
    face = box(a0 - 1.2, 2.7, b0 - 1.2, a1 + 1.2, 3.5, b1 + 1.2)     # sits on the frame recess
    body = box(a0, 3.5, b0, a1, 18.0, b1)
    blank = union([face, body])
    cuts = [box(cx - 11.5, 6.0, b1 - 2.6, cx + 11.5, 16.5, b1 + 1),    # hook pockets
            box(cx - 11.5, 6.0, b0 - 1, cx + 11.5, 16.5, b0 + 2.6)]
    cuts += [box(a0 + 8, 2.0, b1 - 9.5, a1 - 8, 4.2, b1 - 4.0),         # disk slot
             cyly(2.0, 5.5, a0 + 12, b0 + 5.5, 3.2)]                     # LED
    cuts.append(box(a0 + 2.0, 6.0, b0 + 3.2, a1 - 2.0, 18.1, b1 - 3.2))  # hollow from the back
    blank = diff(blank, cuts)
    hooks = []
    for top in (True, False):
        zb, zo = (b1 - 1.4, b1) if top else (b0, b0 + 1.4)
        hooks.append(box(cx - 10, 6.2, zb, cx + 10, 18.0, zo))
        e = b1 if top else b0
        za, zb_ = (e, e + 1.0) if top else (e - 1.0, e)
        hooks.append(M.batch_hull([box(cx - 10, 6.2, za, cx + 10, 8.0, zb_),          # catch lip + ramp
                                   box(cx - 10, 9.99, min(e, e - 0.01), cx + 10, 10.0, max(e, e + 0.01))]))
    button = box(a1 - 26, 1.5, b0 + 2.5, a1 - 8, 2.71, b0 + 7.5)
    return union([blank, button] + hooks)

def dvd_shelf():
    """Shelf + side rails for a standard 5.25" optical drive. Rests on ledges on
    the front and right walls; drive screws through the rail slots (adjust the
    drive forward/back until the bezel sits flush in the JX drive face)."""
    x0, x1 = ODD_CX - 79.0, W - SIDE_T - 0.6
    zt = ODD_BOTTOM
    plate = box(x0, FRONT_T + 0.5, zt - SHELF_T, x1, 148.0, zt)
    notch = box(ODD_OPEN[0] - 1, FRONT_T - 1, zt - SHELF_T - 1, ODD_OPEN[2] + 1, FRONT_T + 8.0, zt + 1)
    body = diff(plate, [notch])
    rl0, rr0 = ODD_CX - 73.03 - 0.3 - 3, ODD_CX + 73.03 + 0.3
    parts = [body, box(rl0, 16, zt - 0.01, rl0 + 3, 130, zt + 20), box(rr0, 16, zt - 0.01, rr0 + 3, 130, zt + 20),
             box(rr0 + 2.99, 16, zt - 0.01, x1, 20, zt + 6), box(rr0 + 2.99, 126, zt - 0.01, x1, 130, zt + 6)]
    body = union(parts)
    cuts = []
    zs = zt + 10.0                                          # 5.25" side-hole height
    for (ya, yb) in ((52, 68), (84, 100)):
        for xr in (rl0, rr0):
            cuts.append(M.batch_hull([cylx(xr - 1, xr + 4, ya, zs, 3.4), cylx(xr - 1, xr + 4, yb, zs, 3.4)]))
    for (x, y) in SHELF_INSERTS:
        cuts.append(cylz(x, y, zt - SHELF_T - 1, zt + 1, 3.4))
        cuts.append(cylz(x, y, zt - 1.7, zt + 0.01, 3.4, d2=6.8))  # countersink
    return diff(body, cuts)

def glyph(ch, cx, cz, size, y_face, height):
    """Raised character on the front face (centred at cx, cz), standing `height`
    proud of the surface at y = y_face."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), ch, size=size, prop=FontProperties(fname=LABEL_FONT))
    cs = CS.even_odd([p[:-1] for p in tp.to_polygons()])
    (bx0, by0, bx1, by1) = cs.bounds()
    cs = cs.translate([cx - (bx0 + bx1) / 2, cz - (by0 + by1) / 2])
    return M.extrude(cs, height + 0.01).rotate([90, 0, 0]).translate([0, y_face + 0.01, 0])

# ---------------------------------------------------------------- power paddle
# Lever geometry is drawn level (tip pointing to the front, -y) around the axle,
# then tilted. x is relative to PSW_X; the lever has one flat side at x = -2.9
# so it prints lying on that side.
PSW_TAIL_R = 19.5              # tail length
PSW_MAG_R = 15.0               # tail magnet radius from the axle
MAG_D, MAG_T = 8.0, 3.0        # 8 x 3 mm disc magnets
# Red paddle head: fills the JX channel (22.8 wide) like the original
HEAD_W, HEAD_H, HEAD_D = 20.6, 15.0, 7.0
HEAD_R0 = 16.9                 # head back face radius (clears the channel floor at both stops)
ARM_R = HEAD_R0 + HEAD_D - 1.5 # arm length into the head

def _pt(theta, y, z):
    """level (y, z) relative to the axle -> case (y, z) when tilted by theta"""
    a = math.radians(-theta)
    return (PSW_PIVOT[0] + y * math.cos(a) - z * math.sin(a), PSW_PIVOT[1] + y * math.sin(a) + z * math.cos(a))

def _at(m, theta):
    """level part -> tilted by theta and placed at the axle"""
    return m.rotate([-theta, 0, 0]).translate([PSW_X, PSW_PIVOT[0], PSW_PIVOT[1]])

def _yz_extrude(pts, x0, x1):
    """extrude a polygon given in (y, z) along x from x0 to x1"""
    cs = CS([pts])
    if cs.area() <= 0:
        cs = CS([pts[::-1]])
    m = M.extrude(cs, x1 - x0)                   # 2D (u, v) -> (x, y), extrude along z
    # map (u, v, w) -> (x = w + x0, y = u, z = v)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])

def paddle_lever(theta=None):
    """Lever: hub on the axle, arm through the slot, tail with a magnet."""
    t = PSW_OFF if theta is None else theta
    hub = cylx(-2.9, 5.1, 0, 0, 9.0, fn=40)
    arm = box(-2.9, -ARM_R, -3.0, 2.9, 0, 3.0)
    tail = box(-2.9, 0, -5.0, 5.1, PSW_TAIL_R, 5.0) ^ cylx(-3, 5.2, 0, 0, 2 * PSW_TAIL_R, fn=96)
    lev = union([hub, arm, tail])
    lev = diff(lev, [cylx(-4, 6, 0, 0, 3.4),                                        # axle
                     cylx(5.1 - MAG_T - 0.1, 5.2, PSW_MAG_R, 0, MAG_D + 0.2)])           # tail magnet (faces +x)
    return _at(lev, t)

def paddle_head(theta=None):
    """Red paddle head, glued onto the end of the arm."""
    t = PSW_OFF if theta is None else theta
    r0, r1, hw, hh = HEAD_R0, HEAD_R0 + HEAD_D, HEAD_W / 2, HEAD_H / 2
    c = 1.5                                                                        # front-edge chamfer
    h = M.batch_hull([box(-hw, -r1 + c, -hh, hw, -r0, hh), box(-hw, -r1, -hh + c, hw, -r0, hh - c)])
    cuts = [box(-3.05, -ARM_R - 0.05, -3.15, 3.05, -r0 + 0.1, 3.15)]              # arm socket
    return _at(diff(h, cuts), t)

def paddle_slot():
    """Slot through the channel wall: the arm's sweep between the hard stops."""
    arms = []
    for k in range(13):
        t = PSW_STOPS[0] + (PSW_STOPS[1] - PSW_STOPS[0]) * k / 12
        arms.append(_at(box(-3.3, -ARM_R, -3.5, 3.3, 0, 3.5), t))
    sweep = M.batch_hull(arms)
    return sweep ^ box(PSW_X - 10, -1, 0, PSW_X + 10, FRONT_T + 0.5, 100)

def paddle_frame():
    """Cheeks carrying the axle and the microswitch. The right cheek holds the
    two latch magnets (切 and 入) that the tail magnet slides past."""
    X, (py, pz) = PSW_X, PSW_PIVOT
    cl, cr = (-6.2, -3.2), (5.4, 9.4)                      # cheek x ranges
    parts = []
    for (a, b) in (cl, cr):
        parts.append(box(X + a, FRONT_T + 0.3, 7.0, X + b, 39.0, 58.0))
    parts.append(box(X + cl[0], FRONT_T + 0.3, 7.0, X + cr[1], 39.0, 8.5))         # base plate
    parts.append(box(X + cl[0], 36.0, 7.0, X + cr[1], 39.0, 58.0))                  # rear wall
    for (ex, ez) in PSW_EARS:          # ears to the wall bosses
        x0, x1 = (X + ex - 6.4, X + cl[0] + 0.01) if ex < 0 else (X + cr[1] - 0.01, X + ex + 6.3)
        if ez < 30:
            parts.append(box(x0, FRONT_T + 2.3, 7.0, x1, 16.0, ez + 5))
        else:                                   # 45-degree gusset down to the cheek
            xc = X + cl[0] if ex < 0 else X + cr[1]
            parts.append(M.batch_hull([box(x0, FRONT_T + 2.3, ez - 5, x1, 16.0, ez + 5),
                                       box(xc - 0.01, FRONT_T + 2.3, ez - 5 - abs(x1 - x0), xc + 0.01, 16.0, ez - 5)]))
    body = union(parts)
    cuts = [cylx(X + cl[0] - 1, X + cr[1] + 1, py, pz, 3.2)]                       # axle
    for t in (PSW_OFF, PSW_ON):                   # latch magnets, pushed in from outside
        my, mz = _pt(t, PSW_MAG_R, 0)
        cuts.append(cylx(X + cr[0] + 0.6, X + cr[1] + 1, my, mz, MAG_D + 0.2))
    for (ex, ez) in PSW_EARS:
        cuts.append(cyly(FRONT_T, 17, X + ex, ez, 3.4))
    # microswitch (SS-5GL / KW11 size) lying between the cheeks, plunger up, under
    # the tail end; two M2 screws through height-adjustable slots in both cheeks
    for hy in (PSW_SW_Y - 4.75, PSW_SW_Y + 4.75):
        cuts.append(M.batch_hull([cylx(X + cl[0] - 1, X + cr[1] + 1, hy + dy, z, 2.4)
                                  for dy in (-1.0, 1.0) for z in (9.5, 17.5)]))
    return diff(body, cuts)

PSW_SW_Y = 16.5                # microswitch centre (y); body 19.8 long, lever tip at the rear end

# ---------------------------------------------------------------- DVD fascia
# JX-style faceplate for a standard 5.25" optical drive, in two pieces: a frame
# glued to the drive's fixed bezel and a strip glued to the moving tray front.
# Measure your drive and adjust these (mm from the bezel's TOP-LEFT corner):
DVD_BEZEL = (148.0, 42.3)                  # bezel width, height
DVD_TRAY = (10.0, 8.0, 138.0, 22.5)        # tray front: x0, from-top0, x1, from-top1
DVD_EJECT = (124.0, 31.0, 140.0, 37.0)     # eject button: x0, from-top0, x1, from-top1
DVD_ACT_LED = (115.0, 34.0)                # drive's activity LED (through hole); None to skip
DVD_PLATE_T = 2.0
DVD_TRAY_GAP = 0.6

def dvd_fascia():
    """Returns (frame, tray_strip) positioned on the assembled case, with the
    drive pulled back by DVD_PLATE_T so the fascia sits in the JX drive face."""
    bw, bh = DVD_BEZEL
    X0, ZT = ODD_CX - bw / 2, ODD_CZ + bh / 2
    yb = 1.6 + DVD_PLATE_T                       # plate back face (drive bezel front)
    yf = yb - DVD_PLATE_T
    def r(x0, t0, x1, t1, ya, yb_):              # rectangle in bezel coords
        return box(X0 + x0, ya, ZT - t1, X0 + x1, yb_, ZT - t0)
    # photo-traced JX 5.25" drive face (photo px -> bezel mm)
    fx, fz = bw / (1380 - 832), bh / (255 - 105)
    def pr(px0, py0, px1, py1):
        return ((px0 - 832) * fx, (py0 - 105) * fz, (px1 - 832) * fx, (py1 - 105) * fz)
    slot = pr(848, 155, 1365, 183)
    door = pr(935, 105, 1155, 255)
    lever = pr(935, 107, 1070, 136)
    knob = ((965 - 832) * fx, (121 - 105) * fz)
    jx_led = ((1280 - 832) * fx, (130 - 105) * fz)
    tx0, tt0, tx1, tt1 = DVD_TRAY
    g = DVD_TRAY_GAP

    def details(base, clip):
        """raise the door panel + lever, recess the slot, inside region `clip`"""
        up = [r(door[0], 0.6, door[2], bh - 0.6, yf - 0.6, yf + 0.01),
              r(lever[0], lever[1], lever[2], lever[3], yf - 1.4, yf + 0.01)]
        up = [u ^ clip for u in up]
        body = union([base] + up)
        cuts = [r(slot[0], slot[1], slot[2], slot[3], yf - 2, yf + 1.2) ^ clip,
                cyly(yf - 2, yf - 0.4, X0 + knob[0], ZT - knob[1], 3.0) ^ clip]
        return diff(body, cuts)

    whole = box(X0 - 5, yf - 5, ZT - bh - 5, X0 + bw + 5, yb + 5, ZT + 5)
    tray_cut = r(tx0 - g, tt0 - g, tx1 + g, tt1 + g, yf - 3, yb + 1)
    frame = diff(r(0, 0, bw, bh, yf, yb), [tray_cut])
    frame = details(frame, whole - tray_cut)
    fcuts = [r(*DVD_EJECT, yf - 3, yb + 1),                              # press the real eject button
             cyly(yf - 2, yf + 1.0, X0 + jx_led[0], ZT - jx_led[1], 3.0)]  # JX LED: paint it red
    if DVD_ACT_LED:
        fcuts.append(cyly(yf - 3, yb + 1, X0 + DVD_ACT_LED[0], ZT - DVD_ACT_LED[1], 2.5))
    frame = diff(frame, fcuts)
    tray = r(tx0, tt0, tx1, tt1, yf, yb)
    tray = details(tray, r(tx0, tt0, tx1, tt1, yf - 3, yb + 1))
    return frame, tray

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
    parts["bay_cage_35_x2"] = (bay_cage(BAY_B_X0), [90, 0, 0])      # front face down
    parts["bay_blank_clip_x2"] = (bay_blank(BAY_B_X0), [-90, 0, 0])  # back face down
    parts["dvd_shelf"] = (dvd_shelf(), None)
    parts["power_paddle_frame"] = (paddle_frame(), None)                # base down
    parts["power_paddle_lever"] = (paddle_lever(0), [0, -90, 0])        # flat side down
    parts["power_paddle_head_RED"] = (paddle_head(0), [90, 0, 0])       # front face down
    dvd_frame, dvd_tray = dvd_fascia()
    parts["dvd_fascia_frame"] = (dvd_frame, [-90, 0, 0])              # back face down
    parts["dvd_fascia_tray"] = (dvd_tray, [-90, 0, 0])
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
