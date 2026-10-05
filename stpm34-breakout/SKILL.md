---
name: stpm34-breakout
description: Apply STPM34_Breakout-specific reconstruction knowledge for the two-voltage, two-current STPM34 variant. Use for the validated 55 x 40 mm KiCad scaffold, QFN-32 pin mapping, dual-circuit and split-phase channel planning, analog-front-end derivation, component marking, render review, and tool-neutral ECAD/MCAD reconstruction. Layer this overlay on stpm3x-breakout and the reusable Whatnick energy-monitor skills.
compatibility: KiCad 10 project overlay for the STPM34 scaffold in whatnick/STPM3x_Breakout; principles are ECAD/MCAD neutral.
metadata:
  org: whatnick
  domain: energy-monitor-pcb
---

# STPM34 Breakout Project Overlay

Load this overlay for STPM34-specific work in `whatnick/STPM3x_Breakout`.
Load `stpm3x-breakout` first for the shared STPM family constraints, then use
the reusable circuit, layout, routing, size/shape, and BOM skills.

## Current Maturity

- The committed STPM34 design is a validated mechanical and library scaffold.
- The analog front end, connectors, support circuit, schematic connectivity,
  placement, and routing are not yet implemented.
- Do not describe the scaffold as electrically complete or production-ready.
- Current PCB validation is zero DRC violations and zero unconnected items
  because the scaffold has no implemented electrical nets.

## Variant Facts

- Channels: two differential voltage channels and two differential current
  channels.
- Intended uses: dual-circuit, split-phase, or two-phase monitoring and
  metrology development.
- STPM34 is not a complete three-phase meter by itself.
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
| 15-16 | VIN2, VIP2 |
| 17-23 | VREF1, GND_REF, VREF2, GNDA, VDDA, GND_REG, VCC |
| 24 | NC |
| 25-27 | GNDD, GNDD, VDDD |
| 28-32 | SYN, SCS, SCL, MOSI/RXD, MISO/TXD |

Preserve the non-intuitive polarity ordering: current channel two is `IIN2`
then `IIP2`, while voltage channel two is `VIN2` then `VIP2`. Mark pin 24 as
NC and preserve both GNDD pins.

## Electrical Design Gates

- Nominal supply is 3.3 V within the device's 2.95 V to 3.65 V range.
- Provide the shared STPM decoupling, dual-reference, 16 MHz clock,
  enable/reset, interface-selection, and digital-access circuits from
  `stpm3x-breakout`.
- Keep both voltage/current channel pairs physically and electrically
  distinguishable throughout schematic, layout, firmware mapping, and labels.
- Derive every burden, divider, protection network, PGA setting, and
  anti-alias filter from its selected source, sensor, and measurement range.
- Keep differential analog input magnitude within the datasheet limits.
- Preserve each readable signal path:
  `field connector -> burden/divider/protection -> anti-alias network -> IC`.
- Use connector-side suffixes such as `_J` and exact IC-side channel names.
- For split-phase use, document the assumed neutral/reference topology and
  verify isolation and common-mode limits.
- Do not connect hazardous voltage directly without a reviewed isolation and
  protection design.

## Reconstruction Sequence

1. Recreate the 55 x 40 mm rounded outline and four mounting-hole datums.
2. Instantiate the verified project-local STPM34 symbol and QFN-32 footprint.
3. Assign the exposed pad only after electrical and assembly review.
4. Define both voltage sources and both current sensors, ranges, isolation,
   phase/channel mapping, and connector contracts.
5. Derive all four analog signal chains independently even when nominal
   component values match.
6. Add the shared supply, both references, clock, reset, interface-selection,
   and digital-access blocks.
7. Place field connectors and analog conditioning in the left region, U1 and
   support parts centrally, and power/digital access in the right region.
8. Route precision analog and clock nets before power and digital nets, then
   implement the reviewed ground-domain strategy.
9. Add unambiguous channel labels, safety text, identity, revision, date,
   Whatnick logo, and OSHW logo.
10. Validate ERC, DRC, unconnected count, dimensions, pin mapping, channel
    polarity, phase association, and top/bottom render readability.

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
- Make voltage/current channel and phase/circuit association unambiguous.
- Keep values on fabrication layers rather than production silkscreen.
- Include explicit isolation/direct-mains safety text matching the implemented
  input architecture.
- Inspect both top and bottom renders for readable references, signal labels,
  board identity, safety markings, and logo orientation before release.

## Validation

```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --output stpm34-drc.rpt .\hardware\STPM34_Breakout\STPM34_Breakout.kicad_pcb
```

The present scaffold passes with zero DRC violations and zero unconnected
items. Once circuitry is implemented, require zero ERC violations, zero DRC
violations, and zero unconnected items before release.
