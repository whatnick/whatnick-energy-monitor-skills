---
name: whatnick-energy-monitor-scripted-layout
description: Build, place and pre-route a KiCad 10 board entirely from Python with pcbnew, so the layout can be regenerated and tried in variants. Use for building a board from a schematic netlist, placement plans with automatic placement of passives beside their pins, keep-clear rings and corridors, plane pours with a via for every plane pad, keep-out rule areas, scripting the nets an autorouter must not be trusted with (power, USB, Ethernet, crystals), routing variants in separate directories, and the pcbnew API quirks of KiCad 10.
compatibility: KiCad 10 (verified on 10.0.8) with its bundled Python 3.9 and pcbnew; kicad-cli on PATH for DRC and renders.
metadata:
  org: whatnick
  domain: pcb-design
---

# Scripted board build, placement and critical routing

Use this skill when the board file is a build product: a script reads the schematic
netlist, places every footprint, pours planes, routes the critical nets and hands the
rest to an autorouter. It extends the layout-design and routing skills, whose
placement and routing priorities still apply; this one covers the mechanics and what
went wrong doing it on a dense 4-layer board (about 300 parts on 86 x 64 mm, LQFP-144
at 0.5 mm pitch, QFN-56 at 0.4 mm pitch, one-sided assembly).

The payoff is iteration. A placement change is one edited coordinate and a 20 second
rebuild; a design-rule change or a different board size is a variant routed in
parallel with four others. The cost is that every judgement a layout person makes by
eye has to be written down as a rule, and the ones you forget show up in review.

## Pipeline

Run each step with the Python interpreter that ships with KiCad; a system `python3`
cannot import `pcbnew`. Stop and run DRC after the steps marked with a gate.

1. **Board from netlist.** Parse `kicad-cli sch export netlist` output; for each
   component load its footprint from the library, set reference, value, fields, the
   symbol path (for schematic parity) and the pad nets.
2. **Project file.** Write the `.kicad_pro` JSON yourself: design rules, net classes
   and net-class patterns. `pcbnew.SaveBoard` does not write them.
3. **Placement.** Fixed positions for everything that matters; automatic placement
   for the rest. Gate: no courtyard overlaps, parity clean.
4. **Planes and keep-outs.** Zones on the inner layers; rule areas round mounting
   holes and anywhere copper must stay out.
5. **Critical routes**, locked. Before the plane vias, so the vias keep clear of them.
6. **A via for every plane pad.** Gate: with only these in place DRC must show zero
   errors. If the board is not clean before the autorouter, it will not be after.
7. **Autoroute** copies of the board in batches (see the freerouting-batches skill).
8. **Post-process** the winning copy: vias that landed in pads, silkscreen pass.
9. **Independent review** (design-review skill), then loop back to step 3.

Make every step deterministic: sort what you iterate (footprints, pads, nets), and
do not let set order or the order pcbnew returns items decide a via position or a
placement. On the reference project the plane-via step did not give the same result
twice (the cause was not investigated; iteration order is the likely one), so every
rebuild gave the autorouter a slightly different board and a very different result,
and the board that finally closed cannot be regenerated from the scripts.
Put deliberate variation behind a seed instead.

Always build variants in their own directories and copy a result over the project
board only when it has closed with zero unconnected items. Make the route script
refuse, or at least warn loudly, when asked to regenerate a board that is already
routed: one careless run replaces a zero-open board with a different, incomplete one.

## Placement plan

- Keep a dictionary of reference to (x, y, rotation) for connectors, ICs, crystals,
  switches and every part whose position is a design decision. Positions are the
  courtyard centre measured from the board's top-left corner, so they survive a
  change of footprint origin.
- Place the remaining passives automatically beside the pin they connect to: for each
  part pick the anchor pin (prefer a pin of a multi-pin part on the same sheet),
  then search outward in a spiral for the first spot whose courtyard is free.
- **Give every fine-pitch part a keep-clear ring.** Automatic placement packs
  capacitors against the pins and boxes them in. On the reference board, with no ring
  8 signals failed to route; with a 1.6 mm ring all routed; with 2.6 mm it was worse
  again (5 failed) because parts were pushed too far out. Treat 1.6 mm as a starting
  point, not a constant.
- Add keep-clear rectangles for corridors a scripted pair or a row of series
  resistors needs, so the placer does not drop a capacitor in them.
- Report the total signal wirelength (sum of net bounding-box half-perimeters) after
  each placement; use it to choose an IC rotation and to see whether a change helped.

What automatic placement gets wrong, every time, until told otherwise:

- **Decoupling lands near the IC, not at the pin.** "Nearest free spot to the pin" for
  twelve capacitors on one rail puts most of them in a clump on one side. A capacitor
  can also attach itself to a strap pin tied to the rail instead of the supply pin.
  Hand-place the capacitor for every supply pin that matters (core regulator outputs,
  PLL and analogue supplies, PHY supplies, regulator input and output) and name the
  pin in a comment beside the coordinate.
- **Parts with a flow direction face the wrong way.** Level translators and series
  resistor packs must sit with their connector side towards the connector. Two I2C
  translators facing away from their headers accounted for the open connections of
  a whole batch of runs.
- **Connector orientation.** Check the entry side of card sockets and plug-in
  connectors against the mechanical drawing, not the footprint's silkscreen. A
  microSD socket was placed with its closed end at the board edge and the card slot
  facing a capacitor; DRC, parity and two reviews of the schematic all passed it.
- **Order a rank of connectors by the order their signals leave the main IC.** That
  alone took one floorplan from 8 open connections to 6, and with more router passes
  to none.
- **Crystals: place so the two tracks are short and stay in front of their own pins.**
  A crystal centred on its two pins works. A crystal offset along the pin row puts
  its tracks across the only strip where neighbouring pins can drop a via.
- **A capacitor at the ideal spot can block a routing channel.** One placed directly
  under a core-regulator pin filled the 2.3 mm channel a whole bus needed, and that
  bus failed in every run until the capacitor moved 1.5 mm to the package corner.
  Check what else has to pass.

Scaling a floorplan down by a factor does not work: connectors and switches do not
shrink, so they collide first. A smaller board needs a new arrangement. Draw
candidates as courtyard rectangles to scale and compare the fill (total courtyard
area divided by board area). The reference board routed on four layers at 54% fill
with ease and at 71% only with the measures in this skill; that is one data point,
not a rule.

## Planes, plane vias and keep-outs

- On four layers use signal / ground plane / supply plane / signal and give every
  surface-mount pad on a plane net its own via, placed by script: just off the end of
  the pad on its long axis, pointing away from the part's centre, joined by a short
  track as wide as the pad allows. Try straight positions at increasing distance
  before any diagonal. A pad that finds no position is listed; most are supply pins
  hemmed in by their own capacitor, which is the connection you want anyway.
- Without this the autorouter has to do it, and the Freerouting option that does
  (fanout) consumed the whole job time on the reference board. The first autoroute
  left 196 connections open, 149 of them plane pads. With script-placed vias, what
  the autorouter leaves open is signals.
- Exposed pads that are a part's only ground get several vias (five worked: centre
  plus four on the centre lines, where the footprint's paste windows leave gaps).
  One via under a QFN is a review finding.
- Reject a via position that lands on another pad of the same net: electrically
  legal, and a solder thief.
- **Mounting holes need keep-outs you add yourself.** The stock mounting-hole
  footprint has a courtyard and nothing else. Add a rule area on both outer layers
  out to the screw-head radius (3.2 mm for M3 worked; a 7 mm washer needs more) with
  tracks and vias disallowed, and a rule area on the inner layers pulling the planes
  back from the hole. Before this, the autorouter ran signal tracks 0.4 mm from two
  holes, under the screw heads, and both planes came within 0.25 mm of every
  unplated hole.
- A keep-out that clips a plane can leave a through-hole pad hanging on thermal
  spokes a fraction of a millimetre wide. DRC counts it as connected. After adding
  any plane void, measure the remaining connection of every pad near its edge.
- Keep supply planes out from under integrated-magnetics jacks if the PHY datasheet
  asks for it, but stop the void short of the jack's own supply and LED pins.

## What to route by script

Route by script what the autorouter will do badly and the board cannot tolerate:

- **Every supply net that is not a plane**: regulator input, switch node, output up
  to the plane vias, core-voltage rails, filtered analogue supplies, reference-voltage
  rails. An autorouter given a single track width routes all of these at signal
  width; on the reference board a 5 V net took 50 mm at 0.127 mm to cover 18 mm, and
  the review estimated a shorted output would burn the switch-node track. Width per
  connection belongs in the script (0.2 to 0.8 mm was used).
- **Differential pairs**: connector or PHY to the far end, side by side, with any
  unavoidable crossing designed in. Swapping two identical channels of a protection
  array in the schematic removed a crossing that the first version solved by
  threading one line between a resistor's pads.
- **Short analogue or bias connections**: feedback divider at the regulator pin,
  PHY bias resistor, regulator filter capacitors.
- **Local supply stubs** from a pin to its hand-placed capacitor.

Be careful with everything else. Fixed tracks remove the autorouter's freedom on a
board that only just routes:

| Scripted on the reference board | Autorouter runs | Connections left open |
|---|---|---|
| Nothing | 3 | 8, 6, 0 |
| USB, Ethernet and all four crystals | 8 | 13 to 35 |
| USB and Ethernet only | 5 | 8, 1, 10, 4, 0 |

Scripted crystal tracks and the loops to their load capacitors walled in the
neighbouring MCU pins. Giving the crystals back to the autorouter (keeping the
improved placement) closed the board; the price was crystal tracks of 9 to 14 mm, two
of them through vias, accepted for a prototype. After a later re-placement, crystals
of the two smaller ICs were scripted again without harm. The lesson is to script a
net only when you have looked at what its track blocks.

A scripted via fanout for every pin of the fine-pitch parts (two staggered rows of
vias outside the pin row) was tried to stop pins being walled in. It made the
autorouter worse: 24 to 42 open before clean-up against 13 to 14 without. It was
removed.

## A small critical-net router

A grid router of about 200 lines is enough: A* over a 0.05 mm grid with 45 degree
moves, each connection given as (net, from, to, layer, width), where an end is a pad
`REF.PIN`, a named via, or a waypoint `at:x,y`. Later routes treat earlier ones as
obstacles. Lock what it lays so the autorouter keeps it (locked tracks export to the
router as fixed).

- KiCad's Python has no numpy; use `bytearray` grids. It is Python 3.9: no
  `itertools.pairwise`, no `match`.
- Model a track as a chain of round-ended pieces. Modelling diagonal segments by
  their bounding boxes blocked two parallel 45 degree tracks that fit easily.
- Waypoints are how you express intent ("pass beside the other line, not under the
  inductor"). When a route fails, render the region and look before changing code.
- Print "N of M routed" and the failures on every build, and stop before autorouting
  if any scripted route failed. A batch of autoroutes launched before noticing one
  failed scripted net is half an hour wasted.
- A maze router that cannot rip up existing tracks is of limited use as a finisher
  after the autorouter: it gave leftover plane pads their vias and closed a handful
  of signals per run, but reported "no path exists" for most of what the autorouter
  left, because those pins were walled in. If you write one, make it exhaustive and
  make it say whether it hit its search limit or proved there is no path.

## Looking at the result

- `kicad-cli pcb drc --format json --severity-all --schematic-parity` after every
  build; parse the JSON and print counts by type plus the unconnected items.
- `kicad-cli pcb render --side top --width 2000 --height 1500 --output top.png` for
  the overall picture; `--perspective --rotate "-55,0,-60"` for connectors.
- For routing detail, `kicad-cli pcb export svg --layers F.Cu,B.Cu,Edge.Cuts
  --mode-single --page-size-mode 2 --exclude-drawing-sheet`, rasterise with any SVG
  renderer at about 2000 px wide, and crop to the region in question. Write a
  small `view board out.png x y w h` helper early; it gets used hundreds of times.
- Parts marked do-not-populate are left out of 3D renders. To show them, render a
  copy with the attribute cleared.

See `references/pcbnew-kicad10-notes.md` for the API calls that work, the ones that do
not, and the wrapper pitfalls.
