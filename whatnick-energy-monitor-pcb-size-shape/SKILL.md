---
name: whatnick-energy-monitor-pcb-size-shape
description: Choose board size, outline shape, mounting holes, connector edge allocation, rounded corners, and form factor for KiCad energy-monitor PCBs. Use for large analog-connector boards, breadboard-only breakouts, PCI/riser DIN-rail modules, FeatherWings, V93XX compact boards, MCP3909 rounded-corner style, ADE9000/ATM-style envelopes, and mechanical DRC constraints.
compatibility: KiCad 10 workflows; optional mechanical scripts use KiCad Python.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# Whatnick Energy Monitor PCB Size And Shape

Use this skill when choosing the board envelope, rounded corners, mounting holes, connector edge plan, or board family.

## Form-Factor Choice

- Breadboard-only breakout: use when the board should plug into or wire like a 0.1 inch module, with one or two pin headers and bottom-side test pads.
- Compact debug board: use when SPI/debug needs a cable connector but the board should remain small.
- Large analog-connector board: use when the board needs CT/stereo jacks, screw terminals, grouped digital header access, and comfortable probing.
- PCI/riser module: use when the board plugs into a backplane, DIN-rail carrier, or PCI-style edge connector and inherits host power/analog/digital routing from that connector.
- FeatherWing: use when the host is an Adafruit Feather-compatible MCU board and long-edge Feather headers define the mechanical envelope.
- Do not force a compact outline when connectors or filters cause bad routing, inaccessible labels, or fragile probing.

## Mechanical Rules

- Use rounded corners when the board will be handled as a bench module.
- The established rounded-corner visual pattern uses about 5.08 mm radius.
- Use four M2 NPTH holes when board space allows.
- M2 holes should be no-net NPTH circular pads with 2.2 mm drill and 2.2 mm pad size, excluded from BOM and position files.
- Keep holes outside component courtyards and away from copper, zones, silkscreen, and connector keepouts.
- Put field wiring connectors where cables naturally leave the board.
- Reserve clean routing corridors between connector groups and IC pin banks.

See `references/size-shape-reference.md` for workspace examples and form-factor-specific rules. Use `scripts/apply_board_dimensions.py` as a starting point for visible board-edge measurements.
