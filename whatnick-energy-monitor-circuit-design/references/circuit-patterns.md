# Circuit Patterns

## Datasheet-First Blocks

- Supply decoupling on every supply, regulator output, and reference pin.
- Anti-alias filters on voltage and current inputs, with values taken from the target datasheet or validated reference design.
- Reset pull-up/RC or supervisor network where required.
- Crystal, oscillator, or external clock network with load capacitors and routing expectations captured in the schematic.
- Mode pins strapped explicitly and named in a way that shows normal/test modes.

## Analog Inputs

- Keep each differential or pseudo-differential pair inspectable from connector to IC pin.
- ADE9000 Figure 55 pattern: 1 k series and 22 nF shunt anti-alias filters on analog inputs; decouple VDD, AVDDOUT, DVDDOUT, and REF.
- V93XX compact pattern: small series resistors and shunt capacitors near the monitor IC; preserve datasheet-specific values.
- ATM-style clamp boards: current inputs enter through CT jacks and voltage inputs through screw terminals, then pass through conditioning networks sized for the measurement range.

## Current Clamps

- For YHDC or similar current-output clamps, add burden/multiplier resistors across each jack-side current pair.
- Keep burdens near the connector and before IC-side anti-alias filters.
- Use explicit pair nets such as `IAP_J`/`IAN_J`, `IBP_J`/`IBN_J`, `ICP_J`/`ICN_J`, and `INP_J`/`INN_J`.

## Digital Debug Exposure

- Compact boards: expose low-use CF/IRQ/reset/clock signals as named test pads.
- Cable-debug boards: use a JST/debug connector for SPI plus power/GND.
- Bench boards: aggregate all digital/debug signals on a breadboard-friendly side header.

## Connector Exposure By Form Factor

- Large analog-connector boards: put current clamp inputs on jacks or robust field connectors, voltage inputs on screw terminals or equivalent field wiring, and all digital/debug signals on one grouped side header.
- Breadboard-only breakouts: expose the most useful power, analog, and host-interface pins on a 0.1 inch header; keep low-use status, IRQ, clock, and reset signals on named test pads.
- PCI/riser modules: define the edge/backplane connector in the schematic as the primary interface for power, host bus, and analog signals; keep jumpers for mode selection explicit.
- FeatherWings: route UART/SPI/I2C and power through the Feather header symbols, and expose metering-mode or host-protocol choices as solder jumpers when the IC supports multiple interfaces.

## Multi-Channel Metering Patterns

- Repeat current/voltage channel conditioning in visually aligned schematic rows so the PCB can become channel lanes.
- Name connector-side nets by channel and connector role before the anti-alias/filter parts.
- Keep burden/multiplier, divider, and anti-alias blocks separate even when their values are small; this prevents later layout mistakes.
- For backplane or Feather host boards, distinguish host-interface voltage domains from metering analog/reference domains in net names and symbols.

## Clock And Oscillator Margin

- Load capacitors: `CL = (C1 * C2) / (C1 + C2) + stray`, with 2 to 5 pF of stray per
  board. Size them for the crystal's rated load, not by copying another design whose
  crystal is unknown.
- Check start-up margin by calculation: `gm_crit = 4 * ESR * (2 * pi * f)^2 * (C0 + CL)^2`
  against the IC's published oscillator transconductance for the drive setting the
  firmware will use. A 12.5 pF, 70 kOhm 32.768 kHz crystal can need a microcontroller's
  highest drive setting where a 7 pF part does not.
- Where the IC vendor names a reference crystal and warns against deviating, a
  crystal with higher ESR or load capacitance is a design change that needs the
  calculation or a bench test, not a sourcing substitution.

## Interfaces To Another Powered Board

- Decide, for each line, what the other board sees in three states: this board off,
  this board's controller in reset, and the cable half connected. Add the pulls that
  make each state harmless.
- A reference rail supplied by the other board through the connector needs a bleed
  resistor, so it does not float when nothing is plugged in.
- Use direction-fixed translators for push-pull control and clock lines. Keep
  auto-direction parts for genuinely bidirectional open-drain buses.
- Any switch or jumper on a line that something can drive gets a series resistor.
