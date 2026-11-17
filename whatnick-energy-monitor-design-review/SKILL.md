---
name: whatnick-energy-monitor-design-review
description: Run independent design reviews of a KiCad schematic or routed board with fresh reviewer agents (or people) who have not seen the designer's reasoning. Use before layout and before fabrication, when ERC and DRC are clean and the question is whether the design is right, for splitting a review by area, writing reviewer briefs, giving reviewers the netlist rather than the drawing, re-reviewing after fixes, triaging findings into must-fix, should-fix and accepted, and for the catalogue of faults such reviews found that ERC, DRC and schematic parity all passed.
compatibility: Tool-neutral method; examples and scripts assume KiCad 10 with kicad-cli, and KiCad's bundled Python for the board audit. Reviewers need read access to the netlist, schematic PDF, board file, parts list, requirements and datasheets.
metadata:
  org: whatnick
  domain: pcb-design
---

# Independent design review

A design that passes ERC, DRC, schematic parity and a netlist-against-intent check
is consistent with what its author intended. None of those checks asks whether the
intent is right. On the project this skill comes from, with all of them clean:

- five schematic reviewers found one blocker and about twenty real faults before
  layout, none of them a wrong pin number;
- a layout reviewer found two must-fix faults on a board with zero DRC errors: a
  card socket mounted backwards and every supply net routed at signal width;
- a second review of each fixed design found new faults introduced by the fixes.

The cost was a few hours of reviewer time. The alternative was a second fabrication
run of assembled boards.

## When

- **Schematic review** after ERC is clean and before placement starts. A fault found
  after routing costs a re-route.
- **Re-review** of whatever the fixes rewrote. The first review saw the old circuit.
- **Layout review** when the board is fully routed with zero DRC errors and before
  any manufacturing output is made.
- **Layout re-review** after the fixes, by a reviewer who does not read the first
  reviewer's working files and measures afresh.

Ask the owner before spending the review; say plainly what has and has not been
checked so far. "It looks good, I did not review it electrically" is the usual
state of a schematic that has only been looked at.

## What makes the review independent

- **A fresh reviewer.** A new agent with no access to the design conversation, or a
  person who did not draw it. The designer re-reading their own work confirms it.
- **Evidence, not conclusions.** Give the netlist, the PDF, the board file, the
  requirements, the parts list and the datasheets. Do not give the reasoning, and do
  not say which parts you believe are fine. A reviewer handed a hypothesis returns
  it confirmed.
- **An adversarial brief.** "Your job is to find faults before layout; assume there
  are some." Add "no finding is an acceptable result for a check; do not pad", or
  the report fills with style notes.
- **Read-only.** Reviewers do not edit, commit, regenerate or route. Name the
  generator scripts they must not run, and give them a scratch directory. A layout
  reviewer works on a copy of the board.
- **A reviewer's report is advice.** The designer verifies each must-fix claim
  against the primary source before acting (the backwards socket was confirmed
  against the maker's drawing before anything moved), and the owner decides what to
  accept.

## Split by area, one reviewer each

One reviewer for the whole design skims. Separate reviewers, run in parallel, each
with a list of specific questions, read the datasheets. A split that worked for an
MCU board:

| Reviewer | Scope |
|---|---|
| Power and USB | Connector, protection, regulator against its datasheet, current budget against the fuse and regulator |
| Each complex IC and its support circuit | Pin by pin against the datasheet pin table; straps and what they latch; crystal; reset |
| External interfaces | Level translators: pinout, direction logic, every partial-power state, floating inputs, what a connected device sees while the MCU is in reset |
| MCU, memory, user I/O | Supply pins, alternate functions, clocks and oscillator margin, boot and reset, bus pull-ups |
| Symbol-to-footprint mapping | Every distinct symbol and footprint pair against the maker's drawing: pad numbering, pin 1, exposed pad size, which pads of a 4-pad part are common |
| Layout | Everything in the layout brief below |

The footprint reviewer is the one most often skipped and the only defence against a
mapping fault, which passes ERC, parity and DRC and yields a dead board.

## What to hand over

- **A readable netlist as ground truth.** Export with `kicad-cli sch export netlist`
  and convert with `scripts/netlist_to_text.py`: one line per component (reference,
  value, footprint, MPN, sheet) and one line per net with every pin, its function
  and type. Tell reviewers to check connectivity there and to use the PDF only for
  orientation. Reviewers who trusted the netlist caught things the drawing hid, and
  one compared all 1,055 pad nets on the board against it.
- **Datasheets on disk**, current revisions, named consistently. Manufacturer sites
  block automated downloads often enough that mirrors and old revisions creep in;
  ask the owner to fetch the ones that matter and say which revision each check used.
- **Requirements and the pin or parts tables** the design was generated from.
- **How to look**: the commands for rendering a PDF page or a board region, the
  interpreter that has pcbnew, known tool pitfalls. Otherwise each reviewer
  rediscovers them.
- **What is already known and accepted**, so it is not re-reported: "do not re-report
  unless you find it is worse than stated".
- **Confidentiality rules**, restated in every brief: which files are confidential
  and must never be uploaded, quoted or searched for, and that personal and project
  names stay out of web requests. Part numbers are fine.

## Brief template

```
You are an independent reviewer of <schematic area | routed board>. Your job is to
find faults before <layout | fabrication>; assume there are some. Review only: do not
edit, commit or regenerate anything, and do not run <generator scripts>. Scratch
files go in <directory>.

The design: <two sentences>. Files: <netlist.txt = ground truth for connectivity;
schematic PDF with page numbers; board file; requirements; parts list; datasheets>.

Check at least: <numbered, specific questions; for each IC "every pin in the netlist
against the datasheet pin table for the exact package"; for each interface "what
happens when side A is powered and side B is not, and when the MCU is in reset">.

Do not rely on memory for any pin number or value: read it from a document and say
which. If you need a fact that is not in the files, say it is unverified.

Already known and accepted: <list>.
Confidential: <files>; never upload, quote or search for their contents.

Report: findings most severe first, each with refs and nets, what is wrong, the
evidence (datasheet section or netlist line, or a measurement with coordinates), the
consequence, a concrete fix and your confidence. Group as must fix / should fix /
accept for a prototype. Then what you checked and found correct, and what you did
not get to. No finding is an acceptable result; do not pad.
```

For a layout review add: "DRC reports 0 errors and 0 unconnected, so look for what
DRC does not catch. Measure, do not eyeball." and name the origin of the board's
coordinates so positions in the report can be found.

## The layout brief: what DRC does not check

Ask for each of these explicitly. Every one produced a finding on a DRC-clean board.

- Mechanical: connectors that take a card, plug or cable face the board edge per the
  maker's drawing, with nothing in the insertion path; edge overhang as drawn.
- Track width against current for every supply net that is not a plane; length
  against straight-line distance.
- Regulators: input loop, switch node length and width, feedback node length and
  what runs beside it, output capacitor at the inductor, number of ground vias.
- Decoupling: track distance from each supply pin to its own capacitor, not the
  distance to the nearest capacitor on the net.
- Exposed pads: number of ground vias; signal vias under the package.
- Planes: one piece per net, no tracks on them, no islands; what crosses any void;
  pads at the edge of a void still solidly connected.
- Copper under screw heads and near unplated holes, on outer and inner layers.
- Differential pairs: width and gap against the fab's calculator figure, coupled
  length, skew, vias, what is underneath; no meander for length where it is not
  needed.
- Crystals: track length, vias, load-capacitor stub, foreign tracks underneath.
- Reset and other sensitive single nets: where the capacitor is, total net length.
- Vias in or touching SMD pads.
- Silkscreen: labels read correctly from the side they are printed on; text hidden
  under parts; polarity and pin-1 marks; required warnings present.
- Fab limits, read from the fab's page that day.

`scripts/audit_board.py` measures several of these without changing the board: vias
whose drill is inside an SMD pad, outer-layer copper close to unplated holes, supply
nets with track narrower than a threshold, planes in more than one piece, and a
length, width and via report for named nets. Run on the board that later failed
review, it reports the thin supply nets and the tracks under the screw heads.

## Triage

- Report to the owner by severity, with your own check of each must-fix.
- Fix must-fix and should-fix items in one pass where they need the same rework (a
  re-route is expensive; do it once).
- Record what was not done as asked and why (a capacitor that could not sit at its
  pin without blocking a bus).
- Record what is accepted for this revision, in the project log, so the next
  reviewer and the bring-up engineer can see it.
- Items that need the owner's decision (a part swap with a cost, a requirement that
  turns out to be the designer's invention) go to the owner as questions, not fixes.
- Firmware consequences (a strap that must be backed by a register write, a pull-up
  that must be enabled, a drive-strength setting) are written beside the circuit on
  the schematic and collected for the firmware owner.

One review item worth its own line: reviewers asked why a requirement was what it
was, and a "1.2 V host" target turned out to have been invented by the designer, not
asked for. Relaxing it to what the owner needed removed a part and a compromise.

See `references/review-findings.md` for the catalogue of faults, grouped by kind, to
seed checklists and briefs.
