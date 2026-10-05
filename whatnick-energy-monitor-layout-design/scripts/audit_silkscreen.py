from __future__ import annotations

import argparse
import re
from pathlib import Path

import pcbnew


def close(actual: float, expected: float, tolerance: float = 0.01) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit production silkscreen geometry and marker coverage."
    )
    parser.add_argument("board", type=Path)
    parser.add_argument("--height", type=float, default=0.8)
    parser.add_argument("--width", type=float, default=0.8)
    parser.add_argument("--stroke", type=float, default=0.2)
    parser.add_argument(
        "--drill-ref-regex",
        default=r"^(H|MH|FID)",
        help="References treated as mounting/tooling/fiducial features.",
    )
    parser.add_argument(
        "--require-logo",
        action="append",
        default=[],
        help="Case-insensitive token required in a logo footprint reference or value.",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    drill_pattern = re.compile(args.drill_ref_regex, re.IGNORECASE)
    failures: list[str] = []

    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        field = footprint.Reference()
        is_drill_feature = bool(drill_pattern.search(reference)) or any(
            token in footprint.GetValue().lower()
            for token in ("mountinghole", "toolinghole", "fiducial")
        )

        if is_drill_feature:
            if field.IsVisible() or footprint.Value().IsVisible():
                failures.append(f"{reference}: drill-only marker must remain hidden")
            continue

        if reference.upper().startswith("LOGO"):
            continue
        if not field.IsVisible():
            failures.append(f"{reference}: fitted reference is hidden")
            continue

        size = field.GetTextSize()
        height = size.y / 1_000_000
        width = size.x / 1_000_000
        stroke = field.GetTextThickness() / 1_000_000
        if not (
            close(height, args.height)
            and close(width, args.width)
            and close(stroke, args.stroke)
        ):
            failures.append(
                f"{reference}: {width:.2f}x{height:.2f}/{stroke:.2f} mm, "
                f"expected {args.width:.2f}x{args.height:.2f}/{args.stroke:.2f} mm"
            )

        expected_layer = (
            pcbnew.F_SilkS
            if footprint.GetLayer() == pcbnew.F_Cu
            else pcbnew.B_SilkS
        )
        if field.GetLayer() != expected_layer:
            failures.append(f"{reference}: reference is not on component-side silkscreen")

    searchable_logos = [
        f"{footprint.GetReference()} {footprint.GetValue()}".lower()
        for footprint in board.GetFootprints()
        if footprint.GetReference().upper().startswith("LOGO")
    ]
    for token in args.require_logo:
        if not any(token.lower() in logo for logo in searchable_logos):
            failures.append(f"missing required logo token: {token}")

    for failure in failures:
        print(f"FAIL {failure}")
    if failures:
        return 1

    print("Silkscreen audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
