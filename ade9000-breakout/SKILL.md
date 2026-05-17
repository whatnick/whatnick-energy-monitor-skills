---
name: ade9000-breakout
description: Apply ADE9000_Breakout-specific KiCad knowledge. Use for ADE9000 Figure 55 schematic work, ATM-style board topology, YHDC clamp burdens, project-local scripts, KiCad 10 validation/export commands, GND planes, Power netclass routing, project-local STEP models, and known MCP/KiCad pitfalls. Layer this overlay on the reusable whatnick energy-monitor skills.
compatibility: KiCad 10 project overlay for the ADE9000_Breakout repository.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# ADE9000 Breakout Project Overlay

Load this overlay for ADE9000_Breakout-specific work. Use it together with the reusable circuit, layout, routing, and size/shape skills.

## Current Board Facts

- Current board style: ATM90E36-style ADE9000 bench breakout.
- Envelope: 65 mm x 55 mm rounded board with four M2 NPTH holes.
- Inputs: stereo current jacks, voltage screw terminals, YHDC current-output clamp burden support.
- Debug: grouped 0.1 inch digital/debug header on one side.
- Routing: F.Cu/B.Cu GND planes and a `Power` netclass for `+3V3`, `AVDDOUT`, and `DVDDOUT`.
- License marking: back silkscreen includes `TAPR OHL`.
- 3D CAD: populated parts use project-local STEP models under `models/step/`; full assembly export lives at `exports/step/ADE9000_Breakout.step`.

## Circuit Facts

- Follow ADE9000 datasheet Figure 55 unless the user explicitly changes topology.
- `ADE9000_Breakout.kicad_sym` is authoritative for custom symbol geometry.
- ADE9000 exposed pad pin number is `EP`.
- Anti-alias filters use 1 k series and 22 nF shunt capacitors on analog inputs.
- VDD, AVDDOUT, DVDDOUT, and REF need local decoupling near U1.
- Clock uses a 24.576 MHz crystal with load capacitors unless using an external clock.
- PM0/PM1 are grounded for normal operating mode.
- R17-R20 are 2.4R 0402 burden/multiplier resistors across jack-side current pairs.

## Validation

STEP export:

```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export step --force --subst-models --output exports\step\ADE9000_Breakout.step .\ADE9000_Breakout.kicad_pcb
```

ERC/DRC:

```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --format json --output erc.json .\ADE9000_Breakout.kicad_sch
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --format json --output drc.json .\ADE9000_Breakout.kicad_pcb
```

Expected final PCB state: zero DRC errors and zero unconnected items. Existing non-error warnings must be understood before shipping.
