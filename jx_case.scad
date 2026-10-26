// JX-style desktop case for a standard ATX motherboard + ATX PSU.
// Printable on a 256 x 256 mm bed (every part <= 250 mm).
//
// Coordinates (assembled case):
//   X = width, left -> right as seen from the front   (0 .. W)
//   Y = depth, front -> rear                           (0 .. D)
//   Z = height, bottom of floor -> top                 (0 .. H)
//
// Needs OpenSCAD 2025 or later with the Manifold backend (for textmetrics()
// and speed). `python3 build.py` renders every part into ./stl; open this file
// in the GUI and pick `part` to look at one.
//
// Hardware (see README.md for the full list): M3 heat-set inserts (M3 x 5.7),
// M3 bolts + nuts, 9 x M3 10 mm female-female brass standoffs.

/* [Output] */
// Printable parts are named after their STL and turned for printing; asm_* are solids in assembled-case coordinates.
part = "assembly"; // [assembly, assembly_open, base_front_left_JP, base_front_left_EN, base_front_left_BLANK, labels_JP_inlay, labels_EN_inlay, base_front_right, base_rear_left, base_rear_right, lid_front_left, lid_front_right, lid_rear_left, lid_rear_right, rear_slot_panel, rear_io_panel, bracket_rail, butterfly_key_x9, foot_x6, badge_plate_x2, bay_cage_35_x2, bay_blank_clip_x2, dvd_shelf, power_switch_frame, dvd_fascia_frame, dvd_fascia_tray, fit_template_left, fit_template_right, asm_shell_JP, asm_shell_EN, asm_shell_BLANK, asm_lid, asm_slot_insert, asm_io_insert, asm_bracket_rail, asm_bay_cage_B, asm_bay_cage_A, asm_bay_blank_B, asm_bay_blank_A, asm_dvd_shelf, asm_power_switch_frame, asm_dvd_fascia_frame, asm_dvd_fascia_tray, asm_labels_JP, asm_labels_EN, asm_lever]
// Blade angle for part = "asm_lever" (deg, + = up)
lever_angle = 30;

/* [Motherboard fit: check with the fit template] */
// Slot-side board edge to the left edge of the I/O shield opening
IO_U0 = 146.0;
// Slot-side board edge to the centre of the bracket nearest the I/O
SLOT7_U = 131.8;
// Card bracket flange rest above the board top (the rail adjusts +-6)
RAIL_LEDGE_ABOVE_BOARD = 108.0;
// Depth of the line between the two "units"
GROOVE_D = 4.0;

/* [DVD fascia: mm from the bezel's top-left corner] */
DVD_BEZEL = [148.0, 42.3];              // bezel width, height
DVD_TRAY = [10.0, 8.0, 138.0, 22.5];    // tray front: x0, from-top0, x1, from-top1
DVD_EJECT = [124.0, 31.0, 140.0, 37.0]; // eject button: x0, from-top0, x1, from-top1
DVD_ACT_LED = [115.0, 34.0];            // drive's activity LED (through hole); [] to skip
DVD_PLATE_T = 2.0;
DVD_TRAY_GAP = 0.6;

/* [Switch labels] */
LABEL_FONT = "IPAGothic";
LABEL_FONT_EN = "Liberation Sans:style=Bold";

/* [Hidden] */
$fn = 48;

// ---------------------------------------------------------------- parameters
W = 495.0; D = 324.0;        // exterior width / depth
WALL_TOP = 196.0;            // top of the walls (lid sits on this); 199 overall = JX photo ratio
LID_T = 3.0;                 // lid plate thickness
FLOOR_T = 5.0;
SIDE_T = 3.0;                // left / right / rear wall
FRONT_T = 6.0;               // front wall (thicker, carries the JX face details)
SPLIT_X = W / 2;             // quadrant split lines
SPLIT_Y = D / 2;

// Motherboard (ATX 305 x 244). Board coords: u along the rear edge from the
// slot-side edge, v from the rear edge toward the front.
BOARD_W = 304.8; BOARD_D = 243.84;
BOARD_X0 = 15.0;                       // case X of the slot-side board edge
INSERT_Y0 = 316.8; INSERT_Y1 = 320.8;  // rear inserts (slot + I/O panels) sit here
BOARD_REAR_Y = INSERT_Y0 - 1.65;       // board rear edge 1.65 mm inside the panel
RING_H = 2.0;                          // printed locating ring under each standoff
STANDOFF_H = 10.0;                     // brass M3 F-F standoff
BOARD_BOTTOM = FLOOR_T + RING_H + STANDOFF_H;
BOARD_TOP = BOARD_BOTTOM + 1.57;

// ATX mounting holes (mm, board coords) A C F G H J K L M
ATX_HOLES = [[16.69, 10.16], [141.15, 10.16], [298.63, 33.02],
             [16.69, 165.10], [141.15, 165.10], [298.63, 165.10],
             [16.69, 237.49], [141.15, 237.49], [298.63, 237.49]];
// Rear I/O aperture (ATX: 158.75 x 44.45, bottom 3.81 below board top)
IO_W = 158.75; IO_H = 44.45;
// Expansion slots: bracket centre of the slot nearest the I/O, 0.8" pitch
SLOT_PITCH = 20.32;
N_SLOTS = 7;
SLOT_OPEN_W = 14.0;
SLOT_OPEN_Z = [10.0, BOARD_TOP + 102.0];
RAIL_LEDGE_Z = BOARD_TOP + RAIL_LEDGE_ABOVE_BOARD;

// PSU (standard ATX 150 x 86, 140-160 deep), rear face against the rear wall
PSU_X0 = 337.0;
PSU_W = 150.0; PSU_H = 86.0;
PSU_CX = PSU_X0 + PSU_W / 2; PSU_CZ = FLOOR_T + PSU_H / 2;

// Rear opening for the two inserts (wall removed here, full height)
REAR_OPEN_X = [13.0, 326.0];

// JX front layout. Features are traced in pixels from a photo of a JX (system
// unit with the expansion unit on top) and mapped uniformly onto the front.
PHOTO_X0 = 39.0; PHOTO_X1 = 1561.0; PHOTO_Y0 = 69.0;   // case left/right/top edges in the photo
PX = W / (PHOTO_X1 - PHOTO_X0);                         // mm per photo pixel
H_TOTAL = WALL_TOP + LID_T;

// photo pixel box -> [x0, z0, x1, z1] on the front face (mm)
function P(x0, y0, x1, y1) =
    [(x0 - PHOTO_X0) * PX, H_TOTAL - (y1 - PHOTO_Y0) * PX,
     (x1 - PHOTO_X0) * PX, H_TOTAL - (y0 - PHOTO_Y0) * PX];

GROOVE_Z = [107.4, 111.4];             // line between the two "units" (photo rows 340-349)
EDGE_R = 2.5;                          // quarter-round on the lid's top edge and both groove lips
EDGE_SEG = 8;                          // facets per quarter-round
CORNER_FRONT = 2.0;                    // 45-degree vertical corners (leg length)
CORNER_REAR = 1.0;
BADGE_UP = P(93, 102, 210, 145);
BADGE_LO = P(93, 377, 210, 420);
DRIVE_B_FRAME = P(712, 380, 1098, 528);
DRIVE_A_FRAME = P(1108, 380, 1500, 528);
UPPER_FACE = P(832, 105, 1380, 255);   // 5.25" drive face in the upper unit

// Functional 3.5" bays (drive B = USB panel, drive A = floppy / card reader)
BAY_W = 102.2; BAY_H = 26.0;
BAY_Z = [DRIVE_B_FRAME[3] - 9.0 - BAY_H, DRIVE_B_FRAME[3] - 9.0];
BAY_B_X0 = (DRIVE_B_FRAME[0] + DRIVE_B_FRAME[2]) / 2 - BAY_W / 2;
BAY_A_X0 = (DRIVE_A_FRAME[0] + DRIVE_A_FRAME[2]) / 2 - BAY_W / 2;

// Functional 5.25" bay for an optical drive (bezel 148 x 42.3, body 146.05 x 41.3)
ODD_CX = (UPPER_FACE[0] + UPPER_FACE[2]) / 2;
ODD_CZ = (UPPER_FACE[1] + UPPER_FACE[3]) / 2;
ODD_OPEN = [ODD_CX - 74.3, ODD_CZ - 21.45, ODD_CX + 74.3, ODD_CZ + 21.45];
ODD_BOTTOM = ODD_CZ - 41.3 / 2;        // drive body bottom = shelf top
SHELF_T = 5.0;
LEDGE_TOP = ODD_BOTTOM - SHELF_T;

// JX power switch built around Axeman's "Big Red Switch (IBM XT style)" lever
// (printables.com/model/459567, CC BY-NC-SA 4.0), used unmodified from
// third_party/BRS_Lever.stl. The red drum sits in the JX channel and the
// blade sticks out. 切 OFF (blade down) and 入 ON (blade up) latch on magnets;
// pushing past 入 is START: it presses a microswitch and springs back.
LEVER_STL = "third_party/BRS_Lever.stl";
PSW_X = 44.2;                          // lever centre (middle of the JX switch channel)
PSW_PIVOT = [18.5, 34.8];              // M4 axle (y, z), axis along X
PSW_OFF = -30.0; PSW_ON = 30.0; PSW_START = 38.0;   // blade angles (deg, + = up)
PSW_STOPS = [-32.0, 39.0];             // the blade root meets the window edges here
LEVER_NATIVE_BLADE = 30.0;             // blade angle in the STL's own frame
LEVER_MAG = [10.03, 5.79];             // lever magnet centre in the STL frame (x, z)
PSW_EARS = [[-20.5, 14.0], [-20.5, 55.0], [20.5, 14.0], [20.5, 55.0]];  // rel. to PSW_X, abs z
LABEL_STYLES = ["JP", "EN", "BLANK"];  // 入/切, IEC | On / Off O, none (for stickers)
LABEL_Y = [1.5, 2.1];                  // labels are 0.6 mm flush inlays in the housing face

FAN92 = 82.5;     // hole spacing
FAN80 = 71.5;

function board_xy(u, v) = [BOARD_X0 + u, BOARD_REAR_Y - v];

STANDOFFS = [for (h = ATX_HOLES) board_xy(h[0], h[1])];
SLOT_X = [for (i = [0 : N_SLOTS - 1]) BOARD_X0 + SLOT7_U - i * SLOT_PITCH];
IO_X = [BOARD_X0 + IO_U0, BOARD_X0 + IO_U0 + IO_W];
IO_Z = [BOARD_TOP - 3.81, BOARD_TOP - 3.81 + IO_H];

// rear inserts, bay cages and DVD shelf (used by the shell as well)
INS_Z = [FLOOR_T, WALL_TOP];
INS_BOLT_Z = [30.0, 100.0, 175.0];
RAIL_BOLT_X = [60.0, 110.0, 180.0];
CAGE_Y0 = FRONT_T + 0.5;
CAGE_HOLE_Y = [CAGE_Y0 + 8.5, CAGE_Y0 + 48.5];
SHELF_INSERTS = [[300.0, FRONT_T + 11.5], [400.0, FRONT_T + 11.5], [462.0, FRONT_T + 6.0],
                 [W - SIDE_T - 4, 40.0], [W - SIDE_T - 4, 95.0], [W - SIDE_T - 4, 140.0]];
MAG_D = 8.0; MAG_T = 3.0;        // 8 x 3 mm disc magnets
PSW_SW = [26.0, 45.0, 64.8];     // microswitch: plunger-face y, body z0, z1 (19.8 long, along z)

QUADRANTS = [["front_left", 0, SPLIT_X, 0, SPLIT_Y], ["front_right", SPLIT_X, W, 0, SPLIT_Y],
             ["rear_left", 0, SPLIT_X, SPLIT_Y, D], ["rear_right", SPLIT_X, W, SPLIT_Y, D]];

// ---------------------------------------------------------------- helpers
// case footprint with its 45-degree vertical corners; `rear` moves the back edge
function case_outline(rear = D) =
    [[CORNER_FRONT, 0], [W - CORNER_FRONT, 0], [W, CORNER_FRONT], [W, rear - CORNER_REAR],
     [W - CORNER_REAR, rear], [CORNER_REAR, rear], [0, rear - CORNER_REAR], [0, CORNER_FRONT]];

// thin horizontal slice of the footprint at height z, inset by `inset` all round
module outline_slice(z, inset, rear = D) {
    translate([0, 0, z]) linear_extrude(0.01) offset(delta = -inset) polygon(case_outline(rear));
}

// points on a quarter-round of radius EDGE_R: [inset from the face, height from the edge's flat end]
function quarter_round() = [for (i = [0 : EDGE_SEG]) let (a = 90 * i / EDGE_SEG)
    [EDGE_R - EDGE_R * cos(a), EDGE_R * sin(a)]];

// Material removed to round one groove lip, following the footprint (front and
// both sides; the outline is pushed past the rear so the back stays square).
// The lip edge is at z = edge; dir = +1 rounds upward (upper lip), -1 downward.
module groove_lip_cut(edge, dir) {
    q = quarter_round();
    for (i = [0 : EDGE_SEG - 1]) {
        // q[i] is at the lip's mouth (inset 0, deepest into the groove's wall)
        za = edge + dir * (EDGE_R - q[i][1]); zb = edge + dir * (EDGE_R - q[i + 1][1]);
        difference() {
            box(-1, -1, min(za, zb), W + 1, D + 1, max(za, zb));
            hull() {
                outline_slice(min(za, zb) - 0.01, dir > 0 ? q[i + 1][0] : q[i][0], D + 20);
                outline_slice(max(za, zb), dir > 0 ? q[i][0] : q[i + 1][0], D + 20);
            }
        }
    }
}

// numpy.arange: a, a+s, ... while < b (OpenSCAD's own [a:s:b] includes b)
function arange(a, b, s) = let (n = ceil((b - a) / s)) n > 0 ? [for (i = [0 : n - 1]) a + i * s] : [];

module box(x0, y0, z0, x1, y1, z1) {
    translate([x0, y0, z0]) cube([x1 - x0, y1 - y0, z1 - z0]);
}
module cylz(x, y, z0, z1, d, fn = 40, d2 = undef) {
    translate([x, y, z0]) cylinder(h = z1 - z0, d1 = d, d2 = is_undef(d2) ? d : d2, $fn = fn);
}
module cylx(x0, x1, y, z, d, fn = 32) {
    translate([x0, y, z]) rotate([0, 90, 0]) cylinder(h = x1 - x0, d = d, $fn = fn);
}
module cyly(y0, y1, x, z, d, fn = 32) {
    translate([x, y0, z]) rotate([-90, 0, 0]) cylinder(h = y1 - y0, d = d, $fn = fn);
}
module hexx(x0, x1, y, z, af = 5.7) {     // nut trap, bolt axis along X
    translate([x0, y, z]) rotate([0, 90, 0]) rotate([0, 0, 30]) cylinder(h = x1 - x0, r = af / sqrt(3), $fn = 6);
}
module hexy(y0, y1, x, z, af = 5.7) {     // nut trap, bolt axis along Y
    translate([x, y0, z]) rotate([-90, 0, 0]) rotate([0, 0, 30]) cylinder(h = y1 - y0, r = af / sqrt(3), $fn = 6);
}

// Block on a wall face with a 45-degree support wedge underneath so it prints
// without supports. `wall` = side the wall is on: "-x", "+x", "-y", "+y".
module gusset(x0, x1, y0, y1, z0, z1, wall) {
    hull() {
        box(x0, y0, z0, x1, y1, z1);
        if (wall == "-x" || wall == "+x") {
            xs = wall == "-x" ? x0 : x1 - 0.01;
            box(xs, y0, z0 - (x1 - x0), xs + 0.01, y1, z0);
        } else {
            ys = wall == "-y" ? y0 : y1 - 0.01;
            box(x0, ys, z0 - (y1 - y0), x1, ys + 0.01, z0);
        }
    }
}

module extrude_poly(pts, z0, z1) {
    translate([0, 0, z0]) linear_extrude(z1 - z0) polygon(pts);
}

// Butterfly key outline; long axis across the seam.
module bowtie(cx, cy, along, shrink = 0.0, z0 = 0.0, z1 = 1.0) {
    L = 15.0 - shrink; Wd = 7.0 - shrink; w = 3.5 - shrink;
    pts = [[-L, -Wd], [0, -w], [L, -Wd], [L, Wd], [0, w], [-L, Wd]];
    p = along == "y" ? [for (q = pts) [q[1], q[0]]] : pts;
    extrude_poly([for (q = p) [cx + q[0], cy + q[1]]], z0, z1);
}

// ---------------------------------------------------------------- lower shell
module lower_shell(labels = "JP") {
    difference() {
        union() {
            difference() {
                union() {
                    difference() {
                        box(0, 0, 0, W, D, WALL_TOP);
                        box(SIDE_T, FRONT_T, FLOOR_T, W - SIDE_T, D - SIDE_T, WALL_TOP + 10);
                    }
                    shell_adds();
                }
                shell_cuts();
                front_recesses();
            }
            front_raises();
        }
        front_through(labels);
    }
}

module shell_adds() {
    // --- standoff locating rings
    for (s = STANDOFFS) cylz(s[0], s[1], FLOOR_T - 0.01, FLOOR_T + RING_H, 9.0);
    // --- bosses for the power-switch frame (heat-set inserts)
    for (e = PSW_EARS) cyly(FRONT_T - 0.01, FRONT_T + 2.0, PSW_X + e[0], e[1], 9.0);
    // --- groove backing bands (the unit groove is deeper than the walls)
    bz0 = GROOVE_Z[0] - 2; bz1 = GROOVE_Z[1] + 2;
    gusset(SIDE_T, W - SIDE_T, FRONT_T - 0.01, FRONT_T + 4, bz0, bz1, "-y");
    gusset(SIDE_T - 0.01, SIDE_T + 4.2, FRONT_T, D - SIDE_T + 0.01, bz0, bz1, "-x");
    gusset(W - SIDE_T - 4, W - SIDE_T + 0.01, FRONT_T, D - SIDE_T + 0.01, bz0, bz1, "+x");
    // --- ledges carrying the optical-drive shelf (front-right quadrant)
    gusset(285, W - SIDE_T, FRONT_T - 0.01, FRONT_T + 14, LEDGE_TOP - 8, LEDGE_TOP, "-y");
    gusset(W - SIDE_T - 8, W - SIDE_T + 0.01, 20, 146, LEDGE_TOP - 8, LEDGE_TOP, "+x");
    // --- seam tabs (bolt + nut) on the front and side walls
    for (zc = [28.0, 106.0, 130.0, 165.0]) {
        gusset(SPLIT_X - 10, SPLIT_X + 10, FRONT_T - 0.01, FRONT_T + 8, zc - 8, zc + 8, "-y");
        gusset(SIDE_T - 0.01, SIDE_T + 8, SPLIT_Y - 10, SPLIT_Y + 10, zc - 8, zc + 8, "-x");
    }
    for (zc = [130.0, 165.0])          // right side: above the PSU only
        gusset(W - SIDE_T - 8, W - SIDE_T + 0.01, SPLIT_Y - 10, SPLIT_Y + 10, zc - 8, zc + 8, "+x");
    // --- lid bosses (heat-set inserts from the top)
    for (b = lid_boss_list()) gusset(b[0], b[2], b[1], b[3], WALL_TOP - 10, WALL_TOP, b[4]);
}

module shell_cuts() {
    for (e = PSW_EARS) cyly(FRONT_T - 4.0, FRONT_T + 2.1, PSW_X + e[0], e[1], 4.0);
    for (s = SHELF_INSERTS) cylz(s[0], s[1], LEDGE_TOP - 6, LEDGE_TOP + 0.1, 4.0);
    // seam tab bolts + nut traps
    xl = (SIDE_T - 0.01 + SIDE_T + 8) / 2;
    xr = (W - SIDE_T - 8 + W - SIDE_T + 0.01) / 2;
    for (zc = [28.0, 106.0, 130.0, 165.0]) {
        cylx(SPLIT_X - 11, SPLIT_X + 11, FRONT_T + 4, zc, 3.4);
        hexx(SPLIT_X + 6.5, SPLIT_X + 10.5, FRONT_T + 4, zc);
        cyly(SPLIT_Y - 11, SPLIT_Y + 11, xl, zc, 3.4);
        hexy(SPLIT_Y + 6.5, SPLIT_Y + 10.5, xl, zc);
    }
    for (zc = [130.0, 165.0]) {
        cyly(SPLIT_Y - 11, SPLIT_Y + 11, xr, zc, 3.4);
        hexy(SPLIT_Y + 6.5, SPLIT_Y + 10.5, xr, zc);
    }
    for (b = lid_boss_list()) cylz(b[5], b[6], WALL_TOP - 7, WALL_TOP + 1, 4.0);

    // --- rear: big opening for the two inserts (wall removed full height)
    box(REAR_OPEN_X[0], D - SIDE_T - 1, FLOOR_T, REAR_OPEN_X[1], D + 1, WALL_TOP + 1);
    // insert fixing bolts through the columns either side
    for (zc = INS_BOLT_Z) {
        cyly(INSERT_Y0 - 1, D + 1, 10.2, zc, 3.4);
        cyly(INSERT_Y0 - 1, D + 1, 330.5, zc, 3.4);
    }
    // PSU opening + screw holes (union of upright / flipped mounting patterns)
    box(PSU_CX - 62, D - SIDE_T - 1, PSU_CZ - 30, PSU_CX + 62, D + 1, PSU_CZ + 30);
    for (sx = [-1, 1], sz = [-1, 1], h = [[69, 37], [69, 27], [45, 37]])
        cyly(D - SIDE_T - 1, D + 1, PSU_CX + sx * h[0], PSU_CZ + sz * h[1], 3.6);

    // --- floor
    for (s = STANDOFFS) {
        cylz(s[0], s[1], -1, FLOOR_T + RING_H + 1, 3.4);
        cylz(s[0], s[1], -1, 2.5, 6.6);                     // M3 head counterbore underneath
    }
    for (xc = SLOT_X)                                       // bracket tab slots
        box(xc - 6, INSERT_Y0 - 5, -1, xc + 6, INSERT_Y0, FLOOR_T + 1);
    for (x = arange(347, 480, 8))                           // PSU vent (fan-down option)
        box(x, 192, -1, x + 4, 306, FLOOR_T + 1);
    for (x = [200.0, 290.0])                                // I/O insert floor lip inserts
        cylz(x, INSERT_Y0 - 2.5, 0.8, FLOOR_T + 0.1, 4.0);
    for (p = [[30, 30], [W - 30, 30], [30, D - 30], [W - 30, D - 30], [150, 205], [345, 125]])
        cylz(p[0], p[1], -0.1, 4.2, 4.0);                   // feet (heat-set from below)
    for (x0 = [BAY_B_X0, BAY_A_X0], x = [x0 - 7.5, x0 + BAY_W + 7.5], y = CAGE_HOLE_Y)
        cylz(x, y, FLOOR_T - 4.5, FLOOR_T + 0.1, 4.0);      // 3.5" bay cage inserts
    for (y = [40, 115, 215, 290])                           // butterfly keys, X seam
        bowtie(SPLIT_X, y, "x", 0, FLOOR_T - 3, FLOOR_T + 0.1);
    for (x = [70, 200, 285, 380, 450])                      // butterfly keys, Y seam
        bowtie(x, SPLIT_Y, "y", 0, FLOOR_T - 3, FLOOR_T + 0.1);

    // --- corners + the line between the two stacked "units"
    difference() {
        box(-1, -1, -1, W + 1, D + 1, WALL_TOP + 1);
        translate([0, 0, -2]) linear_extrude(WALL_TOP + 4) polygon(case_outline());
    }
    gz0 = GROOVE_Z[0]; gz1 = GROOVE_Z[1];
    box(-1, -1, gz0, W + 1, GROOVE_D, gz1);                 // front
    box(-1, -1, gz0, GROOVE_D, D + 1, gz1);                 // left side
    box(W - GROOVE_D, -1, gz0, W + 1, D + 1, gz1);          // right side
    groove_lip_cut(gz1, 1);                                 // rounded lips, like the lid's top edge
    groove_lip_cut(gz0, -1);

    // --- left wall: two 92 mm intake fans aimed at the GPU
    for (yc = [105.0, 230.0]) {
        zc = 55.0;
        for (y = arange(yc - 42, yc + 42, 6)) {
            dy = abs(y + 1.75 - yc);
            if (dy <= 43) {
                hz = sqrt(44 * 44 - dy * dy);
                box(-1, y, zc - hz, SIDE_T + 1, y + 3.5, zc + hz);
            }
        }
        for (sy = [-1, 1], sz = [-1, 1])
            cylx(-1, SIDE_T + 1, yc + sy * FAN92 / 2, zc + sz * FAN92 / 2, 3.4);
    }
    // right wall: vertical vent slots above the PSU / beside the CPU
    for (y = arange(194, 290, 6)) box(W - SIDE_T - 1, y, 117, W + 1, y + 3, 172);
    for (y = arange(20, 140, 6)) box(W - SIDE_T - 1, y, 30, W + 1, y + 3, 90);
}

// JX front, traced from a photo of a JX system unit with its expansion unit on
// top. Recess first (front_recesses), then raised details (front_raises), then
// the cuts through (front_through).
module R(b, d) { box(b[0], -1, b[1], b[2], d, b[3]); }                 // recess box to depth d
module U(b, y) { box(b[0], y - 0.01, b[1], b[2], FRONT_T - 0.5, b[3]); } // raise back up to face-y
module thru(b) { box(b[0], -1, b[1], b[2], FRONT_T + 1, b[3]); }

module front_recesses() {
    // ---------------- upper unit (expansion unit)
    R(BADGE_UP, 1.5);
    pb = P(316, 100, 603, 264);                       // blank cover panel: outline groove
    R([pb[0], pb[1], pb[2], pb[1] + 1.0], 0.8);
    R([pb[0], pb[3] - 1.0, pb[2], pb[3]], 0.8);
    R([pb[0], pb[1], pb[0] + 1.0, pb[3]], 0.8);
    R([pb[2] - 1.0, pb[1], pb[2], pb[3]], 0.8);
    R(P(706, 95, 1507, 258), 3.5);                    // drive bay recess
    // ---------------- lower unit (system unit)
    R(BADGE_LO, 1.5);
    R(P(95, 503, 212, 652), 1.5);                     // power switch housing
    R(P(140, 505, 210, 650), 3.0);                    // switch channel
    R(P(706, 372, 1507, 650), 2.0);                   // drive / cartridge recess
    R(DRIVE_B_FRAME, 3.5);
    R(DRIVE_A_FRAME, 3.5);
    R(P(712, 563, 1500, 645), 3.5);                   // cartridge strip
}

module front_raises() {
    U(P(712, 105, 826, 255), 1.5); U(P(1388, 105, 1500, 255), 1.5);  // end blocks
    U(UPPER_FACE, 0.9);                               // drive face, framing the optical drive
    U(P(852, 572, 1072, 637), 2.5); U(P(1135, 572, 1355, 637), 2.5); // cartridge doors
}

module front_through(labels) {
    thru(ODD_OPEN);                                   // 5.25" optical drive bezel opening
    paddle_slot();                                    // window for the BRS lever
    paddle_wall_magnet_recesses();
    label_solids(labels);                             // switch labels (inlay recesses)
    thru(P(532, 569, 606, 640));                      // IR window -> power LED window
    for (x0 = [BAY_B_X0, BAY_A_X0])                   // functional 3.5" bays
        thru([x0, BAY_Z[0], x0 + BAY_W, BAY_Z[1]]);
    for (l = [[DRIVE_B_FRAME[0] + 12, BAY_Z[0] - 6.5], [DRIVE_A_FRAME[0] + 12, BAY_Z[0] - 6.5]])
        cyly(-1, FRONT_T + 1, l[0], l[1], 3.2);       // 3 mm LEDs (HDD / spare)
    R(P(1400, 598, 1450, 612), 5.0);                  // mode switch slot
}

// [x0, y0, x1, y1, wall-side, hole_x, hole_y]
function lid_boss_list() = concat(
    [for (y = [25.0, 140.0, 184.0, 300.0], s = [0, 1])
        s == 0 ? [SIDE_T - 0.01, y - 5, SIDE_T + 8, y + 5, "-x", SIDE_T + 4, y]
               : [W - SIDE_T - 8, y - 5, W - SIDE_T + 0.01, y + 5, "+x", W - SIDE_T - 4, y]],
    [for (x = [25.0, 200.0, 445.0, 475.0]) [x - 5, FRONT_T - 0.01, x + 5, FRONT_T + 8, "-y", x, FRONT_T + 4]],
    [for (x = [360.0, 465.0]) [x - 5, D - SIDE_T - 8, x + 5, D - SIDE_T + 0.01, "+y", x, D - SIDE_T - 4]]);

// ---------------------------------------------------------------- lid
module lid() {
    z0 = WALL_TOP; z1 = WALL_TOP + LID_T;
    lz0 = z0 - 6;              // locating lip just inside the walls / inserts
    rz0 = z0 - 8;              // seam ribs (bolted), the Y rib stops short of the GPU zone
    g = 0.4;
    difference() {
        union() {
            hull() {                                        // plate, quarter-round top edge
                translate([0, 0, z0]) linear_extrude(z1 - EDGE_R - z0) polygon(case_outline());
                for (p = quarter_round()) outline_slice(min(z1 - EDGE_R + p[1], z1 - 0.01), p[0]);
            }
            box(SIDE_T + g, FRONT_T + g, lz0, W - SIDE_T - g, FRONT_T + g + 2, z0 + 0.01);            // front
            box(SIDE_T + 4.2 + g, FRONT_T + g, lz0, SIDE_T + 4.2 + g + 2, INSERT_Y0 - g, z0 + 0.01);  // left (inside band)
            box(W - SIDE_T - g - 2, FRONT_T + g, lz0, W - SIDE_T - g, D - SIDE_T - g, z0 + 0.01);     // right
            box(336, D - SIDE_T - g - 2, lz0, W - SIDE_T - g, D - SIDE_T - g, z0 + 0.01);             // rear (PSU part)
            box(SIDE_T + g, INSERT_Y0 - g - 2, lz0, 336, INSERT_Y0 - g, z0 + 0.01);                   // rear (inserts)
            box(SPLIT_X - 4, FRONT_T + g, rz0, SPLIT_X + 4, 312, z0 + 0.01);
            box(160, SPLIT_Y - 4, rz0, W - SIDE_T - g, SPLIT_Y + 4, z0 + 0.01);
        }
        for (y = [40.0, 120.0, 205.0, 290.0]) {
            cylx(SPLIT_X - 5, SPLIT_X + 5, y, z0 - 4, 3.4);
            hexx(SPLIT_X + 1.4, SPLIT_X + 4.1, y, z0 - 4);
        }
        for (x = [200.0, 300.0, 400.0, 470.0]) {
            cyly(SPLIT_Y - 5, SPLIT_Y + 5, x, z0 - 4, 3.4);
            hexy(SPLIT_Y + 1.4, SPLIT_Y + 4.1, x, z0 - 4);
        }
        // clear the lip around the wall bosses + screw holes
        for (b = lid_boss_list()) {
            box(b[0] - 0.6, b[1] - 0.6, lz0 - 1, b[2] + 0.6, b[3] + 0.6, z0);
            cylz(b[5], b[6], z0 - 1, z1 + 1, 3.4);
            cylz(b[5], b[6], z1 - 1.7, z1 + 0.01, 3.4, d2 = 6.8);
        }
        // vents over the CPU and over the PSU; they start just above the rib tops
        for (x = arange(168, 326, 7))
            if (!(SPLIT_X - 7 < x && x < SPLIT_X + 4)) box(x, 198, z0 + 0.2, x + 3.5, 300, z1 + 1);
        for (x = arange(346, 482, 7)) box(x, 192, z0 + 0.2, x + 3.5, 306, z1 + 1);
    }
}

// ---------------------------------------------------------------- rear inserts
module slot_insert() {
    difference() {
        box(7.6, INSERT_Y0, INS_Z[0], 157.8, INSERT_Y1, INS_Z[1]);
        for (xc = SLOT_X)
            box(xc - SLOT_OPEN_W / 2, INSERT_Y0 - 1, SLOT_OPEN_Z[0], xc + SLOT_OPEN_W / 2, INSERT_Y1 + 1, SLOT_OPEN_Z[1]);
        for (zc = INS_BOLT_Z) cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, 10.2, zc, 3.4);
        for (x = [RAIL_BOLT_X[0], RAIL_BOLT_X[1]]) cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, x, RAIL_LEDGE_Z + 12, 3.4);
    }
}

module io_insert() {
    k = 0.13;                                  // small oversize so the shield snaps in
    m = 3.0;
    fx = 240.0; fz = 105.0;                    // 80 mm exhaust fan above the I/O
    difference() {
        union() {
            box(158.2, INSERT_Y0, INS_Z[0], 335.0, INSERT_Y1, INS_Z[1]);
            box(170, INSERT_Y0 - 6, FLOOR_T, 320, INSERT_Y0 + 0.01, FLOOR_T + 3);   // floor lip
        }
        box(IO_X[0] - k, INSERT_Y0 - 1, IO_Z[0] - k, IO_X[1] + k, INSERT_Y1 + 1, IO_Z[1] + k);
        // thin the rim to 1.2 mm so a standard I/O shield can clip in (keep-out 2.5 mm)
        box(IO_X[0] - m, INSERT_Y0 - 1, IO_Z[0] - m, IO_X[1] + m, INSERT_Y1 - 1.2, IO_Z[1] + m);
        for (x = [200.0, 290.0]) cylz(x, INSERT_Y0 - 2.5, FLOOR_T - 1, FLOOR_T + 4, 3.4);
        for (zc = INS_BOLT_Z) cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, 330.5, zc, 3.4);
        cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, RAIL_BOLT_X[2], RAIL_LEDGE_Z + 12, 3.4);
        for (z = arange(fz - 37, fz + 37, 6)) {
            dz = abs(z + 1.75 - fz);
            hx = sqrt(max(38 * 38 - dz * dz, 0));
            if (hx > 3) box(fx - hx, INSERT_Y0 - 1, z, fx + hx, INSERT_Y1 + 1, z + 3.5);
        }
        for (sx = [-1, 1], sz = [-1, 1])
            cyly(INSERT_Y0 - 1, INSERT_Y1 + 1, fx + sx * FAN80 / 2, fz + sz * FAN80 / 2, 3.4);
    }
}

// Card-bracket screw rail. Bolts to both inserts through vertical slots so the
// ledge height can be set with a card fitted (+-6 mm). Also ties the two
// inserts together.
module bracket_rail() {
    zl = RAIL_LEDGE_Z;
    difference() {
        union() {
            box(14, INSERT_Y0 - 10, zl - 4, 157, INSERT_Y0 - 0.2, zl);          // ledge
            box(14, INSERT_Y0 - 4.2, zl - 4, 196, INSERT_Y0 - 0.2, zl + 22);    // back
        }
        for (x = RAIL_BOLT_X) hull() {
            cyly(INSERT_Y0 - 5, INSERT_Y0 + 1, x, zl + 6, 3.4);
            cyly(INSERT_Y0 - 5, INSERT_Y0 + 1, x, zl + 18, 3.4);
        }
        for (xc = SLOT_X) hull() {
            cylz(xc - 4, INSERT_Y0 - 6.5, zl - 5, zl + 1, 3.6);
            cylz(xc + 4, INSERT_Y0 - 6.5, zl - 5, zl + 1, 3.6);
        }
    }
}

// ---------------------------------------------------------------- small parts
module butterfly_key() { bowtie(0, 0, "x", 0.15, 0, 2.8); }

module foot() {
    difference() {
        cylz(0, 0, 0, 10, 30, fn = 64, d2 = 26);
        cylz(0, 0, -1, 11, 3.4);
        cylz(0, 0, -1, 6, 6.8);
    }
}

// glue into the badge recess (1.5 deep), add your logo
module badge_plate() {
    box(0, 0, 0, BADGE_UP[2] - BADGE_UP[0] - 0.4, BADGE_UP[3] - BADGE_UP[1] - 0.4, 2.0);
}

// Removable 3.5" bay cage, screws to the floor behind a bay opening. Takes any
// 3.5" device (USB panel, floppy, card reader) via side slots. The rear 36 mm
// is raised so it can overhang the motherboard's front edge.
module bay_cage(x0) {
    x1 = x0 + BAY_W;
    y0 = CAGE_Y0; top = BAY_Z[1] + 4; zlow = 50.0;
    zs = BAY_Z[0] + 6.35;                                  // 3.5" device side-hole height
    difference() {
        union() {
            for (wx0 = [x0 - 3, x1]) {
                box(wx0, y0, FLOOR_T, wx0 + 3, y0 + 58, top);
                box(wx0, y0 + 57.9, zlow, wx0 + 3, y0 + 94, top);
            }
            box(x0 - 0.01, FRONT_T + 6, BAY_Z[0] - 4, x1 + 0.01, y0 + 94, BAY_Z[0]);   // shelf
            box(x0 - 12, y0, FLOOR_T, x0 - 2.99, y0 + 58, FLOOR_T + 3);                 // flanges
            box(x1 + 2.99, y0, FLOOR_T, x1 + 12, y0 + 58, FLOOR_T + 3);
        }
        for (x = [x0 - 7.5, x1 + 7.5], y = CAGE_HOLE_Y) cylz(x, y, FLOOR_T - 1, FLOOR_T + 4, 3.4);
        for (yy = [[14, 40], [46, 74], [80, 96]], xx = [[x0 - 4, x0 + 0.5], [x1 - 0.5, x1 + 4]]) hull() {
            cylx(xx[0], xx[1], y0 + yy[0], zs, 3.4);
            cylx(xx[0], xx[1], y0 + yy[1], zs, 3.4);
        }
    }
}

// Clip-in 3.5" bay cover with a JX drive face. Two snap hooks catch behind the
// front wall; squeeze them from inside to remove. Fits either bay.
module bay_blank(x0) {
    a0 = x0 + 0.2; a1 = x0 + BAY_W - 0.2;
    b0 = BAY_Z[0] + 0.2; b1 = BAY_Z[1] - 0.2;
    cx = (a0 + a1) / 2;
    difference() {
        union() {
            box(a0 - 1.2, 2.7, b0 - 1.2, a1 + 1.2, 3.5, b1 + 1.2);     // face, sits on the frame recess
            box(a0, 3.5, b0, a1, 18.0, b1);                             // body
        }
        box(cx - 11.5, 6.0, b1 - 2.6, cx + 11.5, 16.5, b1 + 1);         // hook pockets
        box(cx - 11.5, 6.0, b0 - 1, cx + 11.5, 16.5, b0 + 2.6);
        box(a0 + 8, 2.0, b1 - 9.5, a1 - 8, 4.2, b1 - 4.0);              // disk slot
        cyly(2.0, 5.5, a0 + 12, b0 + 5.5, 3.2);                         // LED
        box(a0 + 2.0, 6.0, b0 + 3.2, a1 - 2.0, 18.1, b1 - 3.2);         // hollow from the back
    }
    box(a1 - 26, 1.5, b0 + 2.5, a1 - 8, 2.71, b0 + 7.5);                // button
    for (top = [true, false]) {
        e = top ? b1 : b0;
        if (top) box(cx - 10, 6.2, b1 - 1.4, cx + 10, 18.0, b1);
        else box(cx - 10, 6.2, b0, cx + 10, 18.0, b0 + 1.4);
        hull() {                                                        // catch lip + ramp
            if (top) box(cx - 10, 6.2, e, cx + 10, 8.0, e + 1.0);
            else box(cx - 10, 6.2, e - 1.0, cx + 10, 8.0, e);
            box(cx - 10, 9.99, e - 0.01, cx + 10, 10.0, e + 0.01);
        }
    }
}

// Shelf + side rails for a standard 5.25" optical drive. Rests on ledges on the
// front and right walls; drive screws through the rail slots (adjust the drive
// forward/back until the bezel sits flush in the JX drive face).
module dvd_shelf() {
    x0 = ODD_CX - 79.0; x1 = W - SIDE_T - 0.6;
    zt = ODD_BOTTOM;
    rl0 = ODD_CX - 73.03 - 0.3 - 3; rr0 = ODD_CX + 73.03 + 0.3;
    zs = zt + 10.0;                                         // 5.25" side-hole height
    difference() {
        union() {
            difference() {
                box(x0, FRONT_T + 0.5, zt - SHELF_T, x1, 148.0, zt);
                box(ODD_OPEN[0] - 1, FRONT_T - 1, zt - SHELF_T - 1, ODD_OPEN[2] + 1, FRONT_T + 8.0, zt + 1);
            }
            box(rl0, 16, zt - 0.01, rl0 + 3, 130, zt + 20);
            box(rr0, 16, zt - 0.01, rr0 + 3, 130, zt + 20);
            box(rr0 + 2.99, 16, zt - 0.01, x1, 20, zt + 6);
            box(rr0 + 2.99, 126, zt - 0.01, x1, 130, zt + 6);
        }
        for (yy = [[52, 68], [84, 100]], xr = [rl0, rr0]) hull() {
            cylx(xr - 1, xr + 4, yy[0], zs, 3.4);
            cylx(xr - 1, xr + 4, yy[1], zs, 3.4);
        }
        for (s = SHELF_INSERTS) {
            cylz(s[0], s[1], zt - SHELF_T - 1, zt + 1, 3.4);
            cylz(s[0], s[1], zt - 1.7, zt + 0.01, 3.4, d2 = 6.8);  // countersink
        }
    }
}

// ---------------------------------------------------------------- switch labels
// OpenSCAD's text size is 0.72 x the em size, so `size` here is the em size.
// Each string is centred on its glyph bounds.
module text_2d(txt, cx, cz, size, font) {
    s = size * 0.72;
    tm = textmetrics(txt, size = s, font = font);
    translate([cx - (tm.position.x + tm.size.x / 2), cz - (tm.position.y + tm.size.y / 2)])
        text(txt, size = s, font = font);
}

// extrude a 2D (x, z) shape into the front face between y0 and y1
module face_solid(y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
}

function font_missing(font) =
    textmetrics("入On", size = 10, font = font) == textmetrics("入On", size = 10, font = "No Such Font JX");

// Switch labels on the housing's label strip, as 0.6 mm inlay solids. The same
// solids are cut from the base and exported as the inlay part.
module label_solids(style) {
    lx = (115 - PHOTO_X0) * PX + 0.6;                    // centre of the label strip
    z_on = H_TOTAL - (525 - PHOTO_Y0) * PX;              // 入 / "On" group
    z_off = H_TOTAL - (578 - PHOTO_Y0) * PX;             // 切 / "Off" group
    if (style == "JP") {
        if (font_missing(LABEL_FONT)) echo(str("WARNING: font '", LABEL_FONT, "' not found, labels use a fallback font"));
        face_solid(LABEL_Y[0], LABEL_Y[1]) {
            text_2d("入", lx - 0.6, z_on, 4.6, LABEL_FONT);
            text_2d("切", lx - 0.6, z_off, 4.6, LABEL_FONT);
        }
    } else if (style == "EN") {                          // IEC 60417: | = on, O = off
        if (font_missing(LABEL_FONT_EN)) echo(str("WARNING: font '", LABEL_FONT_EN, "' not found, labels use a fallback font"));
        face_solid(LABEL_Y[0], LABEL_Y[1]) {
            translate([lx - 0.45, z_on + 0.8]) square([0.9, 4.2]);
            text_2d("On", lx, z_on - 2.6, 3.8, LABEL_FONT_EN);
            text_2d("Off", lx, z_off + 2.6, 3.8, LABEL_FONT_EN);
            translate([lx, z_off - 3.3]) difference() { circle(2.3, $fn = 48); circle(1.4, $fn = 48); }
        }
    } else assert(style == "BLANK", str("unknown label style ", style));
}

// ---------------------------------------------------------------- power switch (BRS lever)
// case (y, z) of a lever point at radius r, angle a_off from the blade
function _pt(theta, r, a_off = 0.0) =
    [PSW_PIVOT[0] - r * cos(theta + a_off), PSW_PIVOT[1] + r * sin(theta + a_off)];

// The BRS lever in the case at blade angle theta. STL frame: profile in (x, z)
// around the axle at the origin, 20 mm wide along y, magnet on the y=20 face.
// Mapped: STL +x -> forward (-y), STL +z -> up, STL y -> case x.
module paddle_lever(theta = PSW_ON) {
    py = PSW_PIVOT[0]; pz = PSW_PIVOT[1];
    // untilted, the blade sits at its native angle; tilt about the axle
    translate([0, py, pz]) rotate([-(theta - LEVER_NATIVE_BLADE), 0, 0]) translate([0, -py, -pz])
        multmatrix([[0, 1, 0, PSW_X - 10.0], [-1, 0, 0, py], [0, 0, 1, pz], [0, 0, 0, 1]])
            import(LEVER_STL);
}

module paddle_slab() { box(PSW_X - 10.6, -20, 0, PSW_X + 10.6, FRONT_T + 0.5, 100); }

// Window through the channel wall: the lever's sweep between the stops (with
// 0.4 mm clearance). The blade root meets the window ends = hard stops. Hulled
// into a convex window (simple to print).
module paddle_slot() {
    intersection() {
        hull() for (dz = [-0.4, 0.0, 0.4]) translate([0, 0, dz])
            for (k = [0 : 14]) intersection() {
                paddle_lever(PSW_STOPS[0] + (PSW_STOPS[1] - PSW_STOPS[0]) * k / 14);
                paddle_slab();
            }
        paddle_slab();
    }
}

// The fixed magnets sit partly in the back of the front wall.
module paddle_wall_magnet_recesses() {
    for (t = [PSW_OFF, PSW_ON]) {
        m = _pt(t, norm(LEVER_MAG));
        cylx(PSW_X + 10.6, PSW_X + 10.6 + MAG_T + 0.4, m[0], m[1], MAG_D + 0.3);
    }
}

// extrude a polygon given in (y, z) along x from x0 to x1
module yz_extrude(pts, x0, x1) {
    multmatrix([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) linear_extrude(x1 - x0) polygon(pts);
}

// Cheeks carrying the M4 axle, the two latch magnets (right cheek, facing the
// lever's magnet) and the START microswitch behind/above the drum.
module paddle_frame() {
    X = PSW_X; py = PSW_PIVOT[0]; pz = PSW_PIVOT[1];
    cl = [-14.2, -10.4]; cr = [10.6, 14.6];               // cheek x ranges (lever is +-10)
    y0 = FRONT_T + 0.3;
    a_face = PSW_STOPS[0] - 75.0;                          // drum lower edge = blade - 75 deg
    zc = (PSW_SW[1] + PSW_SW[2]) / 2;
    difference() {
        union() {
            box(X + cl[0], y0, 7.0, X + cl[1], 46.0, 71.0);
            box(X + cr[0], y0, 7.0, X + cr[1], 46.0, 71.0);
            box(X + cl[0], 42.0, 7.0, X + cr[1], 46.0, 71.0);             // rear wall
            box(X + cl[0], y0, 7.0, X + cr[1], 46.0, 9.5);                // base
            for (e = PSW_EARS) {
                ex = e[0]; ez = e[1];
                x0 = ex < 0 ? X + ex - 5 : X + cr[1] - 0.01;
                x1 = ex < 0 ? X + cl[0] + 0.01 : X + ex + 5;
                if (ez < 30) box(x0, FRONT_T + 2.3, 7.0, x1, 16.0, ez + 5);
                else {
                    xc = ex < 0 ? X + cl[0] : X + cr[1];
                    hull() {
                        box(x0, FRONT_T + 2.3, ez - 5, x1, 16.0, ez + 5);
                        box(xc - 0.01, FRONT_T + 2.3, ez - 5 - abs(x1 - x0), xc + 0.01, 16.0, ez - 5);
                    }
                }
            }
            // 切 hard stop: the drum's lower edge lands on this block at PSW_STOPS[0]
            yz_extrude(concat([for (i = [0 : 12]) _pt(0, 17.3, a_face - 18.0 * i / 12)],
                              [for (i = [0 : 12]) _pt(0, 12.5, a_face - 18.0 + 18.0 * i / 12)]),
                       X + cl[1] - 0.01, X + cr[0] + 0.01);
        }
        cylx(X + cl[0] - 1, X + cr[1] + 1, py, pz, 4.1);                    // M4 axle
        for (t = [PSW_OFF, PSW_ON]) {                                        // latch magnets
            m = _pt(t, norm(LEVER_MAG));
            cylx(X + cr[0] - 0.01, X + cr[0] + MAG_T + 0.1, m[0], m[1], MAG_D + 0.2);
        }
        for (e = PSW_EARS) cyly(FRONT_T, 17, X + e[0], e[1], 3.4);
        // microswitch on its side between the cheeks, plunger facing forward, lever
        // tip hanging down in front of it where the drum's top edge arrives at START.
        // M2 screws through slots in both cheeks give +-3 mm front/back adjustment.
        for (hz = [zc - 4.75, zc + 4.75]) hull()
            for (y = [PSW_SW[0] + 2.0, PSW_SW[0] + 8.5]) cylx(X + cl[0] - 1, X + cr[1] + 1, y, hz, 2.4);
    }
}

// ---------------------------------------------------------------- DVD fascia
// JX-style faceplate for a standard 5.25" optical drive, in two pieces: a frame
// glued to the drive's fixed bezel and a strip glued to the moving tray front.
// Measure your drive and adjust DVD_* at the top. Both are positioned on the
// assembled case, with the drive pulled back by DVD_PLATE_T so the fascia sits
// in the JX drive face.
DVD_X0 = ODD_CX - DVD_BEZEL[0] / 2;
DVD_ZT = ODD_CZ + DVD_BEZEL[1] / 2;
DVD_YB = 1.6 + DVD_PLATE_T;                // plate back face (drive bezel front)
DVD_YF = DVD_YB - DVD_PLATE_T;
// photo-traced JX 5.25" drive face (photo px -> bezel mm)
DVD_FX = DVD_BEZEL[0] / (1380 - 832);
DVD_FZ = DVD_BEZEL[1] / (255 - 105);
function dvd_pr(px0, py0, px1, py1) =
    [(px0 - 832) * DVD_FX, (py0 - 105) * DVD_FZ, (px1 - 832) * DVD_FX, (py1 - 105) * DVD_FZ];
DVD_SLOT = dvd_pr(848, 155, 1365, 183);
DVD_DOOR = dvd_pr(935, 105, 1155, 255);
DVD_LEVER = dvd_pr(935, 107, 1070, 136);
DVD_KNOB = [(965 - 832) * DVD_FX, (121 - 105) * DVD_FZ];
DVD_JX_LED = [(1280 - 832) * DVD_FX, (130 - 105) * DVD_FZ];

// rectangle in bezel coords: b = [x0, from-top0, x1, from-top1]
module dvd_r(b, ya, yb) { box(DVD_X0 + b[0], ya, DVD_ZT - b[3], DVD_X0 + b[2], yb, DVD_ZT - b[1]); }

module dvd_tray_cut() {
    g = DVD_TRAY_GAP;
    dvd_r([DVD_TRAY[0] - g, DVD_TRAY[1] - g, DVD_TRAY[2] + g, DVD_TRAY[3] + g], DVD_YF - 3, DVD_YB + 1);
}

// raise the door panel + lever and recess the slot on children(0), only inside children(1)
module dvd_details() {
    yf = DVD_YF; bh = DVD_BEZEL[1];
    difference() {
        union() {
            children(0);
            intersection() {
                union() {
                    dvd_r([DVD_DOOR[0], 0.6, DVD_DOOR[2], bh - 0.6], yf - 0.6, yf + 0.01);
                    dvd_r(DVD_LEVER, yf - 1.4, yf + 0.01);
                }
                children(1);
            }
        }
        intersection() {
            union() {
                dvd_r(DVD_SLOT, yf - 2, yf + 1.2);
                cyly(yf - 2, yf - 0.4, DVD_X0 + DVD_KNOB[0], DVD_ZT - DVD_KNOB[1], 3.0);
            }
            children(1);
        }
    }
}

module dvd_fascia_frame() {
    yf = DVD_YF; yb = DVD_YB; bw = DVD_BEZEL[0]; bh = DVD_BEZEL[1];
    difference() {
        dvd_details() {
            difference() { dvd_r([0, 0, bw, bh], yf, yb); dvd_tray_cut(); }
            difference() { box(DVD_X0 - 5, yf - 5, DVD_ZT - bh - 5, DVD_X0 + bw + 5, yb + 5, DVD_ZT + 5); dvd_tray_cut(); }
        }
        dvd_r(DVD_EJECT, yf - 3, yb + 1);                                                 // press the real eject button
        cyly(yf - 2, yf + 1.0, DVD_X0 + DVD_JX_LED[0], DVD_ZT - DVD_JX_LED[1], 3.0);      // JX LED: paint it red
        if (len(DVD_ACT_LED) == 2)
            cyly(yf - 3, yb + 1, DVD_X0 + DVD_ACT_LED[0], DVD_ZT - DVD_ACT_LED[1], 2.5);
    }
}

module dvd_fascia_tray() {
    dvd_details() {
        dvd_r(DVD_TRAY, DVD_YF, DVD_YB);
        dvd_r(DVD_TRAY, DVD_YF - 3, DVD_YB + 1);
    }
}

// 1.2 mm flat template of the board: hole positions + I/O and slot marks. Lay
// it on your motherboard before printing anything big. The halves overlap by
// 12 mm so they can be taped together.
module fit_template(half) {
    u0 = half == 0 ? 0.0 : BOARD_W / 2 - 6;
    u1 = half == 0 ? BOARD_W / 2 + 6 : BOARD_W;
    difference() {
        box(u0, 0, 0, u1, BOARD_D, 1.2);
        for (h = ATX_HOLES) cylz(h[0], h[1], -1, 2, 3.4);
        // lightening windows
        box(u0 + 12, 30, -1, u1 - 12, 140, 2);
        box(u0 + 12, 182, -1, u1 - 12, 225, 2);
        // rear-edge marks: I/O aperture edges and bracket centres (V notches)
        for (u = concat([IO_U0, IO_U0 + IO_W], [for (i = [0 : N_SLOTS - 1]) SLOT7_U - i * SLOT_PITCH]))
            extrude_poly([[u - 2, -1], [u + 2, -1], [u, 4]], -1, 2);
    }
}

// ---------------------------------------------------------------- output
module quadrant(name) {
    q = QUADRANTS[search([name], QUADRANTS, 1, 0)[0]];
    box(q[1], q[3], -10, q[2], q[4], 300);
}

// Assembled-case solids, by name (used by build.py, fitcheck.py and render.py).
module solid(name) {
    if (name == "shell_JP") lower_shell("JP");
    else if (name == "shell_EN") lower_shell("EN");
    else if (name == "shell_BLANK") lower_shell("BLANK");
    else if (name == "lid") lid();
    else if (name == "slot_insert") slot_insert();
    else if (name == "io_insert") io_insert();
    else if (name == "bracket_rail") bracket_rail();
    else if (name == "bay_cage_B") bay_cage(BAY_B_X0);
    else if (name == "bay_cage_A") bay_cage(BAY_A_X0);
    else if (name == "bay_blank_B") bay_blank(BAY_B_X0);
    else if (name == "bay_blank_A") bay_blank(BAY_A_X0);
    else if (name == "dvd_shelf") dvd_shelf();
    else if (name == "power_switch_frame") paddle_frame();
    else if (name == "dvd_fascia_frame") dvd_fascia_frame();
    else if (name == "dvd_fascia_tray") dvd_fascia_tray();
    else if (name == "labels_JP") label_solids("JP");
    else if (name == "labels_EN") label_solids("EN");
    else if (name == "lever") paddle_lever(lever_angle);
    else assert(false, str("unknown solid ", name));
}

// Printable parts, turned for printing. build.py drops each onto the bed;
// the front-left base + label inlays keep the case coordinates so each pair
// loads as one two-colour object.
module print_part(name) {
    if (name == "base_front_left_JP") intersection() { solid("shell_JP"); quadrant("front_left"); }
    else if (name == "base_front_left_EN") intersection() { solid("shell_EN"); quadrant("front_left"); }
    else if (name == "base_front_left_BLANK") intersection() { solid("shell_BLANK"); quadrant("front_left"); }
    else if (name == "labels_JP_inlay") solid("labels_JP");
    else if (name == "labels_EN_inlay") solid("labels_EN");
    // the labels are all in the front-left quadrant, so the others don't need the label font
    else if (name == "base_front_right") intersection() { solid("shell_BLANK"); quadrant("front_right"); }
    else if (name == "base_rear_left") intersection() { solid("shell_BLANK"); quadrant("rear_left"); }
    else if (name == "base_rear_right") intersection() { solid("shell_BLANK"); quadrant("rear_right"); }
    // lid tiles print upside down (top face on the bed)
    else if (name == "lid_front_left") rotate([180, 0, 0]) intersection() { lid(); quadrant("front_left"); }
    else if (name == "lid_front_right") rotate([180, 0, 0]) intersection() { lid(); quadrant("front_right"); }
    else if (name == "lid_rear_left") rotate([180, 0, 0]) intersection() { lid(); quadrant("rear_left"); }
    else if (name == "lid_rear_right") rotate([180, 0, 0]) intersection() { lid(); quadrant("rear_right"); }
    else if (name == "rear_slot_panel") rotate([-90, 0, 0]) slot_insert();     // outer face down
    else if (name == "rear_io_panel") rotate([-90, 0, 0]) io_insert();         // outer face down (thin rim on top side)
    else if (name == "bracket_rail") rotate([-90, 0, 0]) bracket_rail();
    else if (name == "butterfly_key_x9") butterfly_key();
    else if (name == "foot_x6") foot();
    else if (name == "badge_plate_x2") badge_plate();
    else if (name == "bay_cage_35_x2") rotate([90, 0, 0]) bay_cage(BAY_B_X0);      // front face down
    else if (name == "bay_blank_clip_x2") rotate([-90, 0, 0]) bay_blank(BAY_B_X0); // back face down
    else if (name == "dvd_shelf") dvd_shelf();
    else if (name == "power_switch_frame") paddle_frame();                    // base down
    else if (name == "dvd_fascia_frame") rotate([-90, 0, 0]) dvd_fascia_frame(); // back face down
    else if (name == "dvd_fascia_tray") rotate([-90, 0, 0]) dvd_fascia_tray();
    else if (name == "fit_template_left") fit_template(0);
    else if (name == "fit_template_right") fit_template(1);
    else if (len(name) > 4 && name[0] == "a" && name[1] == "s" && name[2] == "m" && name[3] == "_")
        solid(chr([for (i = [4 : len(name) - 1]) ord(name[i])]));
    else assert(false, str("unknown part ", name));
}

if (part == "assembly") {
    solid("shell_JP"); lid(); slot_insert(); io_insert(); bracket_rail();
} else if (part == "assembly_open") {
    solid("shell_JP"); slot_insert(); io_insert(); bracket_rail();
} else if (part != "none") print_part(part);   // "none": used as a library by fitcheck.scad / render.scad
