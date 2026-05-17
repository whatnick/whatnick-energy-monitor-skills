---
name: whatnick-energy-monitor-layout-design
description: Place components on KiCad energy-monitor PCBs for analog accuracy, testability, host compatibility, 3D CAD fit, and routing success. Use for connector grouping across large analog-connector boards, breadboard-only breakouts, PCI/riser modules, and FeatherWings, plus analog/digital partitioning, decoupling placement, project-local STEP models, reference designators, silkscreen markings, and KiCad Python placement workflows.
compatibility: KiCad 10 workflows; optional scripts use KiCad Python.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# Whatnick Energy Monitor Layout Design

Use this skill after the circuit is defined and before routing. The board should be easy to wire, easy to probe, and friendly to the autorouter while keeping analog paths short and readable.

## Placement Workflow

1. Place the monitor IC first, usually near center, with pin banks facing their related circuits.
2. Put analog conditioning between the field connector and the IC pin it serves.
3. Place current inputs, voltage inputs, power/debug connectors, host connectors, and digital headers on board edges with readable pin order.
4. Keep clock parts close to clock pins and away from long digital traces.
5. Place decoupling capacitors tight to supply/reference pins with short GND returns.
6. Put burden/multiplier resistors near current-input connectors before anti-alias filter rows.
7. Move references to matching silkscreen layers and keep values on Fab layers.
8. Assign or vendor STEP models for all populated parts that affect enclosure, connector, or assembly fit.
9. Run placement DRC before routing.

## Layout Rules

- Separate analog connector/filter regions from digital/debug routing corridors.
- Larger bench boards should use their area to reduce congestion and improve readability, not to scatter circuit blocks.
- Compact boards can use bottom-side test pads to reduce front-side crowding.
- PCI/riser boards must treat the edge connector or backplane connector as the mechanical anchor.
- FeatherWings must preserve the host header outline and keep user-facing analog connectors clear of the Feather stacking area.
- Keep every component, connector, and test-pad reference visible unless it is a mounting hole.
- Hide mounting-hole references and values.
- Prefer project-local `${KIPRJMOD}/models/step/...` STEP paths for release-ready boards so CAD export is portable.
- Add board identity, attribution, license notice, and OSHW logo after electrical/mechanical placement is stable.

See `references/layout-reference.md` for board-family patterns and DRC gates. Use `scripts/move_refs_to_silkscreen.py` as a portable starting point for reference-field cleanup.
