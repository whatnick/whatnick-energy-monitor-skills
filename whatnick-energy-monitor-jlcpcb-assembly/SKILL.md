---
name: whatnick-energy-monitor-jlcpcb-assembly
description: Design a KiCad board for JLCPCB fabrication and assembly. Use for 4-layer design rules and the dated capability figures behind them, reading the JLCPCB impedance calculator for USB and Ethernet pairs, via sizes and the price tiers the order form attaches to them, hole-spacing rules and a KiCad custom rule for them, choosing parts by LCSC stock and basic/extended class, modelling assembly fees and cost-reduction options, the LCSC schematic field, fetching 3D models by LCSC number, and the checks still owed before an order.
compatibility: KiCad 10 project files (.kicad_pro, .kicad_dru). Capability and fee figures were read from JLCPCB's public pages on 2026-11-13 and 2026-11-14, and one quote form on 2026-11-15; re-read them before relying on them. No ordering automation is included.
metadata:
  org: whatnick
  domain: pcb-manufacturing
---

# Designing for JLCPCB fabrication and assembly

This skill records what one 4-layer, one-side-assembled board (about 300 parts,
55 BOM lines, five boards) needed to know about JLCPCB before layout and before
choosing parts. It stops before ordering: the export of Gerbers, BOM and placement files and the
rotation corrections had only just begun when this was written, and nothing here
covers them beyond what the first upload of the bare-board files showed.
For bare-board ordering elsewhere see the elecrow-ordering skill; the same
authority rule applies here (prepare and quote, never check out or pay without the
owner).

Every number below carries the date it was read. JLCPCB changes its pages without
notice: one older help page that a search engine still quotes (0.5 mm between holes
of different nets) now returns 404. Re-read the capability page at the start of
layout and the fee page before quoting, and write the date beside each number you
copy into the project.

## Fabrication rules used (4 layers, 1.6 mm, 1 oz outer)

Read from the PCB capabilities page on 2026-11-13 and again on 2026-11-14.

| Item | JLCPCB figure | Used on the board | Why |
|---|---|---|---|
| Track / space, multilayer 1 oz | 0.09 / 0.09 mm | 0.127 / 0.127 mm | Started at 0.15 mm and tightened to route a 0.4 mm pitch QFN; 0.1 mm also routed and was not needed |
| Via | 0.15 mm hole / 0.25 mm pad minimum | 0.25 mm hole / 0.45 mm pad | **Costly mistake, see below.** The capability page was read as charging extra for 0.2 and 0.25 mm holes only when the pad is under 0.45 mm; the order page charges for the 0.25 mm hole itself |
| Via hole to via hole | 0.2 mm | closest pair 0.33 mm | |
| Pad hole to pad hole | 0.45 mm | 0.45 mm board rule | |
| Via hole to track | 0.2 mm | 0.227 mm (0.1 ring + 0.127 clearance) | |
| Inner layer, via hole to copper | 0.2 mm | 0.2 mm zone clearance | |
| Inner layer, plated pad hole to copper | 0.3 mm (one reading of the page; not confirmed) | 0.2 mm | Open: let their DFM check settle it |
| Copper to board edge | 0.2 mm | 0.3 mm rule, 0.5 mm planes | |
| Solder-mask dam | 0.10 mm | 0.15 mm or more | |
| Silkscreen text | 1.0 mm high, 0.15 mm line (as read by a reviewer) | 0.8 mm / 0.12 mm | Accepted for a prototype; expect thin print |

The page does not say whether hole spacing is edge to edge or centre to centre. KiCad
measures edge to edge, the stricter reading.

**The order page is the authority on price, not the capability page.** When the
finished board's Gerbers were uploaded on 2026-11-15, the quote form's "Min via hole
size" option defaulted to 0.3 mm hole / 0.45 mm pad. Selecting the 0.25 mm hole the
board actually uses took five bare boards from $8.00 to about $45 before any finish
upgrade: $17.00 for the hole size, plus a 4-wire Kelvin test ($16.91) and TG155
material ($3.44) that the option forces. The free tier is a 0.3 mm hole with a 0.4
or 0.45 mm pad. Lessons:

- Before fixing the via size, put a dummy board through the quote form and click
  through the via, material and test options to see which values move the price.
- Had the board been designed with 0.3 mm holes in 0.45 mm pads the ring would be
  0.075 mm. Whether that passes their check was not confirmed; choose the via with
  both the price tier and the annular-ring rule in view (a 0.3 mm hole in a 0.5 mm
  pad keeps a 0.1 mm ring at the cost of routing room).
- The same upload confirmed the things that could not be known earlier: the board
  was detected as 4 layers, 64 x 86 mm; Economic assembly was offered for it;
  specifying the JLC04161H-7628 stackup was free; the default finish is leaded HASL
  and ENIG was $17.20 for the order.

KiCad has one `min_hole_to_hole` setting and applies it to vias and pad holes alike.
Set to JLCPCB's pad-hole figure it produced 73 warnings on via pairs 0.33 to 0.45 mm
apart, all of which JLCPCB allows. Relax it for via pairs with a custom rule in
`PROJECT.kicad_dru`, which `kicad-cli pcb drc` picks up from beside the board:

```
(version 1)
# Via holes may be 0.2 mm apart; the 0.45 mm board setting is the figure for
# pad holes. (JLCPCB capabilities page, read 2026-11-14.)
(rule "via hole to via hole"
  (condition "A.Type == 'Via' && B.Type == 'Via'")
  (constraint hole_to_hole (min 0.2mm)))
```

In the `.kicad_pro`, moving to the 0.45/0.25 mm via needed
`min_via_annular_width` 0.1 and `min_hole_clearance` 0.2 as well; with KiCad's
defaults every such via is an `annular_width` error.

Layer use that worked: L1 signals and all parts, L2 solid ground, L3 the main supply,
L4 signals. Keep-outs and plane pull-backs round mounting holes are your job (see
the scripted-layout skill).

## Controlled impedance: read the calculator, not a formula

- The default 4-layer 1.6 mm stackup is JLC04161H-7628: 0.2104 mm of 7628 prepreg
  between L1 and L2.
- The impedance calculator has no API that could be queried from a script; the
  board owner read it and sent screenshots. Ask for exactly this: board type rigid,
  4 layers, 1.6 mm, inner 0.5 oz, outer 1 oz, units mm; one row per target with type
  "differential pair" (not coplanar, unless the top layer really has a ground pour
  beside the pair), signal layer L1, bottom reference L2, and the trace spacing you
  can actually achieve.
- **Check which stackup tab the result is under.** The calculator shows several; the
  first screenshot came from a tab marked "Special" (JLC04161H-7628A, 0.2944 mm L1
  to L2) and gave 0.38 mm for 90 ohm, against 0.25 mm on the standard stackup.
- Results for the standard JLC04161H-7628 tab, read 2026-11-14:

| Target | Spacing entered | Track width |
|---|---|---|
| 90 ohm differential (USB) | 0.15 mm | 0.2474 mm |
| 100 ohm differential (Ethernet) | 0.15 mm | 0.1826 mm |
| 100 ohm differential | 0.30 mm | 0.2725 mm |

- A closed-form microstrip estimate made before the screenshots gave 0.26 mm for
  90 ohm at 0.15 mm spacing and 0.205 mm for 100 ohm: close for USB, 12% wide for
  Ethernet. Good enough to place parts, not to order.
- The pitch of the pins the pair leaves from fixes track plus gap. For a 0.5 mm
  pitch PHY, interpolating between the two 100 ohm rows gives 0.245 mm track with
  0.255 mm gap. For a 0.4 mm pitch QFN, 0.2474 mm does not fit between neighbouring
  pins with clearance; 0.24 mm was used.
- For full-speed USB and a 10 mm 100BASE-TX run this precision is more than the
  links need. Say so in the design notes rather than pretending to control it.
- The calculator page can hang with spinners in the result cells; reload and
  re-enter.

## Choosing parts for assembly

- **Library class decides the fee.** Under Economic assembly every part type that is
  not in the basic library carries a one-off loading fee per order, whatever the
  quantity; basic parts and (assumed, not confirmed) extended parts flagged
  "preferred" do not. On the reference board 21 fee-carrying types cost more in fees
  than all the resistors and capacitors cost in parts.
- **Check stock before the schematic, and again before ordering.** Choose the
  footprint-compatible part that is in stock over the reference design's part that
  is not. Record the LCSC number, library class, stock and the date in the parts
  list. A part with 72 in stock one day had 69 the next.
- **A main IC with no JLCPCB stock** can be bought through their global sourcing
  (parts pre-order) and still be machine placed; price it from a distributor until
  JLCPCB quotes. Its lead time and handling fee were not established here.
- **Prefer basic-library passives and set the generator to refuse values outside the
  list.** A feedback divider of 68 k / 15 k from basic values replaced a textbook
  453 k that would have added a part type.
- **But do not let "basic" pick an electrically marginal part.** The basic-library
  crystals (20 pF 12 MHz with 80 ohm ESR; 12.5 pF 32.768 kHz) were chosen for the
  fee, flagged by review as start-up risks, and replaced by extended parts. A
  $3 fee is cheaper than a board that does not enumerate.
- **Footprints: use the stock KiCad footprint for the exact manufacturer part where
  one exists**, and have someone compare its pads and numbering with the maker's
  drawing. A connector was changed to a different maker's equivalent because that one
  had a verified stock footprint.
- Add an `LCSC` field to every fitted symbol beside `MPN`, `Manufacturer` and the
  distributor fields the bom-sourcing skill lists. Unpopulated hand-fit headers are
  marked do-not-populate and keep their footprints.
- Through-hole parts are hand-soldered by JLCPCB for a labour fee plus a per-joint
  charge; a single through-hole RJ45 cost more to fit than the stencil.

Looking up parts: the search box on jlcpcb.com/parts is backed by a JSON endpoint
that answers a keyword or LCSC code with library class, a preferred flag, stock and
price breaks. It is undocumented and may change or be withdrawn; use it sparingly,
cache results, and send nothing but part numbers. Distributor APIs (see the
bom-sourcing skill) cover the parts JLCPCB does not stock.

## Assembly fees (read 2026-11-13 from the assembly price page; USD)

| Fee | Economic | Standard |
|---|---|---|
| Setup | 8.18 | 25.56 one side, 51.12 two sides |
| Stencil | 1.53 | 8.21 |
| Per SMT joint | 0.0016 | 0.0016 |
| Part-type loading | 3.07 per extended type | 1.53 per type, basic or extended |
| Fixtures | none | 16.42 |
| Hand-soldered through-hole | 3.58 labour + 0.0164 per joint | same |

Economic assembly needs all SMT parts on one side; whether a given board qualifies
is decided by JLCPCB when the files are uploaded, so carry both columns until then.

Model the order in a script that reads the BOM from the schematic, fetches prices at
the order quantity, applies this table and writes a cost sheet with the date. Then
the levers are visible. For the reference order (five boards, about $320 Economic,
bare boards and shipping excluded):

- parts were 73% of the total and one MCU was 54% of the parts;
- the only large saving was assembling fewer boards (two of five saved 45%);
- replacing three DIP switches with jumper headers saved about $19, more than
  removing any single IC;
- under Standard assembly the fee is per part type of any class, so merging part
  types matters more than avoiding extended ones.

## 3D models

Fetch by LCSC number with `uvx easyeda2kicad --lcsc_id C12345 --3d --output DIR`.
Check alignment in a render. Keep the fetched files out of the repository unless you
have established the terms they come under, and commit the fetch script.

## Still owed before an order

None of these was finished on the reference project when this was written; they are
listed so they are not forgotten.

- Gerber, drill, BOM and placement (CPL) export in JLCPCB's column layout.
- **Rotation check.** Polarity and pin-1 orientation in the placement file depend on
  how each KiCad footprint's zero rotation lines up with JLCPCB's reel orientation.
  At least one LED maker numbers its terminals opposite to the KiCad footprint. The
  placement preview in the order flow is the check.
- The global-sourcing quote and their DFM report. (Economic-assembly eligibility
  was confirmed at upload, after this list was first written.)
- Fiducials or tooling holes if their assembly asks for them; none were placed.
- Stock on the day.
