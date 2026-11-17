"""Measure the things DRC passes but a reviewer would not, on a routed KiCad board.

Read-only: the board is loaded and never saved. Run with KiCad's own Python
(pcbnew); written for the Python 3.9 that KiCad 10 bundles, no third-party modules.

Checks:
  vias in pads   a via drill inside an SMD pad wicks solder away from the joint;
                 large pads (exposed thermal pads) are listed separately
  near NPTH      outer-layer copper close to an unplated hole (screw heads and
                 standoffs reach well past the drill)
  thin power     nets matching --power routed narrower than --power-width
  plane pieces   filled zones that ended up in more than one piece on a layer
  net report     length, width range, via count and layers for nets matching --net

Usage:
  KICAD_PYTHON audit_board.py BOARD.kicad_pcb [--power '^(VBUS|\\+5V|\\+1V1)$']
      [--power-width 0.3] [--npth-clearance 1.5] [--net 'USB|XTAL|OSC']

Exit status is 1 if any via sits in a small SMD pad, any power net is thin, or any
copper is inside the NPTH clearance.
"""
from __future__ import annotations

import argparse
import math
import re
import sys

import pcbnew

MM = pcbnew.ToMM


def seg_point_distance(ax, ay, bx, by, px, py):
    """Distance from point p to segment ab."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    ap.add_argument("--power", default=r"^(VBUS|\+\d+V\d*|\+\d+\.\d+V|VCC|VDD)$",
                    help="regex (searched in the net name's last path element) for nets that carry supply current")
    ap.add_argument("--power-width", type=float, default=0.3, help="mm; narrower tracks on power nets are reported")
    ap.add_argument("--plane-net", action="append", default=[],
                    help="net distributed on a plane; its short pad-to-via stubs are not reported. Repeatable")
    ap.add_argument("--npth-clearance", type=float, default=1.5, help="mm from the hole edge kept free of outer copper")
    ap.add_argument("--large-pad", type=float, default=1.5, help="mm; SMD pads at least this small side are 'exposed pads'")
    ap.add_argument("--net", help="regex of nets to report length, width and vias for")
    args = ap.parse_args()

    board = pcbnew.LoadBoard(args.board)
    # Take the collections once and keep them: the swig wrappers can stop iterating
    # after earlier wrapper objects have been garbage collected.
    footprints = list(board.GetFootprints())
    items = list(board.GetTracks())
    zones = list(board.Zones())
    vias = [t for t in items if t.GetClass() == "PCB_VIA"]
    tracks = [t for t in items if t.GetClass() != "PCB_VIA"]
    pads = [(fp.GetReference(), pad) for fp in footprints for pad in fp.Pads()]
    bbox = board.GetBoardEdgesBoundingBox()
    ox, oy = MM(bbox.GetLeft()), MM(bbox.GetTop())
    print(f"board {MM(bbox.GetWidth()):.2f} x {MM(bbox.GetHeight()):.2f} mm; coordinates below are from its top-left corner")
    print(f"{len(footprints)} footprints, {len(tracks)} track segments, {len(vias)} vias, {len(zones)} zones")
    failed = False

    # ---- vias in SMD pads
    small, large = [], []
    for ref, pad in pads:
        if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        bb = pad.GetBoundingBox()
        left, top, right, bottom = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())
        for via in vias:
            x, y, r = MM(via.GetPosition().x), MM(via.GetPosition().y), MM(via.GetDrillValue()) / 2
            if left - r < x < right + r and top - r < y < bottom + r and pad.IsOnLayer(via.TopLayer()):
                entry = f"  {ref}.{pad.GetNumber()} [{pad.GetNetname()}] via at ({x - ox:.2f}, {y - oy:.2f})"
                (large if min(right - left, bottom - top) >= args.large_pad else small).append(entry)
    print(f"\nvias with the drill in a small SMD pad: {len(small)}")
    print("\n".join(small))
    print(f"vias in large SMD pads (exposed pads, test points; usually deliberate): {len(large)}")
    failed |= bool(small)

    # ---- outer copper near unplated holes
    holes = [(ref, MM(pad.GetPosition().x), MM(pad.GetPosition().y), MM(pad.GetDrillSize().x) / 2)
             for ref, pad in pads if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    near = []
    for ref, hx, hy, hr in holes:
        worst = None
        for t in tracks:
            if t.GetLayer() not in (pcbnew.F_Cu, pcbnew.B_Cu):
                continue
            d = seg_point_distance(MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y), hx, hy)
            d -= hr + MM(t.GetWidth()) / 2
            if d < args.npth_clearance and (worst is None or d < worst[0]):
                worst = (d, t.GetNetname(), board.GetLayerName(t.GetLayer()))
        for via in vias:
            d = math.hypot(MM(via.GetPosition().x) - hx, MM(via.GetPosition().y) - hy) - hr - MM(via.GetWidth(pcbnew.F_Cu)) / 2
            if d < args.npth_clearance and (worst is None or d < worst[0]):
                worst = (d, via.GetNetname(), "via")
        if worst:
            near.append(f"  {ref} at ({hx - ox:.1f}, {hy - oy:.1f}), drill {2 * hr:.2f}: {worst[1]} on {worst[2]} "
                        f"{worst[0]:.2f} mm from the hole edge")
    print(f"\nunplated holes with outer-layer copper within {args.npth_clearance} mm of the edge: {len(near)} of {len(holes)}")
    print("\n".join(near))
    failed |= bool(near)

    # ---- per-net figures
    nets: dict[str, dict] = {}
    for t in tracks:
        n = nets.setdefault(t.GetNetname(), {"len": 0.0, "widths": {}, "vias": 0, "layers": set()})
        length = MM(t.GetLength())
        n["len"] += length
        n["widths"][MM(t.GetWidth())] = n["widths"].get(MM(t.GetWidth()), 0.0) + length
        n["layers"].add(board.GetLayerName(t.GetLayer()))
    for via in vias:
        nets.setdefault(via.GetNetname(), {"len": 0.0, "widths": {}, "vias": 0, "layers": set()})["vias"] += 1

    power = re.compile(args.power)
    thin = []
    for name, n in sorted(nets.items()):
        if name in args.plane_net or not power.search(name.rsplit("/", 1)[-1]):
            continue
        narrow = sum(length for width, length in n["widths"].items() if width < args.power_width - 1e-6)
        if narrow > 0:
            thin.append(f"  {name}: {narrow:.1f} of {n['len']:.1f} mm narrower than {args.power_width} mm "
                        f"(narrowest {min(n['widths']):.3f}), {n['vias']} vias")
    print(f"\npower nets with track narrower than {args.power_width} mm: {len(thin)}")
    print("\n".join(thin))
    failed |= bool(thin)

    # ---- plane pieces
    print("\nfilled zones in more than one piece:")
    for zone in zones:
        if zone.GetIsRuleArea():
            continue
        for layer in zone.GetLayerSet().Seq():
            count = zone.GetFilledPolysList(layer).OutlineCount()
            if count != 1:
                print(f"  {zone.GetNetname()} on {board.GetLayerName(layer)}: {count} pieces")

    if args.net:
        pat = re.compile(args.net)
        print(f"\nnets matching {args.net!r}:")
        for name, n in sorted(nets.items()):
            if pat.search(name):
                print(f"  {name}: {n['len']:.1f} mm, width {min(n['widths'], default=0):.3f}-{max(n['widths'], default=0):.3f}, "
                      f"{n['vias']} vias, {'/'.join(sorted(n['layers']))}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
