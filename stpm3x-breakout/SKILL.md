---
name: stpm3x-breakout
description: Apply STPM3x_Breakout-specific reconstruction knowledge for the STPM32 compact board and STPM33/STPM34 family scaffolds. Use for the isolated 9 VAC and 100 A:50 mA CT front end, breadboard header and test-pad pin maps, STPM support circuitry, analog/digital ground strategy, production silkscreen, project-local generation scripts, KiCad validation, and tool-neutral ECAD/MCAD reconstruction.
compatibility: KiCad 10 project overlay for the STPM3x_Breakout repository; principles are ECAD/MCAD neutral.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# STPM3x Breakout Project Overlay

Load this overlay for `whatnick/STPM3x_Breakout`. Use it together with the
reusable circuit, layout, routing, size/shape, and BOM skills.

## STPM32 Board Facts

- Envelope: 38.2 x 28.04 mm rounded compact breakout.
- Connector: one long-edge 1x12, 2.54 mm breadboard header.
- No screw terminals, audio jacks, or direct-mains connector.
- Secondary signals use four bottom-side test pads.
- Metering IC: STPM32 in VQFN-24-1EP, 4 x 4 mm, 0.5 mm pitch.
- Analog ground, reference ground, and digital ground join only through the
  three-pad net tie.
- Routed board uses F.Cu AGND and B.Cu DGND pours.
- Project-local symbols live in `symbols/STPM3x.kicad_sym`.
- Project-local Whatnick and OSHW vector footprints live in
  `hardware/STPM32_Breakout/logos.pretty`.

## Header And Test-Pad Contract

| Pin | Signal | Pin | Signal |
|---:|---|---:|---|
| 1 | +3V3 | 7 | SCS |
| 2 | DGND | 8 | SCL |
| 3 | VAC_P | 9 | MOSI/RXD |
| 4 | VAC_N | 10 | MISO/TXD |
| 5 | CT_P | 11 | SYN |
| 6 | CT_N | 12 | EN |

Bottom test pads:

- TP1: INT1
- TP2: LED1
- TP3: LED2
- TP4: CLKOUT/ZCR

Treat this table as the electrical source of truth when mirroring views or
translating to another ECAD system. Do not infer pin meaning from rendered
left-to-right order.

## Analog Front End

- Current sensor: 100 A:50 mA current-output CT.
- Differential burden: 2.4 ohm, giving 120 mV RMS at 100 A.
- Current filter: 100 ohm series and 330 nF shunt per leg, approximately
  4.8 kHz.
- Voltage source: isolated 9 VAC transformer secondary only.
- Symmetric voltage divider: 200 kohm / 2.49 kohm per conductor,
  approximately 81.3:1 differential scaling.
- Voltage filter: 1 kohm series and 33 nF shunt per leg, approximately 4.8 kHz.
- Expected STPM32 voltage input at 9 VAC: approximately 111 mV RMS and
  157 mV peak.
- Never connect J1 directly to mains.

## Support Circuit Contract

- Nominal supply: 3.3 V.
- VCC: 1 uF to DGND.
- VDDA: 1 uF to AGND.
- VDDD: 4.7 uF to DGND.
- VREF1: 100 nF to GND_REF.
- Clock: 16 MHz crystal with 15 pF load capacitors.
- EN has a 10 kohm pull-up and reset switch to DGND.
- SCS has a 10 kohm pull-down for SPI default; hold high before reset for UART.

## Production Silkscreen

- Every fitted electrical component and test pad has a visible reference.
- Component and signal markers are 0.8 x 0.8 mm with 0.2 mm stroke.
- Header signals are marked from the electrical pin map.
- Test pads carry both `TPx` and functional signal labels.
- Whatnick logo is on F.SilkS; OSHW logo is on B.SilkS.
- B.SilkS carries revision, build date, TAPR OHL notice, isolated-source note,
  and direct-mains prohibition.
- Do not mark mounting holes, tooling holes, or drill-only features.
- Apply the reproducible layout with
  `scripts/apply_stpm32_silkscreen.py`.

## Reconstruction Order

Rebuild from invariants rather than serialized editor objects:

1. Create the board outline and long-edge header datum.
2. Apply the header/test-pad electrical pin contract.
3. Build the STPM32 support circuit and the two analog conditioning chains.
4. Place U1, analog lanes, clock, decoupling, reset, header, and test pads from
   functional adjacency.
5. Route precision analog and clock nets first, then power and digital nets.
6. Add AGND/DGND pours and preserve the explicit three-domain net tie.
7. Apply component, signal, identity, logo, safety, revision, and date markers.
8. Validate ERC, DRC, unconnected count, dimensions, and rendered access-side
   readability.

KiCad-specific generators are implementation aids, not the design definition:

- `scripts/build_stpm32_schematic.py`
- `scripts/build_stpm32_pcb.py`
- `scripts/apply_stpm32_silkscreen.py`

For another ECAD/MCAD system, preserve the electrical pin map, component
adjacency, board/header datums, copper-domain boundaries, text geometry,
artwork dimensions, and validation gates.

## Validation

```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --output erc.rpt .\hardware\STPM32_Breakout\STPM32_Breakout.kicad_sch
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --output drc.rpt .\hardware\STPM32_Breakout\STPM32_Breakout.kicad_pcb
```

Expected state: zero ERC violations, zero DRC violations, and zero unconnected
items.
