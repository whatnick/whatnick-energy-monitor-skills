# Layout Reference

## Connector Patterns

- Compact V93XX style: one 0.1 inch header and bottom-side test pads on a small rounded board.
- Compact ADE9000 JST style: JST-SH for power/SPI, analog headers for measurement pairs, bottom-edge test pads for CF/IRQ/clock/reset.
- ATM-style bench style: stereo jacks for current clamps, screw terminals for voltage inputs, grouped 0.1 inch digital/debug header along one side.
- Breadboard-only style: put the main 0.1 inch header on a long edge, keep IC support parts near the IC, and push low-use debug signals to bottom-side test pads.
- PCI/riser style: place the edge/backplane connector first, then place ICs so analog and host buses fan out from that fixed datum without crossing.
- FeatherWing style: lock the Feather headers and outline first, then place measurement connectors and mode jumpers where they do not break stacking or USB/battery access.
- PMOD style: put the host/chain connectors at one short edge, field connectors
  at the opposite edge, and reserve readable long-edge silkscreen strips so
  branding does not compete with the analog filter rows.

## Form-Factor Layout Patterns

### Large Analog-Connector Boards

- Group CT/stereo jacks by channel along one edge and voltage screw terminals along a readable adjacent edge.
- Put burden/multiplier resistors near the jack-side current pair and anti-alias filters closer to the IC.
- Put the digital/debug header on a separate side from field wiring so logic-analyzer leads do not cross analog cables.
- Use the extra area to make channels readable and routable, not to scatter identical filter rows.

### Breadboard-Only Breakouts

- Keep the 0.1 inch header pin order useful from a breadboard or jumper-wire viewpoint.
- Put optional test pads on B.Cu along an edge, not in the middle of a routing corridor.
- Keep labels short and high-value; crowded silk is worse than a compact README pin table.
- Prefer symmetric IC-centered placement when the header is the only user connector.

### PCI/Riser DIN-Rail Modules

- Place the PCI/backplane connector and board-edge keepouts before any metering circuitry.
- Keep repeated channels in lanes that map cleanly to edge-connector pin groups.
- Use bottom-side jumpers/test points for configuration and bring-up access that should not consume top-side enclosure space.
- Preserve mechanical clearance for insertion/removal and carrier-board neighboring modules.

### FeatherWings

- Place the two Feather headers first and preserve the standard outline and mounting holes.
- Keep host-interface traces short to the Feather pins, then route analog sampling away from USB/battery/high-current host regions.
- Keep jumpers reachable when stacked; underside jumpers are acceptable for rarely changed UART/SPI or metering-mode options.
- Put voltage/current sampling connectors at the outer edges, with labels readable when plugged into a Feather host.

### PMOD Energy Front Ends

- Keep the board identity on a long edge, rotated with the board rather than
  consuming the central component field.
- Use `Made for Tiny Tapeout` when the board is intended as Tiny Tapeout
  companion hardware.
- Keep field-connector function labels adjacent to their connectors and
  readable from the insertion edge.
- A front-side Whatnick mark may occupy a central open area when it does not
  obscure references or functional labels; keep OSHW, URL, revision/date,
  licence, and safety detail on the rear when front space is constrained.
- Connector labels and logos must not force movement of settled analog
  footprints or copper.

## Decoupling Placement

- Place each capacitor adjacent to its associated pin, not in a remote capacitor cluster.
- Pair AVDDOUT, DVDDOUT, and REF capacitors with nearby GND access.
- Keep reset and clock support parts near their IC pins unless connector access requires a clear exception.

## Silkscreen And References

- Reference designators live on the matching silkscreen layer: `F.SilkS` for front-side footprints and `B.SilkS` for back-side footprints.
- Values stay on Fab layers.
- Use compact labels and fitted references at 0.8 mm high with 0.2 mm stroke
  when DRC allows. Apply the convention consistently across the board rather
  than mixing lighter 0.15 mm reference strokes with 0.2 mm annotations.
- Align repeated filter-bank references into visually consistent rows and use
  small reference-only offsets to clear parts and traces.
- Put the product name and ecosystem statement on F.SilkS; rotate them to
  follow a long edge when this preserves component readability.
- Use explicit ecosystem wording such as `Made for Tiny Tapeout`.
- Prefer the Whatnick logo on F.SilkS when a visible open area exists. Put
  attribution, `https://whatnick.com`, revision/date, licence, safety warnings,
  and the OSHW logo on B.SilkS unless the product layout calls for another
  deliberate hierarchy.
- Do not leave new silkscreen over pads, mask openings, or board edges.

### Tool-Neutral Reconstruction Contract

Capture enough intent to reproduce the markings without depending on a
particular KiCad file-format revision:

- Define marker classes: fitted component references, connector signals, test
  signals, board identity, attribution, revision/date, licence, safety, and
  logos.
- Record text height, width, stroke, rotation, layer, and a placement datum.
  Prefer a component anchor, connector pin center, or board edge over opaque
  editor coordinates.
- Record exclusions explicitly. Mounting holes, fiducials, tooling holes, and
  drill-only footprints do not receive component markers.
- Keep pin labels tied to the connector pin map, not to visual left-to-right
  order. Mirroring or viewing the back must not silently reverse the electrical
  meaning.
- Store logos as project-local vector footprints or another open vector source.
  Record source repository, scale, target layer, and intended physical size.
- Keep the board revision and build date as separate semantic fields even when
  rendered as one text string.
- Validate physical results: no silk over mask openings, no silk-to-edge or
  silk-to-silk violations, readable orientation from the normal access side,
  and no missing fitted references.

For a portable reconstruction manifest, use concepts such as:

```yaml
silkscreen:
  production_text: {height_mm: 0.8, width_mm: 0.8, stroke_mm: 0.2}
  references: {layer: component_side, exclude: [mounting_hole, tooling_hole]}
  connector_labels: {datum: pin_center, source: electrical_pin_map}
  logos:
    - {kind: whatnick, source: project_local_vector, layer: front}
    - {kind: oshw, source: project_local_vector, layer: back}
  release_markers: [revision, build_date, licence, safety]
```

This manifest is intentionally independent of footprint UUIDs, KiCad object
serialization, and any one ECAD coordinate API.

### Dense Boards: Silkscreen As A Scripted Pass

On a board with a few hundred 0402 parts on one side there is no room for every
reference, and moving text by hand is lost at the next re-route. Run the silkscreen
as an idempotent script on the routed board that changes text only, and re-run it
after every route. What worked on a 300-part, 86 x 64 mm board:

- The pass first removes the board-level text it added last time, so it can be
  re-run. It never moves footprints or copper; confirm with DRC that unconnected
  and error counts are unchanged.
- Hide references of resistors, capacitors and ferrites (values and references stay
  on the Fab layer; assembly works from the position file). Do the hiding in one
  place: a later loop that makes every reference visible silently undoes it.
- For each remaining reference try a short list of positions beside the part and
  take the first that is clear of pads, other courtyards, other text, holes and the
  board edge. Largest parts choose first, and switches before those, because their
  labels are the ones a user reads.
- Label switches, buttons and jumpers by function (the symbol value: `BOOT`,
  `RESET`, `ID`), not by reference.
- A label that finds no clear position goes on the part's own outline as a last
  resort (readable on the bare board only) or is hidden; print the counts
  ("37 placed, 8 on the part's own outline, 22 hidden") and list the hidden ones.
  Letting labels search further out is worse: one landed 11 mm away beside a
  different part.
- Put connector pin-outs on the bottom side when the top is full: one label per pin
  row beside the pins, generated from the pin map, with the MCU port pin beside the
  signal name where the board is a development target, and a title per connector.
- **Bottom-side text is read mirrored relative to the top view.** Compose each row in
  the order the pins appear when the board is turned over, and check it in a
  bottom-side render. Labels composed in top-view order put the supply label beside
  the ground pin.
- Mark every pin that must not see a higher voltage where the cable goes on, not
  only in a legend elsewhere on the board.
- Shorten a label only where it would actually collide (a mounting hole), not for
  the whole connector; and note any row that lost information.
- Removing paste from an exposed pad that must not be soldered belongs in the same
  pass. It shows afterwards as one `lib_footprint_mismatch` warning, which is
  expected.
- This pass took the silkscreen warnings on that board from about 400 to 3, the rest
  being footprint graphics at the board edge.

Text of 0.8 mm height with 0.12 to 0.15 mm stroke is below what some fabs state as
their minimum (JLCPCB's page was read as 1.0 mm and 0.15 mm); decide per fab.

`scripts/audit_silkscreen.py --allow-hidden-regex '^(R|C|FB)\d'` audits such a board.

## 3D STEP Model Practice

- Release boards should use STEP models for all populated parts that affect mechanical fit: IC packages, passives, crystals, LEDs, jacks, terminals, headers, switches, and large jumpers.
- Mounting-hole footprints and graphical logos may remain model-less unless a spacer, screw, or enclosure part is intentionally represented.
- Prefer project-local model paths such as `${KIPRJMOD}/models/step/Part.step` once a board is ready to share; this keeps KiCad 3D viewer and CAD exports independent of the user's installed library version.
- If a footprint references an obsolete library model name, copy a current matching KiCad STEP model into the project and update the footprint model path deliberately.
- For connectors, search DigiKey, Mouser, and the manufacturer CAD library for the exact orderable part before approximating. Keep the downloaded source CAD archive beside the generated project-local STEP when licensing allows.
- Do not substitute a different connector family just because the pitch or part number is similar; if exact CAD is unavailable, generate a simple footprint-aligned STEP envelope and document it as an approximation.
- Vendor STEP files often use a mechanical CAD frame rather than the KiCad footprint frame. Measure pads, locating pegs, and insertion side against the official footprint; bake any required rotation/offset into the project-local STEP instead of relying on per-footprint transform guesses.
- Use AP214 STEP presentation entities for display colors when possible. Avoid WRL color workarounds for release assets because unit/scale assumptions can make connectors appear oversized in KiCad.
- Use `kicad-cli pcb export step --force --subst-models --output exports/step/BOARD.step BOARD.kicad_pcb` to generate a full-board assembly STEP after model paths are clean.
- When substituting a mechanically equivalent connector model, document the source or approximation in the project README or CAD notes.
- For parts with an LCSC number, `uvx easyeda2kicad --lcsc_id C12345 --3d --output DIR`
  fetches a STEP model, sending only that number. Five of five tried (RJ45, USB-C,
  microSD, tactile switch, VQFN) were usable; one needed an offset. Their
  redistribution terms were not established, so keep them out of the repository and
  commit a fetch script until that is settled.
- A footprint that names a model KiCad does not ship renders as bare pads. List
  footprints whose model file is missing before judging a 3D render.
- Parts marked do-not-populate are omitted from `kicad-cli pcb render`; render a copy
  with the attribute cleared to see them.

## Placement DRC Gate

Before routing, there should be no new:

- `courtyards_overlap`
- `copper_edge_clearance`
- `hole_clearance`
- `hole_to_hole`
- `pth_inside_courtyard`
- `npth_inside_courtyard`
- `silk_overlap`
- `silk_over_copper`
- `silk_edge_clearance`
