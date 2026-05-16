from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


def vmm(x_mm: float, y_mm: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


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


def remove_existing_dimensions(board: pcbnew.BOARD) -> int:
    removed = 0
    for drawing in list(board.GetDrawings()):
        if type(drawing).__name__.startswith("PCB_DIM_"):
            board.Remove(drawing)
            removed += 1
    return removed


def add_dimension(
    board: pcbnew.BOARD,
    start: tuple[float, float],
    end: tuple[float, float],
    height_mm: float,
    text: str,
    text_pos: tuple[float, float],
    text_angle_degrees: float = 0.0,
) -> None:
    dimension = pcbnew.PCB_DIM_ALIGNED(board)
    dimension.SetLayer(pcbnew.Dwgs_User)
    dimension.SetStart(vmm(*start))
    dimension.SetEnd(vmm(*end))
    dimension.SetHeight(pcbnew.FromMM(height_mm))
    dimension.SetUnits(pcbnew.EDA_UNITS_MM)
    dimension.SetUnitsMode(pcbnew.DIM_UNITS_MODE_MM)
    dimension.SetUnitsFormat(pcbnew.DIM_UNITS_FORMAT_BARE_SUFFIX)
    dimension.SetPrecision(pcbnew.DIM_PRECISION_X_XXX)
    dimension.SetText(text)
    dimension.SetTextPos(vmm(*text_pos))
    dimension.SetTextAngleDegrees(text_angle_degrees)
    dimension.SetTextSize(vmm(1.2, 1.2))
    dimension.SetTextThickness(pcbnew.FromMM(0.15))
    dimension.SetLineThickness(pcbnew.FromMM(0.10))
    dimension.SetArrowDirection(pcbnew.DIM_ARROW_DIRECTION_OUTWARD)
    board.Add(dimension)


def main() -> None:
    parser = argparse.ArgumentParser(description="Add board-edge width and height dimensions to Dwgs.User.")
    parser.add_argument("board", type=Path, help="Path to a .kicad_pcb file")
    parser.add_argument("--offset-mm", type=float, default=4.0)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    left, top, right, bottom = edge_cuts_bbox(board)
    width = right - left
    height = bottom - top
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    removed = remove_existing_dimensions(board)
    add_dimension(board, (left, top), (right, top), -args.offset_mm, f"{width:.3f} mm", (center_x, top - args.offset_mm - 1.35))
    add_dimension(board, (right, top), (right, bottom), -args.offset_mm, f"{height:.3f} mm", (right + args.offset_mm + 1.35, center_y), 90.0)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Replaced {removed} dimension item(s) with {width:.3f} mm x {height:.3f} mm measurements.")


if __name__ == "__main__":
    main()
