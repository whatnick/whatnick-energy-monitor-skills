from __future__ import annotations

import argparse
from pathlib import Path


def find_block_end(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1

    raise ValueError("unterminated S-expression block")


def remove_blocks(text: str, block_starts: tuple[str, ...]) -> tuple[str, int]:
    output: list[str] = []
    cursor = 0
    removed = 0

    while cursor < len(text):
        starts = [(text.find(start, cursor), start) for start in block_starts]
        starts = [(index, start) for index, start in starts if index != -1]
        if not starts:
            output.append(text[cursor:])
            break

        index, start = min(starts, key=lambda item: item[0])
        output.append(text[cursor:index])
        cursor = find_block_end(text, index)
        removed += 1

    return "".join(output), removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove KiCad PCB segment and via blocks before a fresh autoroute.")
    parser.add_argument("board", type=Path, help="Path to a .kicad_pcb file")
    args = parser.parse_args()

    text = args.board.read_text(encoding="utf-8")
    text, removed = remove_blocks(text, ("(segment", "(via"))
    args.board.write_text(text, encoding="utf-8", newline="")
    print(f"Removed {removed} route block(s)")


if __name__ == "__main__":
    main()
