# PCB Size And Shape Reference

This reference captures whatnick energy-monitor KiCad board families present in the workspace. Do not use unrelated hardware or software repos as design evidence.

## Workspace Form Factors

| Form factor | Workspace examples | Mechanical intent |
|-------------|--------------------|-------------------|
| Large analog-connector boards | `ADE9000_Breakout`, `ATM90E36_Breakout_KiCAD` | Bench/probing boards with CT/stereo jacks, voltage screw terminals or robust analog connectors, grouped digital headers, mounting holes, and room for labels. |
| Breadboard-only breakouts | `V93XX_Breakout`, `V9261F_Breakout`, `MCP39F511_Breakout`, `MCP39F521_Breakout`, `MCP39xx_Breakout`, `CS5464_Breakout`, `CS5490_Breakout`, `ade7763_breakout_kicad`, `ADE7816_Breakout`, `atm90e26_breakout_kicad` | Small modules exposing power, analog, and debug on 0.1 inch headers plus bottom-side test pads. |
| PCI/riser DIN-rail modules | `din_meter_atm90e26`, `din_meter_atm90e36` | Carrier/backplane modules where a PCI-X1 or similar lower edge connector defines power, analog, and host interfaces. |
| FeatherWings | `ATM90E26_Featherwing_KiCAD` | Feather-compatible outline and header spacing for stacking onto a host MCU board. |

## Breadboard-Only Compact Boards

- V93XX-style boards are about 38.2 mm x 28.04 mm.
- Compact ADE9000 JST revisions used about 38.1 mm x 38.0 mm.
- Keep headers on edges and test pads on the bottom side when front-side space is tight.
- Put logos and attribution on B.SilkS after routing space is known.
- Prefer a single 1x10 or similar 0.1 inch header when it can expose the useful power/analog/debug pins.
- Use bottom-side test pads for secondary signals rather than enlarging the board only for rarely used pins.
- Keep the board narrow enough for breadboard use when that is the point of the design.

## Large Analog-Connector Boards

- ATM-style boards use more area to improve connector access, probing, and routing clarity.
- Use stereo jacks or similarly robust connectors for current clamps.
- Use screw terminals for voltage inputs.
- Put grouped digital/debug access on a side header.
- ADE9000 ATM-style reference: 65 mm x 55 mm, rounded corners, four M2 holes, current jacks, voltage screw terminals, digital header, and GND planes.
- Keep analog connector groups aligned by channel so cable wiring reads from the board edge.
- Use mounting holes and rounded corners because these boards are handled as bench instruments.
- Leave label area near field connectors; connector readability is part of the mechanical design.

## PCI/Riser DIN-Rail Modules

- Treat the PCI-X1 or backplane connector as the primary mechanical datum.
- Preserve edge-connector keepouts, insertion depth, and any notches before placing measurement circuitry.
- Put host-facing buses and shared power on the backplane edge; do not duplicate them with ad hoc side headers unless the board needs standalone debug.
- Fit the board to the enclosure/module width first, then place metering ICs and conditioning networks around the fixed connector.
- Use jumpers or bottom-side configuration pads for mode options when top-side connector density is high.

## FeatherWing Boards

- Preserve Feather outline, mounting holes, and two long-edge header positions before placing metering parts.
- Keep host bus pins on the Feather headers; only add extra connectors for voltage/current sampling and configuration jumpers.
- Avoid tall analog connectors that collide with stacked Feather boards unless the design is explicitly non-stacking.
- Put mode-selection jumpers on the underside when top-side user wiring and Feather compatibility compete.

## Form-Factor Selection Heuristics

- Choose breadboard-only when the board is mainly an IC breakout or driver-development aid.
- Choose large analog-connector when sensor wiring and probing are more important than compactness.
- Choose PCI/riser when the board is part of a DIN-rail/backplane system and shares power or analog buses with a carrier.
- Choose FeatherWing when the host MCU ecosystem and stacking pinout are fixed requirements.
- If a design needs both field wiring and host stacking, decide which interface is mechanically primary before drawing the outline.

## Mechanical DRC Gate

After size, outline, hole, or connector changes, DRC must not introduce:

- `copper_edge_clearance`
- `hole_clearance`
- `hole_to_hole`
- `npth_inside_courtyard`
- `pth_inside_courtyard`
- `courtyards_overlap`
- `silk_edge_clearance`
- `silk_overlap`
- `silk_over_copper`
