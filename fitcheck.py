import jx_case as J
B = J.box
shell, lid = J.lower_shell(), J.lid()
dA = J.BAY_A_X0 - J.BAY_B_X0
solids = {"shell": shell, "lid": lid, "slot": J.slot_insert(), "io": J.io_insert(), "rail": J.bracket_rail(),
          "cageB": J.bay_cage(J.BAY_B_X0), "cageA": J.bay_cage(J.BAY_A_X0),
          "blankB": J.bay_blank(J.BAY_B_X0), "blankA": J.bay_blank(J.BAY_A_X0), "shelf": J.dvd_shelf()}
n = list(solids)
for i in range(len(n)):
    for j in range(i + 1, len(n)):
        v = (solids[n[i]] ^ solids[n[j]]).volume()
        if v > 0.01:
            print("OVERLAP", n[i], n[j], round(v, 2))
cx, zb = J.ODD_CX, J.ODD_BOTTOM
env = {
    "DVD body 146x41.3x185": B(cx - 73.0, 13, zb + 0.05, cx + 73.0, 198, zb + 41.3),
    "DVD bezel 148x42.3": B(cx - 74.0, 1.5, J.ODD_CZ - 21.15, cx + 74.0, 13, J.ODD_CZ + 21.15),
    "floppy in A (147 deep)": B(J.BAY_A_X0 + 0.3, 3.6, J.BAY_Z[0] + 0.05, J.BAY_A_X0 + 101.9, 151, J.BAY_Z[0] + 25.4),
    "USB panel in B (60 deep)": B(J.BAY_B_X0 + 0.3, 3.6, J.BAY_Z[0] + 0.05, J.BAY_B_X0 + 101.9, 64, J.BAY_Z[0] + 25.4),
    "PSU 150 deep": B(J.PSU_X0, 321 - 150, J.FLOOR_T, J.PSU_X0 + 150, 321, J.FLOOR_T + 86),
    "board": B(J.BOARD_X0, J.BOARD_REAR_Y - J.BOARD_D, J.BOARD_BOTTOM, J.BOARD_X0 + J.BOARD_W, J.BOARD_REAR_Y, J.BOARD_TOP),
    "cooler 160 tall (socket area)": B(J.BOARD_X0 + 140, 150, J.BOARD_TOP, J.BOARD_X0 + 260, 300, J.BOARD_TOP + 160),
    "GPU 300L x 160H": B(J.SLOT_X[3] - 10, J.INSERT_Y0 - 300, J.BOARD_TOP + 3, J.SLOT_X[0] + 9, J.INSERT_Y0 - 0.5, J.BOARD_TOP + 160),
    "board front-edge connectors 30mm": B(J.BOARD_X0, J.BOARD_REAR_Y - J.BOARD_D, J.BOARD_TOP, J.BOARD_X0 + J.BOARD_W, J.BOARD_REAR_Y - J.BOARD_D + 30, J.BOARD_TOP + 30),
}
allm = J.union([v for k, v in solids.items() if not k.startswith("blank") and k != "rail"])
for k, e in env.items():
    print(f"{k:34s} clash {round((allm ^ e).volume(), 2)}")
print("floppy vs PSU150", round((env["floppy in A (147 deep)"] ^ env["PSU 150 deep"]).volume(), 1))
print("DVD top", round(zb + 41.3, 2), "lid rib bottom", J.WALL_TOP - 8, " bezel open", [round(v, 1) for v in J.ODD_OPEN])
print("bays B/A x0", round(J.BAY_B_X0, 1), round(J.BAY_A_X0, 1), "z", [round(v, 1) for v in J.BAY_Z])
print("components per part:", {k: len(v.decompose()) for k, v in solids.items()})
