# Layout Reference

## Connector Patterns

- Compact V93XX style: one 0.1 inch header and bottom-side test pads on a small rounded board.
- Compact ADE9000 JST style: JST-SH for power/SPI, analog headers for measurement pairs, bottom-edge test pads for CF/IRQ/clock/reset.
- ATM-style bench style: stereo jacks for current clamps, screw terminals for voltage inputs, grouped 0.1 inch digital/debug header along one side.
- Breadboard-only style: put the main 0.1 inch header on a long edge, keep IC support parts near the IC, and push low-use debug signals to bottom-side test pads.
- PCI/riser style: place the edge/backplane connector first, then place ICs so analog and host buses fan out from that fixed datum without crossing.
- FeatherWing style: lock the Feather headers and outline first, then place measurement connectors and mode jumpers where they do not break stacking or USB/battery access.

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

## Decoupling Placement

- Place each capacitor adjacent to its associated pin, not in a remote capacitor cluster.
- Pair AVDDOUT, DVDDOUT, and REF capacitors with nearby GND access.
- Keep reset and clock support parts near their IC pins unless connector access requires a clear exception.

## Silkscreen And References

- Reference designators live on the matching silkscreen layer: `F.SilkS` for front-side footprints and `B.SilkS` for back-side footprints.
- Values stay on Fab layers.
- Use compact labels around 0.8 mm high with 0.2 mm stroke when DRC allows.
- Do not leave new silkscreen over pads, mask openings, or board edges.

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
