---
name: stpm33-breakout
description: Apply STPM33_Breakout-specific reconstruction knowledge for the one-voltage, two-current STPM33 variant. Use for the validated 55 x 40 mm KiCad scaffold, QFN-32 pin mapping, phase/neutral and tamper-oriented channel planning, analog-front-end derivation, component marking, render review, and tool-neutral ECAD/MCAD reconstruction. Layer this overlay on stpm3x-breakout and the reusable Whatnick energy-monitor skills.
compatibility: KiCad 10 project overlay for the STPM33 scaffold in whatnick/STPM3x_Breakout; principles are ECAD/MCAD neutral.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# STPM33 Breakout Project Overlay

Load this overlay for STPM33-specific work in `whatnick/STPM3x_Breakout`.
Load `stpm3x-breakout` first for the shared STPM family constraints, then use
the reusable circuit, layout, routing, size/shape, and BOM skills.

## Current Maturity

- The committed STPM33 design is a validated mechanical and library scaffold.
- The analog front end, connectors, support circuit, schematic connectivity,
  placement, and routing are not yet implemented.
- Do not describe the scaffold as electrically complete or production-ready.
- Current PCB validation is zero DRC violations and zero unconnected items
  because the scaffold has no implemented electrical nets.

## Variant Facts

- Channels: one differential voltage channel and two differential current
  channels.
- Intended uses: phase/neutral monitoring, tamper experiments, or two current
  sensors sharing one voltage channel.
- Package: QFN-32 with exposed pad, 5 x 5 mm body, 0.5 mm pitch, and nominal
  3.45 x 3.45 mm exposed pad.
- Scaffold footprint:
  `Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm`.
- Envelope: 55 x 40 mm with 5.08 mm rounded corners.
- Mounting: four M2 NPTH holes with 2.2 mm drills.
- Analog field/sensor region is reserved on the left; power and digital I/O
  are reserved on the right.
- The exposed-pad net and thermal-via construction remain explicit
  design-review items. Do not infer them from the package name.

## Verified Pin Contract

| Pins | Function |
|---|---|
| 1-8 | CLKOUT/ZCR, CLKIN/XTAL2, XTAL1, LED1, LED2, INT1, INT2, EN |
| 9-10 | VIP1, VIN1 |
| 11-12 | IIP1, IIN1 |
| 13-14 | IIN2, IIP2 |
| 15-16 | NC |
| 17-23 | VREF1, GND_REF, VREF2, GNDA, VDDA, GND_REG, VCC |
| 24-25 | NC |
| 26-27 | GNDD, VDDD |
| 28-32 | SYN, SCS, SCL, MOSI/RXD, MISO/TXD |

Preserve the current-channel polarity order exactly: channel two is `IIN2` on
pin 13 and `IIP2` on pin 14. Mark every NC pin explicitly in the schematic.

## Electrical Design Gates

- Nominal supply is 3.3 V within the device's 2.95 V to 3.65 V range.
- Provide the shared STPM decoupling, reference, 16 MHz clock, enable/reset,
  interface-selection, and digital-access circuits from `stpm3x-breakout`.
- Keep both current signal chains physically and electrically distinguishable.
- Derive each burden, divider, protection network, PGA setting, and
  anti-alias filter from the selected sensor and measurement range.
- Keep differential analog input magnitude within the datasheet limits.
- Preserve the readable signal path:
  `field connector -> burden/divider/protection -> anti-alias network -> IC`.
- Use connector-side suffixes such as `_J` and IC-side names such as `VIP1`,
  `VIN1`, `IIP1`, `IIN1`, `IIP2`, and `IIN2`.
- Do not connect hazardous voltage directly without a reviewed isolation and
  protection design.

## Reconstruction Sequence

1. Recreate the 55 x 40 mm rounded outline and four mounting-hole datums.
2. Instantiate the verified project-local STPM33 symbol and QFN-32 footprint.
3. Assign the exposed pad only after electrical and assembly review.
4. Define the voltage source and both current sensors, ranges, isolation, and
   connector contracts.
5. Derive both current channels independently even when their nominal
   component values match.
6. Add the shared supply, references, clock, reset, interface-selection, and
   digital-access blocks.
7. Place field connectors and analog conditioning in the left region, U1 and
   support parts centrally, and power/digital access in the right region.
8. Route precision analog and clock nets before power and digital nets, then
   implement the reviewed ground-domain strategy.
9. Add functional connector labels, safety text, identity, revision, date,
   Whatnick logo, and OSHW logo.
10. Validate ERC, DRC, unconnected count, dimensions, pin mapping, channel
    polarity, and top/bottom render readability.

The KiCad scaffold generator is an implementation aid, not the design
definition:

```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" .\scripts\generate_scaffold.py
```

When translating to another ECAD or MCAD tool, preserve the electrical pin
contract, board and mounting datums, package geometry, functional zones,
channel identity, marking geometry, and validation gates.

## Marking And Render Review

- Visible fitted component and test-pad references use 0.8 x 0.8 mm text with
  0.2 mm stroke on the component-side silkscreen.
- Keep mounting-hole, tooling-hole, drill-only, and fiducial references hidden.
- Derive connector signal labels from the electrical pin map, not rendered
  left-to-right order.
- Keep values on fabrication layers rather than production silkscreen.
- Include explicit isolation/direct-mains safety text matching the implemented
  input architecture.
- Inspect both top and bottom renders for readable references, signal labels,
  board identity, safety markings, and logo orientation before release.

## Validation

```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --output stpm33-drc.rpt .\hardware\STPM33_Breakout\STPM33_Breakout.kicad_pcb
```

The present scaffold passes with zero DRC violations and zero unconnected
items. Once circuitry is implemented, require zero ERC violations, zero DRC
violations, and zero unconnected items before release.
