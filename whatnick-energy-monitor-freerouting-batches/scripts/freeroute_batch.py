"""Route copies of one KiCad board with several Freerouting runs side by side.

On a board at the edge of routability the autorouter's result swings widely with
small changes to its input, and its routing passes use one core, so the useful way
to spend a many-core machine is to make several different attempts at once and keep
the best. Freerouting 2.5.0 is deterministic (the same DSN gives the same session),
so run 1 routes the board as exported and each further run gets the same DSN with
its net list in a different, seeded order. This script never writes to the board it
is given: every run works in its own directory under --out.

For each run: copy the board with its .kicad_pro and .kicad_dru, export a Specctra
DSN (from this process, which has loaded the project from disk), mark plane layers
as power, run Freerouting headless, import the session, refill zones, run KiCad DRC
and count what is left unconnected.

Usage (run with KiCad's own Python, which provides pcbnew):
  KICAD_PYTHON freeroute_batch.py BOARD.kicad_pcb --jar freerouting.jar --runs 4 \
      --power-layer In1.Cu --power-layer In2.Cu [--passes 30] [--timeout 00:20:00] \
      [--expect-track 0.127] [--out build/routes]

Written for KiCad 10.0.8 (bundled Python 3.9) and Freerouting 2.5.0; needs java and
kicad-cli on PATH.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent


def fill(board) -> None:
    """Refill copper zones, leaving rule areas (keep-outs) alone."""
    zones = pcbnew.ZONES()
    for zone in list(board.Zones()):
        if not zone.GetIsRuleArea():
            zones.append(zone)
    pcbnew.ZONE_FILLER(board).Fill(zones)


def drc(board_path: Path, out: Path) -> tuple[int, dict[str, int]]:
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "--output", str(out), str(board_path)],
                   capture_output=True, check=False)
    report = json.loads(out.read_text())
    errors: dict[str, int] = {}
    for v in report.get("violations", []):
        if v["severity"] == "error":
            errors[v["type"]] = errors.get(v["type"], 0) + 1
    return len(report.get("unconnected_items", [])), errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board", type=Path, help="placed board; tracks marked locked are kept as they are")
    ap.add_argument("--jar", type=Path, required=True, help="freerouting.jar")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--passes", type=int, default=30)
    ap.add_argument("--timeout", default="00:20:00", help="Freerouting job time limit, hh:mm:ss")
    ap.add_argument("--power-layer", action="append", default=[], help="layer holding a plane; repeatable")
    ap.add_argument("--expect-track", type=float, help="fail unless the DSN's default track width is this (mm)")
    ap.add_argument("--seed", type=int, default=0, help="base seed for the net-order shuffle of runs 2..N")
    ap.add_argument("--out", type=Path, default=Path("build/routes"))
    args = ap.parse_args()

    src = args.board.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    runs = []
    for i in range(1, args.runs + 1):
        run = (args.out / f"run{i}").resolve()
        shutil.rmtree(run, ignore_errors=True)  # no stale session or DRC file can be read by mistake
        run.mkdir(parents=True)
        for ext in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
            if src.with_suffix(ext).exists():
                shutil.copy(src.with_suffix(ext), run / (src.stem + ext))
        runs.append(run)

    # One export serves every run. Loading the saved board here, in a process that has
    # not built it, is what makes the export see the project's net classes.
    board = pcbnew.LoadBoard(str(runs[0] / src.name))
    dsn = runs[0] / "board.dsn"
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("DSN export failed")
    raw = dsn.read_text()
    for i, run in enumerate(runs):
        (run / "board.dsn").write_text(raw)
        patch = [sys.executable, str(HERE / "patch_dsn.py"), str(run / "board.dsn")]
        for layer in args.power_layer:
            patch += ["--power-layer", layer]
        if args.expect_track is not None:
            patch += ["--expect-track", str(args.expect_track)]
        if i:  # the first run is the board as exported; the others see the nets in another order
            patch += ["--shuffle-nets", str(args.seed + i)]
        done = subprocess.run(patch, check=False, capture_output=bool(i), text=True)
        if done.returncode:
            raise SystemExit(f"DSN check failed for {run.name}; nothing routed\n{done.stderr or ''}")

    start = time.time()
    jobs = []
    for run in runs:
        log = (run / "freerouting.log").open("w")
        # Fanout is off: with it on, Freerouting 2.5.0 spent its whole job time escaping pins.
        jobs.append(subprocess.Popen(
            ["java", "-jar", str(args.jar.resolve()), "-de", str(run / "board.dsn"), "-do", str(run / "board.ses"),
             f"--router.autorouter.max_passes={args.passes}", "--router.fanout.enabled=false",
             f"--router.job_timeout={args.timeout}", "--router.automatic_neckdown=false"],
            stdout=log, stderr=subprocess.STDOUT, cwd=run))
    for job in jobs:
        job.wait()
    print(f"{len(runs)} Freerouting runs finished in {time.time() - start:.0f} s")

    results = []
    for run in runs:
        path = run / src.name
        if not (run / "board.ses").exists():
            print(f"{run.name}: no session file; see {run / 'freerouting.log'}")
            continue
        routed = pcbnew.LoadBoard(str(path))
        if not pcbnew.ImportSpecctraSES(routed, str(run / "board.ses")):
            print(f"{run.name}: session import failed")
            continue
        fill(routed)
        pcbnew.SaveBoard(str(path), routed)
        items = list(routed.GetTracks())
        vias = sum(1 for t in items if t.GetClass() == "PCB_VIA")
        unconnected, errors = drc(path, run / "drc.json")
        results.append((unconnected, sum(errors.values()), run))
        print(f"{run.name}: unconnected {unconnected}; DRC errors {errors or 'none'}; "
              f"{len(items) - vias} segments, {vias} vias; {path}")
    if not results:
        return 1
    best = min(results, key=lambda r: (r[0], r[1]))
    print(f"best: {best[2].name} with {best[0]} unconnected. Inspect it, then copy it over the project board yourself.")
    return 0 if best[0] == 0 and best[1] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
