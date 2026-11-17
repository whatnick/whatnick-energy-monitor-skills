---
name: whatnick-energy-monitor-circuit-design
description: Design and review KiCad schematics for energy-monitor boards using ADE9000, ATM90E36, V9360, V9381, V9261F, MCP39xx, ADE7763, ADE7816, CS5464, CS5490, or similar metering ICs. Use for datasheet reference circuits, analog input conditioning, clamp burden choices, power/reference/clock support, form-factor connector policy, host/backplane interfaces, and ERC-safe KiCad connectivity.
compatibility: KiCad 10 workflows; examples assume Windows PowerShell and KiCad CLI/Python are available.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# Whatnick Energy Monitor Circuit Design

Use this skill for electrical design before PCB placement or routing. Start with the target IC datasheet reference circuit, then adapt connectors and conditioning to the intended board format.

## Workflow

1. Identify the exact IC, package, exposed pad naming, and datasheet reference/test circuit.
2. Preserve project-local symbols and footprints for metering ICs; do not swap in guessed global-library parts.
3. Inspect actual KiCad symbol pin locations before wiring. Never infer pin order from package drawings or visual intuition.
4. Implement support blocks: supply input, regulator/reference decoupling, anti-alias filters, reset, crystal/oscillator, mode straps, and no-connects.
5. Choose connector exposure for the form factor: breadboard headers/test pads, JST debug, large-board jacks/screw terminals/grouped digital header, PCI/backplane edge connector, or FeatherWing host headers.
6. Use physical KiCad connectivity: pin endpoint -> short wire stub -> net label. Prefer exact endpoint tools such as `connect_to_net` when available.
7. Run ERC after every bulk wiring pass and require zero ERC errors.

## Key Rules

- IC-side filtered nets use IC signal names such as `IAP`, `IAN`, `VAP`, and `VAN`.
- Connector-side nets use a suffix such as `_J`, `_IN`, or the local project convention when a series part separates them from IC pins.
- Keep burden, multiplier, divider, and anti-alias components visually distinct in the schematic.
- Add `PWR_FLAG` symbols only where ERC needs proof that a supply is driven.
- Add no-connect markers only to datasheet-confirmed unused pins.
- Treat `endpoint_off_grid` as grid hygiene; do not undo proven physical connectivity to silence it.
- A stock symbol for a similar part is not a symbol for your part. Compare every pin
  number and name with the datasheet for the exact part and package before using
  it; one pin that is ground on the older part and a control input on the newer one
  is enough to change the circuit.
- Choose the footprint by the maker's package code where the stock library has it,
  and check the exposed-pad size as well as the pitch.
- Do not rely on memory for a pin number, strap level or component value. Read it
  from the document and note which document and revision.
- For every pin wired to a node that depends on a weak internal pull (reset, boot,
  enable), check what each connected device does to that node in its own reset state.
- ERC clean means the drawing is consistent. Have the circuit reviewed against the
  datasheets by someone who did not draw it before layout starts; see the
  design-review skill.

See `references/circuit-patterns.md` for reusable analog, power, clock, and debug patterns.
For schematics emitted by a script instead of drawn, see the schematic-generation skill.
