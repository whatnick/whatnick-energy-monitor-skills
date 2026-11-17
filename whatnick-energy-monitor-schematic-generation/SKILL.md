---
name: whatnick-energy-monitor-schematic-generation
description: Generate multi-sheet KiCad 10 schematics from Python and prove they are wired as intended. Use when a schematic is produced by a script rather than drawn, for the S-expression format details KiCad 10 expects, pin tables as the source of truth, project symbols built from datasheet pin tables, the record-intent-then-compare-netlist check that catches shorts ERC cannot see, ERC triage on generated sheets, and making generated sheets read like hand-drawn ones.
compatibility: KiCad 10 (verified on 10.0.8) with kicad-cli on PATH; plain Python 3.9+ for the generator and the bundled check script.
metadata:
  org: whatnick
  domain: pcb-design
---

# Generating KiCad schematics from Python

Use this skill when the schematic is written by a generator and the `.kicad_sch` files
are build products. It complements the circuit-design skill, which says what to draw;
this one says how to emit it and how to know the emitted files mean what you intended.

## Decide first: is generation worth it

Generation pays when the design has a machine-readable source of truth (a pin map of
100+ MCU pins, a parts list with sourcing fields), repeated blocks, and several review
rounds ahead. It costs more than drawing for a one-off 20-part breakout. The price is
appearance: a first pass comes out electrically right and visually plain, and every
overlap has to be fixed in the generator, by rendering the page and looking at it.

## Sources of truth

Keep the facts out of the sheet generators:

- **Pin map** (YAML): one entry per MCU pin with net, function and the block it belongs
  to. Check it mechanically against the KiCad symbol for the exact part (pin number
  exists, the named alternate function is offered on that pin) before any sheet uses it.
- **Parts list** (YAML): one entry per part with MPN, manufacturer, distributor numbers,
  symbol, footprint. The generator copies these into symbol fields, so the BOM comes
  from the schematic. Make the generator refuse a passive value that is not in the
  list: that is what stops a 453 k one-off creeping in beside the stocked 15 k.
- **Pin tables for parts with no stock symbol** (YAML list of number, name, electrical
  type, optional side and order): build the project symbol library from these. Have the
  table read from the datasheet by one agent and checked by another; a wrong pin number
  is a dead board and nothing downstream will catch it.

## Workflow

1. **Spike.** Emit one sheet with one resistor and two power symbols. Run it through
   `kicad-cli sch erc`, `kicad-cli sch export netlist` and `kicad-cli sch export pdf`
   and look at the PDF. Fix the format problems here, not with 200 parts on the page.
2. **Read real geometry.** Load each symbol from the library file, flatten `extends`,
   and compute pin endpoints from the symbol's own pin positions, rotation and mirror.
   Never infer pin positions from the package drawing.
3. **Connect by construction.** Every connection is pin endpoint, wire, then a label,
   a power symbol or another pin. Record the intended net of every pin as you draw it.
4. **One generator module per sheet**, one reference-number range per sheet (1xx power,
   2xx MCU, ...), so a reference tells you where to look.
5. **Build in two passes** if you want tidy labels: the first pass finds which nets
   appear on more than one sheet; the second draws those as global labels and the
   rest as local labels on the wire.
6. **Check every build**: ERC with all severities, then the netlist comparison below.
   Treat "0 errors, 0 netlist problems" as the gate for committing a sheet.
7. **Render and look.** Export the PDF, rasterise the page (`pdftoppm -r 80`), crop
   the region you changed and view it. Text overlaps and wires through symbols are
   invisible to ERC.
8. **Never hand-edit the output.** Say so in the project notes; a GUI edit is lost on
   the next build.

## The check that matters: intent against KiCad's netlist

ERC proves the drawing is self-consistent. It does not prove the drawing is the
circuit you meant. A wire end that lands on a neighbouring pin merges two nets with no
ERC message at all; a label that misses its wire end by one grid step splits one.

So: the generator records `{(ref, pin): intended net}` while drawing, KiCad extracts
the netlist from the files, and a comparison requires that pins meant to share a net
share one and that distinct intended nets stay distinct. Names are not compared, only
grouping, so hierarchical name prefixes do not matter.

On the reference project this caught, with ERC clean each time:

- a new series resistor whose tap landed on the same x as a neighbouring line and
  shorted two signals together;
- a connector line whose label did not sit on the connector's wire, leaving the net
  split in two;
- pins that were missing from the netlist altogether in the first spike.

`scripts/check_netlist_intent.py` is the standalone form: give it the root schematic
and a JSON intent file. It runs ERC and the comparison and exits non-zero on either.

What this check cannot do is tell you the intent is right. That needs the datasheet
review described in the design-review skill.

## KiCad 10 file format facts

Verified against KiCad 10.0.8; each cost a failed spike to find.

- Stock symbol libraries are `(version 20251024)` with `(generator_version "10.0")`.
  A schematic written with an older `(version ...)` header loads; normalise it with
  `kicad-cli sch upgrade --force FILE`, after which the file reads `(version 20260306)`.
  Emitting a simple older-format file and letting `sch upgrade` rewrite it is easier
  than matching the newest writer byte for byte.
- Hidden properties are written `(property "Name" "value" (at x y a) (hide yes)
  (effects (font (size 1.27 1.27))))`. `(hide yes)` is a child of the property, not of
  `effects` as in older files. Compare your emitter's output with a file that
  `sch upgrade` has rewritten and match that.
- Power symbols are marked `(power global)` in KiCad 10 libraries (earlier files have
  a bare `(power)`). A generator that treats power symbols specially must detect them
  with a pattern that accepts both.
- Symbols that `(extends "PARENT")` must be flattened into a full definition when
  copied into the sheet's `lib_symbols`: take the parent's body, rename its unit
  sub-symbols to the child's name, and use the child's properties.
- A `PWR_FLAG` (or any pin) placed in the middle of an existing wire is not connected
  until a junction is added at that point.
- A label is attached only where its anchor touches a wire or pin. Anchor on-wire
  labels at the wire's end, with the text running back along the wire; a label
  anchored part-way along left `unconnected_wire_endpoint` warnings on the stubs.
- Text on a rotated part has its justification mirrored; test both rotations when
  placing reference and value text beside vertical parts.
- Project symbols need a `sym-lib-table` in the project directory with
  `(uri "${KIPRJMOD}/lib/NAME.kicad_sym")`, or ERC reports `lib_symbol_issues` for
  every project part.
- Derive UUIDs deterministically (for example `uuid5` of sheet, reference and role)
  so that regenerating unchanged input gives an unchanged file and diffs stay small.

## Grid discipline

Accidental contact is the main failure of generated wiring. One convention removes
most of it: pins of multi-pin parts sit on the 2.54 mm grid and net wires have
lengths that are multiples of 2.54 mm, while risers, taps and hung parts use odd
multiples of 1.27 mm. Two things drawn by different helpers then cannot coincide by
chance. The netlist comparison catches the rest.

## ERC triage on generated sheets

- `power_pin_not_driven` while the power sheet does not exist yet is expected; it
  must disappear when the rail gets its source or a `PWR_FLAG`. Rails that arrive
  through a connector pin (a reference voltage supplied by another board) need a flag.
- `pin_not_driven` on inputs whose driver lives on a sheet not generated yet is the
  same story. Give the build a way to generate one sheet alone; it should report
  these and nothing else.
- `pin_to_pin` between a `PWR_FLAG` and a bidirectional pin appears when you flag a
  net that is biased through a resistor rather than supplied. It is a warning; record
  why it is acceptable rather than removing the flag.
- A label that has the same name as a power rail draws a warning; connect supply pins
  with the power symbol, not a label of the same name.
- Zero errors is the gate. Read every warning once and write down the count that is
  expected, so a new one stands out.

## Making generated sheets read like drawn ones

A first version that connected every pin to a labelled stub was electrically correct
and was sent back as unreadable, with overlapping power symbols. What changed, and is
worth doing from the start:

- Wire parts together inside a functional block; use labels between blocks and
  global labels between sheets. Keep a label on every MCU pin.
- Hang pull-ups, pull-downs and capacitors from the wire they belong to.
- One power symbol per rail per part: join that part's pins of a rail with a short
  common wire and put a single symbol on it. Draw decoupling as a bank of capacitors
  between one rail symbol and one ground symbol.
- Put power pins on the top and bottom of project symbols and order signal pins so the
  wires to the neighbouring part run straight.
- Series resistors in adjacent rows: small text on the wire, value left, reference
  right.
- A heading for each block, and the firmware-visible facts (address, strap result,
  required pin configuration) as text beside the circuit they describe.
- A connector may use a single-column symbol with a two-row footprint when that keeps
  the wires straight; pin numbers are what tie the two together, so state the
  odd/even row arrangement in the pin map.

## Outputs for other stages

- `kicad-cli sch export pdf` for human review.
- `kicad-cli sch export netlist --format kicadsexpr` for the board builder and for
  reviewers. Convert it to a readable text listing (see the design-review skill's
  `netlist_to_text.py`) and treat that listing, not the drawing, as ground truth for
  connectivity.
