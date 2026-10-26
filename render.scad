// Preview scenes for render.py (PNG export). Pick one with `scene`.
include <jx_case.scad>
part = "none";

scene = "front"; // [front, flat, dvd, rear, open, exploded, power_on, power_off, power_inside, labels_JP, labels_EN, labels_BLANK]

/* [Hidden] */
GREY = CASE_COLOUR;                                   // base, covers, DVD fascia (CASE_COLOUR is in jx_case.scad)
LIDC = is_string(CASE_COLOUR) ? CASE_COLOUR : CASE_COLOUR * 1.06;  // lid, a touch lighter
INS = is_string(CASE_COLOUR) ? CASE_COLOUR : CASE_COLOUR * 0.85;   // rear panels, bay cages
ACC = [0.80, 0.60, 0.15]; GREEN = [0.20, 0.50, 0.25]; PSUC = [0.55, 0.55, 0.55];
DVDC = [0.16, 0.16, 0.17]; DEV = [0.22, 0.22, 0.24]; BRS_RED = [0.78, 0.13, 0.10];
SW = [0.15, 0.15, 0.17]; MAG = [0.65, 0.65, 0.7]; WHITE = [0.93, 0.93, 0.9];

module case_closed() {
    color(GREY) lower_shell("JP");
    color(LIDC) lid();
}

// bay cages, covers, DVD drive + fascia, USB panel
module inside() {
    cx = ODD_CX; zb = ODD_BOTTOM;
    color(INS) { bay_cage(BAY_B_X0); bay_cage(BAY_A_X0); }
    color(GREY) bay_blank(BAY_A_X0);
    color(ACC) dvd_shelf();
    color(DVDC) {
        box(cx - 73.0, 13, zb, cx + 73.0, 190, zb + 41.3);
        box(cx - 74.0, 1.6 + DVD_PLATE_T, ODD_CZ - 21.15, cx + 74.0, 13, ODD_CZ + 21.15);
    }
    color(DEV) box(BAY_B_X0 + 0.3, 3.6, BAY_Z[0] + 0.05, BAY_B_X0 + 101.9, 60, BAY_Z[0] + 25.4);
    color(GREY) { dvd_fascia_frame(); dvd_fascia_tray(); }
}

// Camera from an eye position (relative to the target) and a target point,
// as OpenSCAD's $vpt / $vpr / $vpd / $vpf.
function camera(eye_off, target, fov = 30) =
    [target, [acos(eye_off.z / norm(eye_off)), 0, atan2(eye_off.x, -eye_off.y)], norm(eye_off), fov];

TGT = [W / 2, D / 2, 80];
// OpenSCAD lights the scene from the camera's left, so views of the front look
// from the front-right to keep the front face lit.
CAMERAS = [
    ["front", camera([520, -1050, 520], TGT, 19)],
    ["flat", camera([500, -3000, 450], [W / 2, 0, (WALL_TOP + 3) / 2], 7)],
    ["dvd", camera([180, -900, 260], [ODD_CX, 0, ODD_CZ - 5], 17)],
    ["rear", camera([-600, 1050, 420], TGT, 19)],
    ["open", camera([300, -800, 950], TGT, 22)],
    ["exploded", camera([650, -1100, 760], TGT + [0, 0, 40], 23)],
    // the switch sits in a channel, so look at it from the left even though the face goes darker
    ["power_on", camera([-170, -330, 110], [PSW_X + 6, 0, 36], 19)],
    ["power_off", camera([-170, -330, 110], [PSW_X + 6, 0, 36], 19)],
    ["power_inside", camera([-340, 30, 60], [PSW_X, 20, 36], 24)],
    ["labels_JP", camera([40, -420, 40], [PSW_X - 10, 0, 36], 10)],
    ["labels_EN", camera([40, -420, 40], [PSW_X - 10, 0, 36], 10)],
    ["labels_BLANK", camera([40, -420, 40], [PSW_X - 10, 0, 36], 10)],
];
CAM = CAMERAS[search([scene], CAMERAS, 1, 0)[0]][1];
$vpt = CAM[0]; $vpr = CAM[1]; $vpd = CAM[2]; $vpf = CAM[3];

module rear_inserts() { color(INS) { slot_insert(); io_insert(); } }

// slice off the switch's left cheek to show the inside
module power_cut() { intersection() { box(PSW_X - 10.3, -40, -5, PSW_X + 40, 60, 100); children(); } }

module power_inside() {
    X = PSW_X;
    color(GREY) power_cut() lower_shell("JP");
    color(ACC) power_cut() paddle_frame();
    color(BRS_RED) power_cut() paddle_lever(PSW_ON);
    color(SW) power_cut() box(X - 3.2, PSW_SW[0], PSW_SW[1], X + 3.2, PSW_SW[0] + 10.2, PSW_SW[2]);
    color(MAG) power_cut() for (t = [PSW_OFF, PSW_ON]) let (m = _pt(t, norm(LEVER_MAG)))
        cylx(X + 10.6, X + 13.6, m[0], m[1], 8.0);
}

if (scene == "front" || scene == "flat") {
    case_closed(); rear_inserts(); inside();
} else if (scene == "dvd") {
    case_closed(); inside();
} else if (scene == "rear") {
    case_closed(); rear_inserts(); color(ACC) bracket_rail();
} else if (scene == "open") {
    color(GREY) lower_shell("JP"); rear_inserts(); color(ACC) bracket_rail(); inside();
    color(GREEN) box(BOARD_X0, BOARD_REAR_Y - BOARD_D, BOARD_BOTTOM, BOARD_X0 + BOARD_W, BOARD_REAR_Y, BOARD_TOP);
    color(PSUC) box(PSU_X0, 321 - 150, FLOOR_T, PSU_X0 + 150, 321, FLOOR_T + 86);
    color([0.55, 0.12, 0.12])
        box(SLOT_X[0] - 40, INSERT_Y0 - 280, BOARD_TOP + 2, SLOT_X[0] + 4, INSERT_Y0 - 1, BOARD_TOP + 120);
} else if (scene == "exploded") {
    for (q = QUADRANTS) {
        dx = q[1] == 0 ? -30 : 30; dy = q[3] == 0 ? -30 : 30;
        translate([dx, dy, 0]) color(GREY) intersection() { lower_shell("JP"); quadrant(q[0]); }
        translate([dx, dy, 110]) color(LIDC) intersection() { lid(); quadrant(q[0]); }
    }
    translate([0, 110, 0]) rear_inserts();
    translate([0, 75, 0]) color(ACC) bracket_rail();
} else if (scene == "power_on" || scene == "power_off") {
    case_closed();
    color(BRS_RED) paddle_lever(scene == "power_on" ? PSW_ON : PSW_OFF);
} else if (scene == "power_inside") {
    power_inside();
} else if (scene == "labels_JP" || scene == "labels_EN" || scene == "labels_BLANK") {
    style = scene == "labels_JP" ? "JP" : scene == "labels_EN" ? "EN" : "BLANK";
    color(GREY) lower_shell(style);
    color(BRS_RED) paddle_lever(PSW_ON);
    color(WHITE) label_solids(style);
}
