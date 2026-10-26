# JX-style ATX desktop case (3D printable)

A dark-grey desktop box modelled on the front of an IBM JX (5511) system unit with its expansion unit stacked on top. The front is traced from a photo and scaled uniformly, so it keeps the JX's proportions. It takes a full ATX board, a standard ATX PSU, a 5.25" optical drive and two 3.5" bay devices. Every part fits a 256 × 256 mm bed (largest part 247.5 mm).

**Outside size:** 495 W × 324 D × 199 H mm, the same width-to-height ratio as the photo (about 2.49 : 1).

## Before you print anything big: run the fit check

Print `fit_template_left` and `fit_template_right` first. They are 1.2 mm thick and take about 30 minutes each. Tape them together and lay them on your MSI board.

- **All 9 holes should line up with the board's mounting holes.**
- **The V-notches on the rear edge** mark the left and right edges of the I/O shield and the centre of each expansion bracket. They should line up with your board's I/O shield and slots.

The hole pattern is ATX standard, so it should match. The I/O shield and slot positions are best estimates, so check them. If they are off, measure from the board's slot-side edge, then change these values at the top of `jx_case.scad` (they're also in the OpenSCAD Customizer) and rebuild:

| Parameter | Meaning | Current |
|---|---|---|
| `IO_U0` | Slot-side board edge to left edge of the I/O shield opening | 146.0 mm |
| `SLOT7_U` | Slot-side board edge to centre of the bracket nearest the I/O | 131.8 mm |
| `RAIL_LEDGE_ABOVE_BOARD` | Height above the board top where card bracket flanges rest (also adjustable ±6 mm on the rail) | 108 mm |
| `GROOVE_D` | Depth of the line between the two "units" | 4 mm |
| `EDGE_R` | Radius of the rounded top edge and of both lips of the groove | 2.5 mm |

## Building

The model is `jx_case.scad`. You need [OpenSCAD](https://openscad.org) 2025 or later (a development snapshot), which has the fast Manifold backend and `textmetrics()`, plus Python 3. The scripts use only the standard library.

- **`python3 build.py`** renders every part into `stl/`, oriented for printing and dropped onto the bed, then prints a size and volume report. It takes a few seconds. Use `python3 build.py <outdir> [part ...]` to build only some parts.
- **`python3 fitcheck.py`** checks clearances. It intersects every pair of printed parts in their assembled positions, and every hardware envelope (board, PSU, GPU, cooler, drives) against the case. It reports any overlap with its volume, and any part that has split into separate pieces.
- **`python3 render.py [scene ...]`** writes the `preview_*.png` images (`all` renders every scene). The scenes and cameras are in `render.scad`. The case colour is `CASE_COLOUR` in `jx_case.scad` (charcoal by default), used both here and when you view a part in the OpenSCAD GUI; change it there, or pass `-D 'CASE_COLOUR="DimGray"'` to `openscad`.

To look at one part, open `jx_case.scad` in OpenSCAD and pick it in the Customizer's `part` list. `asm_*` entries show a part in its assembled position. If `openscad` isn't on your PATH, set `OPENSCAD=/path/to/openscad`.

**Label fonts:** the JP labels use IPA Gothic (`brew install --cask font-ipafont` on macOS, `fonts-ipafont-gothic` on Debian/Ubuntu), and the EN labels use Liberation Sans Bold. If a font is missing, OpenSCAD substitutes another one that may lack the 入/切 glyphs, so `build.py` refuses to write the labelled parts until the font is installed or `LABEL_FONT` / `LABEL_FONT_EN` names one you have.

To change the front, edit the photo-pixel boxes passed to `P()` in `front_recesses()`, `front_raises()` and `front_through()`.

## Front panel layout

**Upper unit**

- **5.25" bay:** a working bay for any standard 5.25" optical drive, such as a DVD-RW. The drive's own bezel shows in the middle of the JX drive face, between the two end blocks.
- **Cosmetic details:** the badge recess and the blank cover panel.

**Lower unit**

- **Drive B (left):** a working 3.5" bay intended for a USB front panel.
- **Drive A (right):** a working 3.5" bay for a floppy drive or card reader.
- **Clip-in covers:** each bay has a JX-style cover that snaps in. The covers are interchangeable, so you can leave either bay empty.
- **LED holes:** two 3 mm holes sit below the drive bays, for the HDD LED and a spare.
- **Power switch:** Axeman's Big Red Switch lever (IBM XT style), used unmodified, set into the JX switch channel with the 入 and 切 labels on the left. Magnets hold it at 切 and 入, and pushing past 入 is a spring-back START. See *Power switch* below.
- **Power LED window:** the square IR window takes a piece of smoked acrylic with the power LED behind it.
- **Cartridge strip:** two cartridge doors and the mode-switch slot. These are cosmetic.

## Parts to print (`stl/`)

All parts are already oriented for printing, and none need supports except where noted below.

| File | Qty | Notes |
|---|---|---|
| base_front_left_JP / _EN / _BLANK | pick 1 | Front-left floor and walls, carrying the switch labels. JP = 入 / 切, EN = IEC "| On" / "Off O", BLANK = no labels (for stickers or transfers). |
| labels_JP_inlay / labels_EN_inlay | 1 (with JP or EN) | The labels as 0.6 mm flush inlays, for a second AMS colour. See *Two-colour labels* below. |
| base_front_right / rear_left / rear_right | 1 each | Floor plus walls, printed floor-down. The front one carries the rest of the JX face. |
| lid_front_left / front_right / rear_left / rear_right | 1 each | Printed top face down. |
| rear_slot_panel | 1 | Expansion slot panel. |
| rear_io_panel | 1 | I/O shield opening (with a 1.2 mm rim so the shield clips in) and an 80 mm exhaust fan mount. |
| bracket_rail | 1 | Card bracket screw ledge. Also ties the two rear panels together. |
| bay_cage_35_x2 | 2 | 3.5" bay cages, screwed to the floor behind drives A and B. They're removable, so you can fit a device on the bench. |
| bay_blank_clip_x2 | 2 | Clip-in bay covers with the JX drive face. Squeeze the two hooks from inside to remove one. |
| dvd_shelf | 1 | Shelf and side rails for the optical drive. Rests on ledges on the front and right walls. |
| dvd_fascia_frame | 1 | JX drive face for the optical drive: glue it onto the drive's fixed bezel. |
| dvd_fascia_tray | 1 | Matching strip: glue it onto the tray front so the slot line continues when the tray is closed. |
| power_switch_frame | 1 | Holds the M4 axle, the two latch magnets, the 切 stop and the START microswitch. Screws to 4 bosses behind the front wall. |
| third_party/BRS_Lever.stl | 1 | Axeman's lever, included unmodified (CC BY-NC-SA 4.0, see `third_party/README.md`). Print in red. |
| butterfly_key_x9 | 9 | Glue into the floor seams (CA or epoxy). |
| foot_x6 | 6 | Feet. |
| badge_plate_x2 | 2 | Blank plates for the two badge recesses. Put your logo on these. |
| fit_template_left / right | 1 each | Fit check, see above. |

- **Material:** PETG or ASA is recommended, since PLA can soften near a hot GPU or PSU. Charcoal grey matches the JX.
- **Settings:** 3 walls, 15–20 % infill. Print the clip-in covers in PETG so the hooks flex instead of snapping.
- **Filament:** roughly 2.5–3 kg in total.
- **Long bridges:** the tops of the front openings bridge 100–150 mm (the 5.25" opening, the two 3.5" openings and the PSU opening). Most printers manage this, or you can paint supports on just those openings.

## DVD fascia

The optical drive can wear a JX-style front. The frame carries the door panel, the lever, the slot line and a small LED recess (paint it red). The tray strip carries the middle of the slot line, and it moves out with the tray. A cut-out leaves the drive's real eject button reachable, and a 2.5 mm hole lets the drive's activity light show through.

**Tray and button positions differ between drive models, so measure yours first.** Measure from the top-left corner of the bezel, then change these values at the top of `jx_case.scad` and rebuild:

| Parameter | Meaning | Default |
|---|---|---|
| `DVD_TRAY` | Tray front: left, top, right, bottom (mm from the top-left corner) | 10, 8, 138, 22.5 |
| `DVD_EJECT` | Eject button opening | 124, 31, 140, 37 |
| `DVD_ACT_LED` | Drive activity LED hole (`[]` to skip) | 115, 34 |

Both plates are 2 mm thick, so mount the drive 2 mm further back on the shelf. The rail slots allow this. Use thin double-sided tape or a few dots of CA on the tray strip, keeping glue off the edges so the tray still slides freely.

## Two-colour labels (AMS)

Each labelled base and its inlay STL share the same coordinates, so they line up automatically:

1. Select both files, `base_front_left_EN.stl` and `labels_EN_inlay.stl` (or the JP pair), and drag them into Bambu Studio together.
2. When it asks *"Load these files as a single object with multiple parts?"*, answer **Yes**.
3. In the object list, give the label part its own filament (white suits the JX). Print as normal.

The labels sit on the front wall, which prints vertically, so the colour changes are spread over a few layers. That only adds a little time.

**The smallest strokes are about 0.6 mm wide.** A 0.4 mm nozzle handles them, but print this piece with a fine layer height (0.12–0.16 mm) for crisp lettering. The blank version suits stickers or rub-on transfers.

## Power switch

The switch uses the red lever from Axeman's [Big Red Switch (IBM XT style) with magnetic latching](https://www.printables.com/model/459567-big-red-switch-ibm-xt-style-with-magnetic-latching). It is included unmodified as `third_party/BRS_Lever.stl` under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The frame that holds it in this case is new, and so is the momentary START action. Full attribution and licence details are in [Credits and licences](#credits-and-licences).

The red drum sits in the JX switch channel and the blade sticks out of it.

| Position | Blade | What it does |
|---|---|---|
| 切 | Down | A magnet holds it here, and a stop in the frame stops it going further. Nothing is pressed. |
| 入 | Up | A magnet holds it here. Nothing is pressed. This is the resting position while you use the PC. |
| START | Pushed further up (about 8°) | The drum's rear edge presses the microswitch. When you let go, the 入 magnet pulls it back, helped by the microswitch's spring. The blade meets the top of the window at the end of the travel. |

A modern PC only needs a momentary press on its power button, so START is the only electrical position.

- **Power on:** flip up to 入, then nudge up to START.
- **Shut down:** nudge up to START again, then flip down to 切.
- **Force off:** hold START for 4 seconds.

**Parts:**

- **Lever:** Axeman's lever, printed in red.
- **Magnets:** three 8 × 3 mm disc magnets. One goes in the lever's pocket, as in Axeman's design. Two go in the frame's right cheek, facing the lever. These two stick out about 2 mm and sit in matching recesses in the back of the front wall.
- **Axle:** one M4×35 screw and a nyloc nut.
- **Microswitch:** one lever microswitch, 19.8 × 10.2 × 6.4 mm (Omron SS-5GL or a generic "KW11-3Z" with a hinge lever).
- **Screws:** two M2×25 screws and nuts for the microswitch, and four M3×10 screws to mount the frame.
- **Inserts:** four M3 heat-set inserts for the wall bosses.

**Assembly (on the bench first):**

1. **Fit the lever magnet** flush in its pocket.
2. **Fit the two cheek magnets.** Before gluing, check each one *attracts* the lever magnet; mark the faces so you get the polarity right.
3. **Fit the lever** in the frame on the M4 axle. Tighten the nyloc nut until there's no play but the lever still swings freely.
4. **Fit the microswitch** between the cheeks:
   - Lay it on its side with the plunger facing forward and the hinge lever hanging down in front of it.
   - The drum's rear top edge should push the lever back at START but not at 入. The screw slots give 6 mm of front-to-back adjustment, and you can bend the lever to fine-tune.
5. **Mount the frame** on the wall bosses. The drum and blade go through the window from behind.
6. **Wire it up:** connect the switch's COM and NO terminals to the motherboard's PWR_SW header pins. Polarity doesn't matter.

**To regenerate the case:** `jx_case.scad` reads `third_party/BRS_Lever.stl` to size the window and to check the clearances.

## Hardware

- **Motherboard:** 9 × M3 10 mm female-female brass standoffs. Use 9 × M3×8 screws from under the floor and 9 × M3×6 screws through the board.
- **Heat-set inserts:** 40 × M3 (short type, 4.0 mm hole). That covers 14 lid bosses, 6 feet, 2 for the I/O panel lip, 8 for the bay cages, 6 for the DVD shelf ledges and 4 for the power switch.
- **Seam bolts:** 10 × M3×20 with nuts (front and side wall seams).
- **Lid bolts:** 8 × M3×10 with nuts (lid seam ribs) and 14 × M3×8 countersunk (lid to walls).
- **Rear panels:** 9 × M3×12 with nuts (6 at the columns, 3 for the rail) and 2 × M3×8 (I/O panel lip to floor).
- **Bays:**
  - 8 × M3×8 to screw the cages down.
  - 6 × M3×10 countersunk for the DVD shelf.
  - 4 × M3×5 for the optical drive.
  - Your 3.5" devices' own side screws.
- **Feet:** 6 × M3×10.
- **Fans:** 2 × 92 mm intake fans on the left side, aimed at the GPU, and 1 × 80 mm exhaust on the rear. All are optional.

## Assembly order

1. **Join the base quadrants.** Push in heat-set inserts first. Glue the butterfly keys into the floor seams, then bolt the wall seam tabs. Do front-left to front-right and rear-left to rear-right, then join the front and rear halves.
2. **Fit the standoffs** from underneath, then the feet.
3. **Fit the PSU** from inside, with 4 screws through the rear wall. The rear holes suit fan-up or fan-down mounting; there are vents in the lid and floor for either.
4. **Fit the 3.5" devices.** Mount each device in its cage on the bench, with the faceplate flush with the cage front. Then screw each cage to the floor and clip a cover into any empty bay.
5. **Fit the optical drive.** Screw it loosely to the shelf rails, drop the shelf onto its ledges and screw it down. Slide the drive forward until its bezel sits flush in the JX drive face, then tighten. The rail slots give ±8 mm of adjustment.
6. **Fit the rear panels.** Bolt them to the columns either side and to the floor lip, then add the bracket rail.
7. **Fit the board.** Install a card, set the rail height so the bracket flange sits flat, and tighten.
8. **Fit the lid.** Bolt the 4 tiles together at the ribs, then screw it down.

## Clearances

- **CPU cooler:** up to about 165 mm (the lid seam rib bottom is 169 mm above the board). Any part of the cooler that reaches under the DVD shelf, at the front-right of the board, is limited to about 115 mm.
- **GPU:** up to about 165 mm above the board, and up to about 300 mm long.
- **Optical drive:** any standard 5.25" drive up to about 185 mm deep.
- **3.5" bays:**
  - Drive B suits USB panels up to about 100 mm deep. Its cage overhangs the front edge of the board.
  - Drive A suits a full-size floppy or card reader up to about 150 mm deep.
- **PSU:** standard ATX up to 150 mm deep if you fit a full-depth floppy in drive A; otherwise up to 160 mm.
- **Side fans:** the 25 mm side fans take up the space of the bottom (7th) slot. Use 15 mm slim fans if you need that slot.

## Credits and licences

- **Big Red Switch lever** (`third_party/BRS_Lever.stl`): "[Big Red Switch (IBM XT Style) with magnetic latching](https://www.printables.com/model/459567-big-red-switch-ibm-xt-style-with-magnetic-latching)" by Axeman.
  - Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) and included **unmodified**.
  - The magnetic latching concept also comes from this design.
  - Non-commercial use only. Adaptations must be shared under the same licence.
- **Power switch frame** (`power_switch_frame`, generated by `jx_case.scad`): designed for this project to hold Axeman's lever. Because it is built around that design, it is also released under CC BY-NC-SA 4.0.
- **Everything else in this repository** (the case design, `jx_case.scad` and the scripts, the STLs and the renders): © Glenn Ji Mason, licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The full licence text is in [`LICENSE`](LICENSE).
- **IBM** and the **IBM JX** are trademarks of IBM. This is an unofficial fan project, not affiliated with or endorsed by IBM. No IBM logo artwork is included.
