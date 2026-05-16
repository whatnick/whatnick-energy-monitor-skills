from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


def main() -> None:
    parser = argparse.ArgumentParser(description="Move footprint reference fields to matching silkscreen layers and values to Fab layers.")
    parser.add_argument("board", type=Path, help="Path to a .kicad_pcb file")
    parser.add_argument("--hide-mounting-holes", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    moved = 0
    hidden = 0
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        reference_field = footprint.Reference()
        value_field = footprint.Value()
        front = footprint.GetLayer() == pcbnew.F_Cu
        if args.hide_mounting_holes and ref.startswith("H") and "MountingHole" in footprint.GetValue():
            reference_field.SetVisible(False)
            value_field.SetVisible(False)
            hidden += 1
            continue
        reference_field.SetLayer(pcbnew.F_SilkS if front else pcbnew.B_SilkS)
        reference_field.SetVisible(True)
        value_field.SetLayer(pcbnew.F_Fab if front else pcbnew.B_Fab)
        moved += 1
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Moved {moved} reference field(s); hid {hidden} mounting-hole reference/value pair(s).")


if __name__ == "__main__":
    main()
