"""Write a readable components-and-nets listing from a KiCad netlist.

Reviewers (human or agent) should check connectivity from what KiCad extracted, not
from the drawing. This turns `kicad-cli sch export netlist` output into two plain
sections: one line per component (ref | value | footprint | chosen fields | sheet)
and one line per net with every pin on it as REF.PIN(pin function, pin type).

Usage:
  kicad-cli sch export netlist --format kicadsexpr --output netlist.net ROOT.kicad_sch
  python netlist_to_text.py netlist.net netlist.txt [--field MPN --field LCSC]

Plain Python 3.9+. Tested with netlists from KiCad 10.0.8.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

COMP_RE = re.compile(r'\(comp\s*\(ref "([^"]+)"\)(.*?)(?=\(comp\s*\(ref|\(libparts|\(libraries|\(nets)', re.DOTALL)
NET_RE = re.compile(r'\(net\s*\(code\s*"?\d+"?\)\s*\(name\s*"([^"]*)"\)(.*?)(?=\(net\s*\(code|\Z)', re.DOTALL)
NODE_RE = re.compile(
    r'\(node\s*\(ref\s*"([^"]+)"\)\s*\(pin\s*"([^"]+)"\)'
    r'(?:\s*\(pinfunction\s*"([^"]*)"\))?(?:\s*\(pintype\s*"([^"]*)"\))?'
)


def natural(ref: str) -> tuple:
    m = re.match(r"([A-Za-z#_]+)(\d+)?", ref)
    return (m.group(1), int(m.group(2) or 0), ref) if m else (ref, 0, ref)


def components(text: str, fields: list[str]) -> list[str]:
    rows = []
    for m in COMP_RE.finditer(text):
        ref, body = m.group(1), m.group(2)

        def prop(key: str, body: str = body) -> str:
            hit = re.search(rf'\({key} "([^"]*)"\)', body)
            return hit.group(1) if hit else ""

        def user_field(name: str, body: str = body) -> str:
            hit = re.search(rf'\(field\s*\(name "{re.escape(name)}"\)\s*"([^"]*)"\)', body)
            return hit.group(1) if hit else ""

        sheet = re.search(r'\(sheetpath\s*\(names "([^"]*)"\)', body)
        cols = [ref, prop("value"), prop("footprint"), *[user_field(f) for f in fields], sheet.group(1) if sheet else ""]
        rows.append((natural(ref), " | ".join(cols)))
    return [row for _, row in sorted(rows)]


def nets(text: str) -> list[str]:
    start = text.find("(nets")
    rows = []
    for m in NET_RE.finditer(text[start:] if start >= 0 else text):
        pins = [f"{r}.{p}({fn or ''},{ty or ''})" for r, p, fn, ty in NODE_RE.findall(m.group(2))]
        rows.append(f"{m.group(1)}: " + "  ".join(pins))
    return sorted(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("netlist", type=Path, help="netlist exported with --format kicadsexpr")
    ap.add_argument("output", type=Path)
    ap.add_argument("--field", action="append", default=[], help="symbol field to list per component; repeatable")
    args = ap.parse_args()

    text = args.netlist.read_text()
    comps, net_rows = components(text, args.field), nets(text)
    header = "# ref | value | footprint | " + "".join(f"{f} | " for f in args.field) + "sheet"
    args.output.write_text("\n".join([header, *comps, "", "# net: REF.PIN(pin function,pin type) ...", *net_rows]) + "\n")
    print(f"{len(comps)} components, {len(net_rows)} nets")


if __name__ == "__main__":
    main()
