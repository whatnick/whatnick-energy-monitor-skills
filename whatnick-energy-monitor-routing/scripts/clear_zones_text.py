from __future__ import annotations

import argparse
from pathlib import Path

from clear_routes_text import remove_blocks


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove KiCad PCB zone blocks before rerouting or refilling.")
    parser.add_argument("board", type=Path, help="Path to a .kicad_pcb file")
    args = parser.parse_args()

    text = args.board.read_text(encoding="utf-8")
    text, removed = remove_blocks(text, ("(zone",))
    args.board.write_text(text, encoding="utf-8", newline="")
    print(f"Removed {removed} zone block(s)")


if __name__ == "__main__":
    main()
