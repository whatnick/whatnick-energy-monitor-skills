from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


def vmm(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def item_net_name(item: pcbnew.BOARD_ITEM) -> str:
    if hasattr(item, "GetNetname"):
        return item.GetNetname()
    if hasattr(item, "GetNet") and item.GetNet() is not None:
        return item.GetNet().GetNetname()
    return ""


def edge_cuts_bbox(board: pcbnew.BOARD) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for drawing in board.GetDrawings():
        if not hasattr(drawing, "GetLayer") or drawing.GetLayer() != pcbnew.Edge_Cuts:
            continue
        for point in (drawing.GetStart(), drawing.GetEnd()):
            xs.append(pcbnew.ToMM(point.x))
            ys.append(pcbnew.ToMM(point.y))
        if hasattr(drawing, "GetCenter"):
            center = drawing.GetCenter()
            xs.append(pcbnew.ToMM(center.x))
            ys.append(pcbnew.ToMM(center.y))
    if not xs or not ys:
        raise RuntimeError("board has no Edge.Cuts outline")
    return min(xs), min(ys), max(xs), max(ys)


def widen_power_copper(
    board: pcbnew.BOARD,
    power_nets: set[str],
    track_width_mm: float,
    via_diameter_mm: float,
    via_drill_mm: float,
) -> tuple[int, int]:
    widened_tracks = 0
    widened_vias = 0
    track_width = pcbnew.FromMM(track_width_mm)
    via_diameter = pcbnew.FromMM(via_diameter_mm)
    via_drill = pcbnew.FromMM(via_drill_mm)

    for track in board.GetTracks():
        if item_net_name(track) not in power_nets:
            continue
        if type(track).__name__ == "PCB_VIA":
            if track.GetFrontWidth() < via_diameter:
                track.SetWidth(via_diameter)
            if hasattr(track, "SetDrill") and track.GetDrillValue() < via_drill:
                track.SetDrill(via_drill)
            widened_vias += 1
        elif hasattr(track, "SetWidth"):
            if track.GetWidth() < track_width:
                track.SetWidth(track_width)
            widened_tracks += 1
    return widened_tracks, widened_vias


def remove_existing_zones(board: pcbnew.BOARD, net_name: str) -> int:
    removed = 0
    for zone in list(board.Zones()):
        if zone.GetNetname() == net_name and zone.GetLayer() in {pcbnew.F_Cu, pcbnew.B_Cu}:
            board.Remove(zone)
            removed += 1
    return removed


def add_zone(
    board: pcbnew.BOARD,
    layer: int,
    net_name: str,
    bbox: tuple[float, float, float, float],
    inset_mm: float,
    clearance_mm: float,
    min_thickness_mm: float,
    solid: bool,
) -> None:
    left, top, right, bottom = bbox
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(board.FindNet(net_name))
    zone.SetAssignedPriority(0)
    zone.SetLocalClearance(pcbnew.FromMM(clearance_mm))
    zone.SetMinThickness(pcbnew.FromMM(min_thickness_mm))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(pcbnew.FromMM(0.25))
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.30))
    zone.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
    zone.SetIsFilled(True)
    zone.AppendCorner(vmm(left + inset_mm, top + inset_mm), -1)
    zone.AppendCorner(vmm(right - inset_mm, top + inset_mm), -1)
    zone.AppendCorner(vmm(right - inset_mm, bottom - inset_mm), -1)
    zone.AppendCorner(vmm(left + inset_mm, bottom - inset_mm), -1)
    board.Add(zone)


def main() -> None:
    parser = argparse.ArgumentParser(description="Add F.Cu/B.Cu GND planes and enforce thicker power copper.")
    parser.add_argument("board", type=Path, help="Path to a .kicad_pcb file")
    parser.add_argument("--ground-net", default="GND")
    parser.add_argument("--power-net", action="append", default=[], help="Power net to widen; may be repeated")
    parser.add_argument("--track-width-mm", type=float, default=0.25)
    parser.add_argument("--via-diameter-mm", type=float, default=0.50)
    parser.add_argument("--via-drill-mm", type=float, default=0.25)
    parser.add_argument("--zone-inset-mm", type=float, default=0.60)
    parser.add_argument("--zone-clearance-mm", type=float, default=0.20)
    parser.add_argument("--zone-min-thickness-mm", type=float, default=0.20)
    parser.add_argument("--thermal", action="store_true", help="Use thermal relief instead of solid zone pad connections")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    power_nets = set(args.power_net)
    widened_tracks, widened_vias = widen_power_copper(
        board, power_nets, args.track_width_mm, args.via_diameter_mm, args.via_drill_mm
    ) if power_nets else (0, 0)
    bbox = edge_cuts_bbox(board)
    removed = remove_existing_zones(board, args.ground_net)
    add_zone(board, pcbnew.F_Cu, args.ground_net, bbox, args.zone_inset_mm, args.zone_clearance_mm, args.zone_min_thickness_mm, not args.thermal)
    add_zone(board, pcbnew.B_Cu, args.ground_net, bbox, args.zone_inset_mm, args.zone_clearance_mm, args.zone_min_thickness_mm, not args.thermal)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Widened {widened_tracks} tracks and {widened_vias} vias; replaced {removed} {args.ground_net} zone(s).")


if __name__ == "__main__":
    main()
