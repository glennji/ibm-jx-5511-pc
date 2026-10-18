# JX-style ATX desktop case (3D printable)

A low, wide, dark-grey desktop box modelled on the front of an IBM JX (5511) system unit with its expansion unit stacked on top, traced from a photo and scaled to fit ATX. It takes a full ATX board and a standard ATX PSU, and every part fits a 256 × 256 mm bed (largest part 247.5 mm).

**Outside size:** 495 W × 324 D × 165 H mm. It is wider and taller than a real JX, because ATX needs that room.

## Before you print anything big: run the fit check

Print `fit_template_left` and `fit_template_right` first. They are 1.2 mm thick and take about 30 minutes each. Tape them together and lay them on your motherboard.

- **All 9 holes should line up with the board's mounting holes.**
- **The V-notches on the rear edge** mark the left and right edges of the I/O shield and the centre of each expansion bracket. They should line up with your board's I/O shield and slots.

The hole pattern is ATX standard, so it should match. The I/O shield and slot positions are best estimates, so check them. If they are off, measure from the board's slot-side edge, then edit these values near the top of `jx_case.py` and rerun:

| Parameter | Meaning | Current |
|---|---|---|
| `IO_U0` | Slot-side board edge to left edge of the I/O shield opening | 146.0 mm |
| `SLOT7_U` | Slot-side board edge to centre of the bracket nearest the I/O | 131.8 mm |
| `RAIL_LEDGE_Z` | Height where card bracket flanges rest (also adjustable ±6 mm on the rail) | board top + 108 mm |

To regenerate: `pip install manifold3d numpy`, then `python3 jx_case.py`.

## Parts to print (`stl/`)

All parts are already oriented for printing, and none need supports except where noted below.

| File | Qty | Notes |
|---|---|---|
| base_front_left / front_right / rear_left / rear_right | 1 each | Floor plus walls, printed floor-down. The front ones carry the JX face. |
| lid_front_left / front_right / rear_left / rear_right | 1 each | Printed top face down. |
| rear_slot_panel | 1 | Expansion slot panel. |
| rear_io_panel | 1 | I/O shield opening (with a 1.2 mm rim so the shield clips in) and an 80 mm exhaust fan mount. |
| bracket_rail | 1 | Card bracket screw ledge. Also ties the two rear panels together. |
| butterfly_key_x9 | 9 | Glue into the floor seams (CA or epoxy). |
| foot_x6 | 6 | Feet. |
| badge_plate_x2 | 2 | Blank plates for the two badge recesses (one per "unit"). Put your logo on these. |
| drive_a_face | 1 | JX-style drive face that plugs the 3.5" bay (drive "A") if you leave it empty. Glue or tape it in from inside. |
| fit_template_left / right | 1 each | Fit check, see above. |

- **Material:** PETG or ASA is recommended, since PLA can soften near a hot GPU or PSU. Charcoal grey matches the JX.
- **Settings:** 3 walls, 15–20 % infill.
- **Filament:** roughly 2 kg in total.
- **Two openings bridge more than 100 mm:** the front 3.5" bay opening and the PSU opening. Most printers bridge these acceptably, or you can paint supports on just those two openings.

## Hardware

- **Motherboard:** 9 × M3 10 mm female-female brass standoffs. Use 9 × M3×8 screws from under the floor and 9 × M3×6 screws through the board.
- **Heat-set inserts:** 22 × M3 (short type, 4.0 mm hole). That covers 14 lid bosses, 6 feet and 2 for the I/O panel lip.
- **Seam bolts:** 8 × M3×20 with nuts (front and side wall seams).
- **Lid bolts:** 8 × M3×10 with nuts (lid seam ribs) and 14 × M3×8 countersunk (lid to walls).
- **Rear panels:** 9 × M3×12 with nuts (6 at the columns, 3 for the rail) and 2 × M3×8 (I/O panel lip to floor).
- **Feet:** 6 × M3×10.
- **Fans:** 2 × 92 mm intake fans on the left side, aimed at the GPU, and 1 × 80 mm exhaust on the rear. All are optional.
- **Front panel:** a momentary switch with a 13 × 19 mm panel cut-out (KCD1 size, sold as "momentary rocker"), fitted in the JX power-switch housing. The square IR window takes a piece of smoked acrylic with the power LED behind it. A 3 mm HDD LED fits either the upper drive or drive B. Wire them to the board's front-panel header.

## Assembly order

1. **Join the base quadrants.** Push in heat-set inserts first. Glue the butterfly keys into the floor seams, then bolt the wall seam tabs. Do front-left to front-right and rear-left to rear-right, then join the front and rear halves.
2. **Fit the standoffs** from underneath, then the feet.
3. **Fit the PSU** from inside, with 4 screws through the rear wall. The rear holes suit fan-up or fan-down mounting; there are vents in the lid and floor for either.
4. **Fit the rear panels.** Bolt them to the columns either side and to the floor lip, then add the bracket rail.
5. **Fit the board.** Install a card, set the rail height so the bracket flange sits flat, and tighten.
6. **Fit the lid.** Bolt the 4 tiles together at the ribs, then screw it down.

## Clearances

- **CPU cooler:** up to about 133 mm. The lid seam rib runs over the CPU area, so use a low-profile cooler.
- **GPU height:** up to about 140 mm above the board. Where the lid rib crosses, the limit is about 133 mm.
- **GPU length:** up to about 300 mm.
- **Side fans:** the 25 mm side fans take up the space of the bottom (7th) slot. Use 15 mm slim fans if you need that slot.
- **PSU:** standard ATX, up to 160 mm deep.
- **Front 3.5" bay (drive A):** suits a card reader or USB panel, mounted on a shelf with side screw holes.
