---
name: whatnick-energy-monitor-freerouting-batches
description: Autoroute dense KiCad 10 boards with Freerouting 2.x run headless in parallel batches, and get a trustworthy result. Use when a board is at the edge of routability, when results swing wildly from one attempt to the next, when plane layers get cut up or power nets come out at signal width, for checking and patching the Specctra DSN KiCad exports, the Freerouting command-line settings that matter, deciding what to change between batches, and judging a run by KiCad DRC rather than the router's own score.
compatibility: KiCad 10 (verified on 10.0.8) with its bundled Python and kicad-cli on PATH; Freerouting 2.5.0 jar and a Java runtime. Scripts never write to the board they are given.
metadata:
  org: whatnick
  domain: pcb-design
---

# Freerouting in parallel batches

The routing skill has the basic DSN/SES flow. This skill is for the case where that
flow almost works: a multi-layer board where each attempt leaves a handful of
connections open, a different handful each time. It records what was learnt routing one such board (about
300 parts, 86 x 64 mm, four layers with two planes) through some sixty autorouter runs.

## Three facts to plan around

1. **Near the edge of routability the outcome is chaotic.** Runs on what was meant
   to be the same board left 21 and 1 connections open; five more gave 8, 1, 10, 4
   and 0. A single run tells you almost nothing about whether a change helped.
2. **Freerouting itself is deterministic.** Two Freerouting 2.5.0 runs started
   together on the same DSN file wrote byte-identical session files (checked on a
   partly routed copy of the same board, 8 passes). The spread in point 1 came from
   the inputs: the script that rebuilt the board before each run placed its plane
   vias slightly differently each time (364 or 365 vias, different pads left without
   one, for the same placement). Tiny differences in the input are enough.
3. **Routing passes use one core.** Freerouting logs "autorouter pass is
   single-threaded"; only its optimiser, which runs on completely routed boards, is
   threaded. A process sits near 200% CPU, and no setting makes one run faster.

So: make several deliberately different attempts at once and keep the best. Re-running
an unchanged DSN buys nothing. Judge a placement change by a batch, and by which
nets stay open, not by one count. On a 14-core machine four or five runs side by
side cost little more wall time than one (10 to 16 minutes each for the board above).

`scripts/freeroute_batch.py BOARD --jar freerouting.jar --runs 4 --power-layer In1.Cu
--power-layer In2.Cu --expect-track 0.127` does this. Run 1 routes the board as
exported; each further run gets the same DSN with its net list in a different seeded
order (`patch_dsn.py --shuffle-nets SEED`), which changes the order the router works
in. It makes per-run directories, checks and patches the DSN, runs in parallel,
imports each session, refills zones, runs KiCad DRC per run, prints a table of
unconnected counts and names the best run. It leaves the source board alone; copying
a winner over the project board is your decision. Because every input is a file and
every variation a seed, a good result can be reproduced, which the reference
project's rebuild-and-hope batches could not.

How much the shuffle spreads results on a board routed from scratch is not yet
measured. The script was tested on a copy of the finished board with about thirty
nets ripped up: the unshuffled run reproduced itself exactly three times, and two
shuffled runs differed from it and from each other (4, 5 and 4 unconnected).

## Check the router's input before believing any output

Two faults in the exported DSN made the first two batches on the reference board
meaningless. Both are silent.

**Planes exported as signal layers.** KiCad 10 writes `(type signal)` for every copper
layer. Freerouting then routes on the plane layers: in one run 1,151 segments on the
two planes and 36 on the bottom layer, the ground plane cut into 29 pieces and the
supply plane into 13, and plane vias stranded on islands. Mark the plane layers
`(type power)` in the DSN (`scripts/patch_dsn.py --power-layer In1.Cu ...`). Expect the
honest result to look worse at first: the runs that borrowed the planes had been
flattering the board.

**Rules that are not the project's.** If the DSN is exported by the same Python
process that built the board, it can carry KiCad's built-in defaults (0.2 mm track
and clearance, 0.6/0.3 mm via) instead of the project's net classes; see the
scripted-layout skill's pcbnew notes for the experiment. With 0.2 mm clearance a
0.4 mm pitch QFN cannot be escaped at all, so every pin of that part stayed open in
every variant, and the comparison between variants was noise. `patch_dsn.py` prints
the width, clearance and via of the board rule and every class, and `--expect-track`
fails the job when the default is not what you designed for.

Do not fix the second fault by rewriting every width in the DSN to the signal width.
That was done on the reference project, and it erased the power class: supply nets
were routed at 0.127 mm with long detours, which an independent review later rated
must-fix. Export from a fresh process so the classes come through, and route the
supply nets by script anyway.

Other things to confirm in the DSN, all visible in `patch_dsn.py`'s printout:

- Locked tracks and vias appear as `(type fix)`; unlocked as `(type route)`. If your
  scripted routes show as `route`, the autorouter may move them.
- Rule areas appear as `keepout` polygons on their layers.
- The via padstack named in `use_via` is the size you intend.

## Command line

```bash
java -jar freerouting.jar -de board.dsn -do board.ses \
  --router.autorouter.max_passes=30 \
  --router.fanout.enabled=false \
  --router.job_timeout=00:20:00 \
  --router.automatic_neckdown=false
```

Verified with Freerouting 2.5.0:

- `-mp N` still works but logs that it is deprecated in favour of
  `--router.autorouter.max_passes`.
- **Set `--router.job_timeout`.** Left at its default, the first run on the
  reference board was cut off about two minutes in, two seconds after the fanout
  stage finished, with 226 connections unrouted.
- **Turn fanout off** and place plane vias yourself (scripted-layout skill). With
  fanout on, the whole job time went on escaping pins.
- The setting names are not all in `--help`. They were found by listing the fields
  of the classes under `app/freerouting/settings/` in the jar with `javap`.
- The router stops by itself when its score stops improving, typically after 10 to
  20 passes on this board. Raising the pass limit from 20 to 40 once turned 6 open
  into 0; beyond that, more passes bought nothing.
- The log's final line gives the router's own count of unrouted nets and
  "violations". It does not equal KiCad's count. Import the session, refill zones,
  run `kicad-cli pcb drc` and use its unconnected-items list.

## Reading a batch

For each run list the unconnected items by net and by position. Then ask:

- **Is the same net open in most runs?** That is a placement or blocking problem.
  Render the area. On the reference board every recurring failure had a visible
  cause: a crystal's tracks across the strip where neighbouring pins drop vias, a
  capacitor filling the only channel for a bus, translators facing away from their
  connector, series resistors auto-placed into a pocket closed off by a supply link.
- **Is a different handful open in each attempt?** That is general congestion. Options,
  in the order they paid off: a keep-clear ring round fine-pitch parts; finer rules
  if the fab allows them without surcharge; reorder connectors and pin assignments
  to remove crossings; fewer scripted (fixed) tracks; then more layers.
- **Are plane pads open?** They need a script-placed via, not more router time.

What did not help, measured on the same board:

- **A larger board.** 110 x 78 mm routed worse than 100 x 70 mm (9 open against 1),
  and 88 x 64 worse than 86 x 64. The open connections were pins walled in beside
  fine-pitch parts, which extra area at the edges does nothing for. Six layers
  attack that directly; on the one comparison made, six layers matched the best
  four-layer variant and was not needed.
- **A scripted via fanout on every pin** of the fine-pitch parts: 24 to 42 open
  against 13 to 14.
- **A maze-router clean-up pass** that cannot rip up tracks: it connects leftover
  plane pads and a few signals, and reports the rest as having no path.

Expect several batches after any placement change. Closing the reference board the
second time, after a review forced a re-placement, took six batches of three or four
runs: 8/14/10, 3/4/1, 3/7/5, 12/4/2/14, 4/9/5/6, 0/8/4/6, with one placement fix
between each.

## Running batches without fooling yourself

- One directory per run, holding its own copy of the board, project file, custom
  rules file, DSN, session, log and DRC report. Delete it before reuse. A wait loop
  once read the DRC file left by the previous batch and reported a result for a run
  that had not finished.
- Wait on the processes, not on a sleep: a watcher that looked for the Java process
  before it had started exited at once and reported nothing.
- Kill stray runs before starting a batch on changed input, and never let a run
  write to the project board.
- Keep the best run of each batch in a named directory until a better one exists.
- Make the board build deterministic (sort every collection you iterate; do not
  depend on set order or on the order pcbnew returns footprints) and put any
  variation behind a seed. Otherwise the installed board cannot be regenerated, and
  the commit that installs it must say so.
- Commit the script change that produced a batch with its result in the message.

## After the autorouter

A run with zero unconnected items and zero DRC errors is not a finished board. The
autorouter leaves, and DRC accepts:

- vias inside or touching SMD pads (two in pads, six within 0.03 mm of a pad on the
  reference board);
- signal tracks under crystals and close to their pads;
- 40 to 90 mm routes with 6 to 14 vias for nets whose pins are 15 mm apart;
- every net at the one width it was given;
- tracks under mounting-hole screw heads unless a keep-out says otherwise;
- zero-length and doubled-back segments.

Sweep for these by script (the design-review skill's `audit_board.py` covers the
first, fourth and fifth) and have the routed board reviewed before fabrication.

## Other routers

One GPU-accelerated open-source autorouter was tried on the same board for
comparison (version 1.0.0). Its self-test passed; the
routing job sat at 0% CPU in its multi-threaded mode, and single-threaded it stalled
after about a minute of CPU time in two hours without writing a board. That is one
attempt on one machine, recorded so the next attempt starts by sampling the process
rather than waiting.
