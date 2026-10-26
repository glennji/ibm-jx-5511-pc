// Fit check for fitcheck.py: the printed parts in their assembled positions,
// plus envelope boxes for the hardware that goes inside. Renders the overlap
// of fit_a and fit_b; an empty result means they don't touch.
include <jx_case.scad>
part = "none";

fit_a = "shell";
fit_b = "lid";

// printed parts that sit in the case together
FIT_SOLIDS = ["shell", "lid", "slot", "io", "rail", "cageB", "cageA", "blankB", "blankA", "shelf"];

// hardware envelopes: [name, [x0, y0, z0, x1, y1, z1]], checked against every
// printed part except the bay blanks and the bracket rail
FIT_ENVELOPES = [
    ["DVD body 146x41.3x185", [ODD_CX - 73.0, 13, ODD_BOTTOM + 0.05, ODD_CX + 73.0, 198, ODD_BOTTOM + 41.3]],
    ["DVD bezel 148x42.3", [ODD_CX - 74.0, 1.5, ODD_CZ - 21.15, ODD_CX + 74.0, 13, ODD_CZ + 21.15]],
    ["floppy in A (147 deep)", [BAY_A_X0 + 0.3, 3.6, BAY_Z[0] + 0.05, BAY_A_X0 + 101.9, 151, BAY_Z[0] + 25.4]],
    ["USB panel in B (60 deep)", [BAY_B_X0 + 0.3, 3.6, BAY_Z[0] + 0.05, BAY_B_X0 + 101.9, 64, BAY_Z[0] + 25.4]],
    ["PSU 150 deep", [PSU_X0, 321 - 150, FLOOR_T, PSU_X0 + 150, 321, FLOOR_T + 86]],
    ["board", [BOARD_X0, BOARD_REAR_Y - BOARD_D, BOARD_BOTTOM, BOARD_X0 + BOARD_W, BOARD_REAR_Y, BOARD_TOP]],
    ["cooler 160 tall (socket area)", [BOARD_X0 + 140, 150, BOARD_TOP, BOARD_X0 + 260, 300, BOARD_TOP + 160]],
    ["GPU 300L x 160H", [SLOT_X[3] - 10, INSERT_Y0 - 300, BOARD_TOP + 3, SLOT_X[0] + 9, INSERT_Y0 - 0.5, BOARD_TOP + 160]],
    ["board front-edge connectors 30mm", [BOARD_X0, BOARD_REAR_Y - BOARD_D, BOARD_TOP, BOARD_X0 + BOARD_W,
                                          BOARD_REAR_Y - BOARD_D + 30, BOARD_TOP + 30]],
];

module fit_solid(name) {
    env = search([name], FIT_ENVELOPES, 1, 0)[0];
    if (name == "shell") lower_shell("BLANK");     // labels don't affect clearances
    else if (name == "lid") lid();
    else if (name == "slot") slot_insert();
    else if (name == "io") io_insert();
    else if (name == "rail") bracket_rail();
    else if (name == "cageB") bay_cage(BAY_B_X0);
    else if (name == "cageA") bay_cage(BAY_A_X0);
    else if (name == "blankB") bay_blank(BAY_B_X0);
    else if (name == "blankA") bay_blank(BAY_A_X0);
    else if (name == "shelf") dvd_shelf();
    else if (name == "parts") {
        for (s = FIT_SOLIDS) if (s != "blankB" && s != "blankA" && s != "rail") fit_solid(s);
    } else if (env != []) let (b = FIT_ENVELOPES[env][1]) box(b[0], b[1], b[2], b[3], b[4], b[5]);
    else assert(false, str("unknown fit solid ", name));
}

if (fit_a == "info") {
    echo(fit_solids = FIT_SOLIDS, envelopes = [for (e = FIT_ENVELOPES) e[0]]);
    echo(dvd_top = ODD_BOTTOM + 41.3, lid_rib_bottom = WALL_TOP - 8, bezel_open = ODD_OPEN);
    echo(bays_B_A_x0 = [BAY_B_X0, BAY_A_X0], bay_z = BAY_Z);
} else if (fit_b == "") fit_solid(fit_a);
else intersection() { fit_solid(fit_a); fit_solid(fit_b); }
