"""Check and correct a Specctra DSN exported by KiCad before giving it to Freerouting.

KiCad 10's export marks every copper layer `(type signal)`, including layers that
hold plane zones, so the autorouter runs tracks through the planes and cuts them
into islands. This marks the named layers `(type power)`.

It also prints the track width, clearance and via padstack of the board rule and of
every net class, because a DSN exported from the same Python process that created
the board carries KiCad's built-in defaults (0.2 mm, 0.6/0.3 mm via) instead of the
project's net classes. Read the printout before routing. `--expect-track` turns that
reading into a hard failure; `--class-width` overrides one class when you must.

`--shuffle-nets SEED` reorders the net list. Freerouting 2.5.0 is deterministic: the
same DSN gives the same session file, so repeating a run needs some such change to be
a different attempt.

Usage:
  python patch_dsn.py board.dsn --power-layer In1.Cu --power-layer In2.Cu \
      [--expect-track 0.127] [--class-width Power=0.4] [--shuffle-nets 3] [-o patched.dsn]

Plain Python 3.9+. Tested on DSN files from KiCad 10.0.8 (resolution um).
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

CLASS_RE = re.compile(r'\(class\s+("[^"]*"|\S+)(.*?)\n    \)', re.DOTALL)
NET_BLOCK_RE = re.compile(r"^    \(net .*?^    \)\n", re.DOTALL | re.MULTILINE)


def um(mm: float) -> str:
    return f"{mm * 1000:g}"


def report(text: str) -> dict[str, float]:
    """Print the rules found; return {class name: track width in mm}."""
    if "(resolution um" not in text:
        raise SystemExit("DSN is not in um resolution; this script assumes KiCad's export")
    widths = {}
    board_rule = re.search(r"\(structure.*?\(rule\s*\(width ([\d.]+)\)\s*\(clearance ([\d.]+)\)", text, re.DOTALL)
    if board_rule:
        widths["(board)"] = float(board_rule.group(1)) / 1000
        print(f"board rule: track {widths['(board)']:g} mm, clearance {float(board_rule.group(2)) / 1000:g} mm")
    for m in CLASS_RE.finditer(text):
        name, body = m.group(1).strip('"'), m.group(2)
        width = re.search(r"\(width ([\d.]+)\)", body)
        gap = re.search(r"\(clearance ([\d.]+)\)", body)
        via = re.search(r'\(use_via ([^)]*)\)', body)
        if width:
            widths[name] = float(width.group(1)) / 1000
        print(f"class {name}: track {widths.get(name, 0):g} mm, clearance {float(gap.group(1)) / 1000 if gap else 0:g} mm, "
              f"via {via.group(1) if via else '?'}")
    layers = re.findall(r"\(layer (\S+)\s+\(type (\w+)\)", text)
    print("layers: " + ", ".join(f"{n} {t}" for n, t in layers))
    print(f"wires: {text.count('(type fix)')} fixed (locked in KiCad), {text.count('(type route)')} free")
    return widths


def shuffle_nets(text: str, seed: int) -> str:
    """Reorder the net definitions in the network section.

    Freerouting gives the same result every time for the same file. Changing the order
    in which nets are listed changes the order it works in, which is a cheap way to
    get a genuinely different attempt from the same board.
    """
    start = text.find("\n  (network\n")
    if start < 0:
        raise SystemExit("no network section found")
    end = text.find("\n    (class ", start)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    blocks = NET_BLOCK_RE.findall(section)
    if len(blocks) < 2:
        raise SystemExit("could not split the network section into nets")
    first = section.find(blocks[0])
    last = section.rfind(blocks[-1]) + len(blocks[-1])
    if "".join(blocks) != section[first:last]:
        raise SystemExit("network section has content between nets; not shuffling")
    random.Random(seed).shuffle(blocks)
    return text[:start] + section[:first] + "".join(blocks) + section[last:] + text[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dsn", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="default: rewrite the input file")
    ap.add_argument("--power-layer", action="append", default=[], help="layer holding a plane, e.g. In1.Cu; repeatable")
    ap.add_argument("--expect-track", type=float, help="fail unless the default class has this track width (mm)")
    ap.add_argument("--class-width", action="append", default=[], metavar="CLASS=MM", help="set one class's track width")
    ap.add_argument("--shuffle-nets", type=int, metavar="SEED", help="reorder the net list, seeded, to vary the route")
    args = ap.parse_args()

    text = args.dsn.read_text()
    widths = report(text)
    default = widths.get("kicad_default", widths.get("(board)"))
    if args.expect_track is not None and (default is None or abs(default - args.expect_track) > 1e-6):
        print(f"default track is {default} mm, expected {args.expect_track}: the export did not see the project's "
              "net classes. Export the DSN from a fresh process, after the .kicad_pro is on disk.", file=sys.stderr)
        return 1

    for layer in args.power_layer:
        text, n = re.subn(rf"\(layer {re.escape(layer)}(\s+)\(type signal\)", rf"(layer {layer}\1(type power)", text)
        if n != 1:
            print(f"layer {layer} not found as a signal layer", file=sys.stderr)
            return 1
    for spec in args.class_width:
        name, _, value = spec.partition("=")

        def set_width(m: re.Match, name: str = name, value: str = value) -> str:
            if m.group(1).strip('"') != name:
                return m.group(0)
            return re.sub(r"\(width [\d.]+\)", f"(width {um(float(value))})", m.group(0))

        text, _ = CLASS_RE.subn(set_width, text)
    if args.shuffle_nets is not None:
        text = shuffle_nets(text, args.shuffle_nets)
        print(f"net order shuffled with seed {args.shuffle_nets}")
    (args.output or args.dsn).write_text(text)
    if args.power_layer or args.class_width:
        print("after patching:")
        report(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
