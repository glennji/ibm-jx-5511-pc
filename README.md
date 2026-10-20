# JX-style ATX desktop case (3D printable)

A dark-grey desktop box modelled on the front of an IBM JX (5511) system unit with its expansion unit stacked on top. The front is traced from a photo and scaled uniformly, so it keeps the JX's proportions. It takes a full ATX board, a standard ATX PSU, a 5.25" optical drive and two 3.5" bay devices. Every part fits a 256 × 256 mm bed (largest part 247.5 mm).

**Outside size:** 495 W × 324 D × 199 H mm, the same width-to-height ratio as the photo (about 2.49 : 1).

## Before you print anything big: run the fit check

Print `fit_template_left` and `fit_template_right` first. They are 1.2 mm thick and take about 30 minutes each. Tape them together and lay them on your MSI board.

- **All 9 holes should line up with the board's mounting holes.**
- **The V-notches on the rear edge** mark the left and right edges of the I/O shield and the centre of each expansion bracket. They should line up with your board's I/O shield and slots.

The hole pattern is ATX standard, so it should match. The I/O shield and slot positions are best estimates, so check them. If they are off, measure from the board's slot-side edge, then edit these values near the top of `jx_case.py` and rerun:

| Parameter | Meaning | Current |
|---|---|---|
| `IO_U0` | Slot-side board edge to left edge of the I/O shield opening | 146.0 mm |
| `SLOT7_U` | Slot-side board edge to centre of the bracket nearest the I/O | 131.8 mm |
| `RAIL_LEDGE_Z` | Height where card bracket flanges rest (also adjustable ±6 mm on the rail) | board top + 108 mm |
| `GROOVE_D` | Depth of the line between the two "units" | 4 mm |

To regenerate: `pip install manifold3d numpy`, then `python3 jx_case.py`. To change the front, edit the photo-pixel boxes passed to `P()` in `front_relief()`.

## Front panel layout

**Upper unit**

- **5.25" bay:** a working bay for any standard 5.25" optical drive, such as a DVD-RW. The drive's own bezel shows in the middle of the JX drive face, between the two end blocks.
- **Cosmetic details:** the badge recess and the blank cover panel.

**Lower unit**

- **Drive B (left):** a working 3.5" bay intended for a USB front panel.
- **Drive A (right):** a working 3.5" bay for a floppy drive or card reader.
- **Clip-in covers:** each bay has a JX-style cover that snaps in. The covers are interchangeable, so you can leave either bay empty.
- **LED holes:** two 3 mm holes sit below the drive bays, for the HDD LED and a spare.
- **Power switch:** a red paddle (in the spirit of the XT's big red switch) that tilts in the JX switch channel, with raised 入 and 切 labels. Magnets hold it at 切 (down) and 入 (up). Pushing it further up is a spring-back START that presses the PC's power button. See *Power paddle* below.
- **Power LED window:** the square IR window takes a piece of smoked acrylic with the power LED behind it.
- **Cartridge strip:** two cartridge doors and the mode-switch slot. These are cosmetic.

## Parts to print (`stl/`)

All parts are already oriented for printing, and none need supports except where noted below.

| File | Qty | Notes |
|---|---|---|
| base_front_left / front_right / rear_left / rear_right | 1 each | Floor plus walls, printed floor-down. The front ones carry the JX face. |
| lid_front_left / front_right / rear_left / rear_right | 1 each | Printed top face down. |
| rear_slot_panel | 1 | Expansion slot panel. |
| rear_io_panel | 1 | I/O shield opening (with a 1.2 mm rim so the shield clips in) and an 80 mm exhaust fan mount. |
| bracket_rail | 1 | Card bracket screw ledge. Also ties the two rear panels together. |
| bay_cage_35_x2 | 2 | 3.5" bay cages, screwed to the floor behind drives A and B. They're removable, so you can fit a device on the bench. |
| bay_blank_clip_x2 | 2 | Clip-in bay covers with the JX drive face. Squeeze the two hooks from inside to remove one. |
| dvd_shelf | 1 | Shelf and side rails for the optical drive. Rests on ledges on the front and right walls. |
| dvd_fascia_frame | 1 | JX drive face for the optical drive: glue it onto the drive's fixed bezel. |
| dvd_fascia_tray | 1 | Matching strip: glue it onto the tray front so the slot line continues when the tray is closed. |
| power_paddle_frame | 1 | Mechanism frame with the axle, two latch magnets and the microswitch. Screws to 4 bosses behind the front wall. |
| power_paddle_lever | 1 | Lever (hub, arm and magnet tail). Prints lying on its flat side. |
| power_paddle_head_RED | 1 | Red paddle head, 20.6 × 15 mm, filling most of the switch channel like the original. Print in red and glue it onto the end of the arm once the lever is through the slot. |
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

**Tray and button positions differ between drive models, so measure yours first.** Measure from the top-left corner of the bezel, then edit these values near `dvd_fascia()` in `jx_case.py` and rerun:

| Parameter | Meaning | Default |
|---|---|---|
| `DVD_TRAY` | Tray front: left, top, right, bottom (mm from the top-left corner) | 10, 8, 138, 22.5 |
| `DVD_EJECT` | Eject button opening | 124, 31, 140, 37 |
| `DVD_ACT_LED` | Drive activity LED hole (`None` to skip) | 115, 34 |

Both plates are 2 mm thick, so mount the drive 2 mm further back on the shelf. The rail slots allow this. Use thin double-sided tape or a few dots of CA on the tray strip, keeping glue off the edges so the tray still slides freely.

## Power paddle

The magnetic latching idea comes from Axeman's [Big Red Switch (IBM XT style) with magnetic latching](https://www.printables.com/model/459567-big-red-switch-ibm-xt-style-with-magnetic-latching) (CC BY-NC-SA 4.0). The parts here are a new design.

Tip: paint the inside of the switch channel matte black, as on the original, so the slot behind the paddle disappears.

| Position | Paddle | What it does |
|---|---|---|
| 切 | Tilted down | A magnet holds it here. Nothing is pressed. |
| 入 | Tilted up | A magnet holds it here. Nothing is pressed. This is the resting position while you use the PC. |
| START | Pushed further up | Presses the power button. The 入 magnet pulls it back when you let go, helped by the microswitch's own spring. |

The ends of the slot in the front wall are the hard stops, so the paddle can't be pushed past START.

A modern PC only needs a momentary press on its power button, so START is the only electrical position.

- **Power on:** flip up to 入, then nudge up to START.
- **Shut down:** nudge up to START again, then flip down to 切.
- **Force off:** hold START for 4 seconds.

**Parts:**

- **Magnets:** three 8 × 3 mm disc magnets. One goes in the tail of the lever, and two go in the frame's right cheek, pushed in from outside.
- **Microswitch:** one lever microswitch, 19.8 × 10.2 × 6.4 mm (Omron SS-5GL or a generic "KW11-3Z" with a hinge lever).
- **Screws:** one M3×16 screw and nyloc nut as the axle, two M2×20 screws and nuts for the microswitch, and four M3×10 screws to mount the frame.
- **Inserts:** four M3 heat-set inserts for the wall bosses.

**Assembly (on the bench first):**

1. **Glue in the tail magnet**, flush with the lever's flat outer side.
2. **Glue in the two cheek magnets.** Before gluing, check each one *attracts* the tail magnet; mark the faces so you get the polarity right.
3. **Fit the lever** between the cheeks on the M3 axle. Tighten the nyloc nut just enough to remove play, so the lever still swings freely.
4. **Fit the microswitch** between the cheeks, plunger up, with its lever tip toward the rear and under the lever's tail. Its screw slots allow about 8 mm of height adjustment. Set it so it clicks at START but not at 入. If needed, gently bend the switch lever to fine-tune.
5. **Mount the frame** on the wall bosses with the arm through the slot, then glue the red head onto the arm.
6. **Wire it up:** connect the switch's COM and NO terminals to the motherboard's PWR_SW header pins. Polarity doesn't matter.

**If the latch feels wrong:**

- **Too strong or too weak:** change the gap. The skin between the cheek magnets and the lever is 0.6 mm. `paddle_frame()` controls it.
- **START doesn't spring back reliably:** reduce the START angle (`PSW_START` and `PSW_STOPS`) so the paddle stays closer to the 入 magnet.

## Hardware

- **Motherboard:** 9 × M3 10 mm female-female brass standoffs. Use 9 × M3×8 screws from under the floor and 9 × M3×6 screws through the board.
- **Heat-set inserts:** 40 × M3 (short type, 4.0 mm hole). That covers 14 lid bosses, 6 feet, 2 for the I/O panel lip, 8 for the bay cages, 6 for the DVD shelf ledges and 4 for the power paddle.
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
