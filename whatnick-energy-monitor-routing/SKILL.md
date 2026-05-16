---
name: whatnick-energy-monitor-routing
description: Route and validate KiCad energy-monitor PCBs across breadboard-only, large analog-connector, PCI/riser, and FeatherWing form factors. Use for analog route priority, power net classes, GND planes, host/backplane connector fanout, Freerouting DSN/SES workflows, KiCad 10 routing APIs, route/zone cleanup, and DRC checks requiring zero errors and zero unconnected items.
compatibility: KiCad 10 Python and KiCad CLI; Freerouting examples assume a local Java runtime and freerouting.jar.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# Whatnick Energy Monitor Routing

Use this skill once placement is DRC-clean. Route analog, clock, power, and return paths deliberately, and make the router aware of power widths before autorouting.

## Routing Order

1. Confirm placement DRC is clean except expected unconnected items.
2. Route current and voltage input pairs through their filters with short, tidy paths.
3. Route reference, regulator-output, and decoupling connections with short loops.
4. Route clock/crystal nets short and away from SPI/CF/IRQ runs.
5. Route digital/debug signals after analog and clock corridors are stable.
6. Add or refill GND planes after critical routes are stable.
7. Run DRC and require zero errors and zero unconnected items.

## Rules Of Thumb

- Keep project `.kicad_pro` constraints aligned with the routed board; KiCad CLI DRC uses project constraints.
- Dense compact boards can route with 0.15 mm tracks, 0.15 mm clearance, 0.45 mm vias, and 0.20 mm drills.
- Bench boards should use a `Power` netclass for supply rails before DSN export; do not blindly post-widen dense routes.
- Use GND planes for return copper rather than widening every GND trace in dense analog areas.
- PCI/riser boards route the edge connector/backplane fanout first so power, analog, and host buses do not fight for the same neck-down region.
- FeatherWing boards route host headers and fixed bus pins early, then fit metering analog paths around the host outline.
- Treat references such as `REF` as precision nodes, not bulk power rails, unless the design requires otherwise.

See `references/routing-reference.md` for Freerouting and validation commands. Scripts in `scripts/` are portable utilities for common route cleanup and post-route plane tasks.
