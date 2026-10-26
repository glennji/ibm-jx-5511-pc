"""Preview images of the case, rendered by OpenSCAD from the scenes and
cameras in render.scad.

    python3 render.py [scene ...]       (default: front rear open exploded)
    python3 render.py all
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import scadtools as S

# scene -> image size (px)
SIZES = {
    "front": (1400, 900), "flat": (2000, 800), "dvd": (1600, 900), "rear": (1400, 900),
    "open": (1400, 900), "exploded": (1400, 900), "power_on": (1200, 1000), "power_off": (1200, 1000),
    "power_inside": (1200, 1000), "labels_JP": (1000, 1000), "labels_EN": (1000, 1000),
    "labels_BLANK": (1000, 1000),
}
FILENAMES = {"flat": "preview_front_flat.png", "dvd": "preview_dvd_fascia.png"}
GROUPS = {"power": ["power_on", "power_off", "power_inside"], "labels": ["labels_JP", "labels_EN", "labels_BLANK"],
          "all": list(SIZES)}


def render(scene):
    out = FILENAMES.get(scene, f"preview_{scene}.png")
    w, h = SIZES[scene]
    S.openscad("render.scad", out, {"scene": scene},
               ["--render", f"--imgsize={w},{h}", "--projection=p", "--colorscheme=Tomorrow"])
    return out


def main():
    scenes = []
    for a in sys.argv[1:] or ["front", "rear", "open", "exploded"]:
        if a not in SIZES and a not in GROUPS:
            raise SystemExit(f"unknown scene {a}; choose from {', '.join(list(SIZES) + list(GROUPS))}")
        scenes += GROUPS.get(a, [a])
    with ThreadPoolExecutor(os.cpu_count()) as ex:
        for out in ex.map(render, scenes):
            print("wrote", out)


if __name__ == "__main__":
    main()
