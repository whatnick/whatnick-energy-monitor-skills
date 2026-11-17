"""Compare the netlist KiCad extracts from a schematic with the generator's intent.

A generated schematic can pass ERC and still be wrong: a wire that touches a
neighbouring pin merges two nets, and a label that misses its wire end splits one.
The generator knows which net every pin was meant to join, so let KiCad extract the
netlist from the files it wrote and compare the two.

Intent file: JSON object mapping "REF.PIN" to the intended net name, for example
{"U1.3": "SPI_MOSI", "R4.1": "SPI_MOSI", "R4.2": "+3V3"}. Net names need not match
KiCad's names (hierarchical nets get a sheet path prefix); only the grouping is
compared.

Usage:
  python check_netlist_intent.py ROOT.kicad_sch intent.json [--build DIR] [--kicad-cli PATH]
  python check_netlist_intent.py ROOT.kicad_sch --write-intent intent.json

Exit status is 1 when ERC reports errors or the netlist disagrees with the intent.
Needs kicad-cli (KiCad 8 or later); tested with KiCad 10.0.8. Plain Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

NET_RE = re.compile(r'\(net\s*\(code\s*"?\d+"?\)\s*\(name\s*"([^"]*)"\)(.*?)(?=\(net\s*\(code|\Z)', re.DOTALL)
NODE_RE = re.compile(r'\(node\s*\(ref\s*"([^"]+)"\)\s*\(pin\s*"([^"]+)"\)')


def run_erc(cli: str, root_sch: Path, build: Path) -> tuple[int, int, list[str]]:
    """Run ERC with every severity; return (errors, warnings, formatted lines)."""
    out = build / "erc.json"
    subprocess.run(
        [cli, "sch", "erc", "--format", "json", "--severity-all", "--output", str(out), str(root_sch)],
        check=False, capture_output=True,
    )
    report = json.loads(out.read_text())
    errors = warnings = 0
    lines = []
    for sheet in report.get("sheets", []):
        for v in sheet.get("violations", []):
            errors += v["severity"] == "error"
            warnings += v["severity"] == "warning"
            where = "; ".join(i.get("description", "") for i in v.get("items", []))
            lines.append(f"{v['severity']:7s} {v['type']:28s} {sheet.get('path', '')} {where}")
    return errors, warnings, lines


def read_netlist(cli: str, root_sch: Path, build: Path) -> dict[str, str]:
    """Export the netlist and return {"REF.PIN": KiCad net name}."""
    out = build / "netlist.net"
    subprocess.run(
        [cli, "sch", "export", "netlist", "--format", "kicadsexpr", "--output", str(out), str(root_sch)],
        check=True, capture_output=True,
    )
    nodes = {}
    for net in NET_RE.finditer(out.read_text()):
        for node in NODE_RE.finditer(net.group(2)):
            nodes[f"{node.group(1)}.{node.group(2)}"] = net.group(1)
    return nodes


def compare(intent: dict[str, str], actual: dict[str, str]) -> list[str]:
    """Pins meant to share a net must share one, and distinct nets must stay distinct."""
    problems = []
    by_intent: dict[str, set] = {}
    for key, net in intent.items():
        if key not in actual:
            problems.append(f"{key}: intended {net}, missing from KiCad's netlist")
            continue
        by_intent.setdefault(net, set()).add(actual[key])
    for net, names in by_intent.items():
        if len(names) > 1:
            problems.append(f"net {net} is split in KiCad: {sorted(names)}")
    by_actual: dict[str, set] = {}
    for key, name in actual.items():
        if key in intent:
            by_actual.setdefault(name, set()).add(intent[key])
        elif not name.startswith("unconnected-"):
            problems.append(f"{key}: on net {name} in KiCad but not connected by the generator")
    for name, nets in by_actual.items():
        if len(nets) > 1:
            problems.append(f"KiCad net {name} merges intended nets {sorted(nets)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("schematic", type=Path, help="root .kicad_sch")
    ap.add_argument("intent", type=Path, nargs="?", help='JSON {"REF.PIN": "net"}')
    ap.add_argument("--write-intent", type=Path, help="write KiCad's own netlist as an intent file and exit")
    ap.add_argument("--build", type=Path, default=Path("build"), help="directory for erc.json and netlist.net")
    ap.add_argument("--kicad-cli", default="kicad-cli")
    args = ap.parse_args()
    args.build.mkdir(parents=True, exist_ok=True)

    actual = read_netlist(args.kicad_cli, args.schematic, args.build)
    if args.write_intent:
        args.write_intent.write_text(json.dumps(actual, indent=1, sort_keys=True) + "\n")
        print(f"wrote {len(actual)} pins to {args.write_intent}")
        return 0
    if not args.intent:
        ap.error("give an intent file or --write-intent")

    errors, warnings, lines = run_erc(args.kicad_cli, args.schematic, args.build)
    for line in lines:
        print(line)
    problems = compare(json.loads(args.intent.read_text()), actual)
    for problem in problems:
        print(problem)
    print(f"ERC: {errors} errors, {warnings} warnings. Netlist: {len(problems)} problems. "
          f"{len({k.split('.')[0] for k in actual})} components, {len(set(actual.values()))} nets.")
    return 1 if errors or problems else 0


if __name__ == "__main__":
    sys.exit(main())
