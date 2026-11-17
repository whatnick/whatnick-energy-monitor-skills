# What independent reviews found

Faults found by fresh reviewers on one MCU board (LQFP-144 MCU, 10/100 Ethernet PHY,
USB debug probe MCU, level-shifted headers to another machine, buck regulator) after
ERC, DRC, schematic parity and a netlist-against-intent comparison were all clean.
Each is written as the general lesson; use them as checklist items and brief
questions. "Verified" figures are the reviewer's, from the datasheet section cited
in their report.

## Schematic

### Two parts fighting over one node

- **Reset pin held mid-rail.** A second MCU's GPIO was wired straight to the main
  MCU's reset pin to act as an open-drain reset driver. That GPIO powers up with its
  pad pull-down enabled (50 to 80 k); the reset pin's internal pull-up is 30 to
  50 k. The node sits at 1.65 to 2.4 V, across the logic-high threshold, from
  power-up until the second MCU's firmware configures the pin. Two reviewers found
  it independently. Fix: an external pull-up strong enough to win (4.7 k), and a
  series resistor so a button cannot short a driven pin.
  *Check the reset-state pull of every pin you connect to a node that relies on a
  weak internal pull.*
- **A switch that can short a driver.** A simulation DIP switch tied a line straight
  to the supply while a translator output could drive the same line low. Rule adopted:
  a switch on a shared line always has a series resistor (1 k).
- **Direction-selectable lines.** Where a switch sets a translator's direction, the
  wrong setting puts two push-pull outputs against each other (27 to 60 mA estimated,
  above the MCU's 25 mA pin limit). 470 ohm in series on both sides of the translator
  keeps contention under 7 mA.

### Level translators and unpowered or undriven sides

- **Auto-direction translators are the wrong part for control lines.** A
  TXS0108E-class part has pull-ups on every line, cannot hold a line low while its
  input floats, has DC drive of hundreds of microamps, needs VCCA at or below VCCB at
  all times and has no partial-power-down specification. A power-enable output through
  one reads as asserted at the far end whenever the MCU is in reset. An LED on such a
  line drags it to an invalid level. Use direction-fixed translators for anything
  that is not open-drain.
- **The stock symbol for a near-equivalent part may be wrong for yours.** KiCad's
  SN74AVC8T245 symbol has pin 11 as ground; on the SN74AXC8T245 that pin is DIR2.
  Used as-is the symbol forces all eight bits one way. On that part DIR2 does not set
  the direction of bits 5 to 8 independently; it inverts them relative to DIR1. Read
  the function table.
- **Supply range for mixed directions.** The same part supports simultaneous up and
  down translation only with both supplies at 1.40 V or more.
- **A reference rail supplied through a connector floats when the connector is
  empty.** With only a decoupling capacitor on it, leakage can charge the rail into
  the region where the translator's isolation is no longer guaranteed. Fit a bleed
  resistor (10 k) on every such rail. A PCA9306's 200 k bias will charge an open
  low-side reference to about 2.7 V and present that on the bus pins.
- **Translator inputs float while the MCU is in reset.** MCU pins are high-impedance
  in and after reset, so the far side sees garbage on clock, reset and serial lines.
  Pull every MCU-driven translator input to its idle level (clock low, reset
  inactive, serial transmit high).
- **Far-side inputs float when the reference is connected but the signal is not.**
  A pull on the MCU side of the translator does not help; it is on the output. Add
  a weak pull on the connector side and ground unused inputs.
- **Outputs that must be safe when this board is off.** A power-enable or reset line
  to another machine needs a pull on the far side of the translator, because the
  translator is high-impedance when its near-side supply is absent.
- **Output-enable tied active.** The translator datasheet recommends holding outputs
  disabled during supply ramps. Where no spare MCU pin exists, far-side pulls define
  the idle levels instead; record that this was a choice.
- **I2C pull-ups for a cable.** 10 k with 100 pF gives a rise time fine for 100 kHz
  and outside the 400 kHz limit; 4.7 k was fitted.

### Straps, oscillators and margins

- **Strap pull-downs at the datasheet's suggested value can have almost no margin.**
  A 1.5 k pull-down against an internal pull-up of 7.5 to 12.5 k gave 0.55 to 0.58 V
  worst case against a 0.6 V threshold. 1 k gives 0.39 V. Compute the worst case, and
  have firmware write the configuration it needs rather than trust the strap.
- **Fit the strap resistors that only repeat an internal default** when a mis-strap
  would select a different interface mode; they are cheap insurance.
- **Crystal load capacitors.** CL is roughly C/2 plus 2 to 5 pF of stray. 15 pF
  capacitors on a 12 pF crystal give about 9 to 10 pF: tens of ppm fast. 33 pF on a
  20 pF crystal is right for load but see the next item.
- **Oscillator start-up margin, by calculation.** gm_crit = 4 x ESR x (2 pi f)^2 x
  (C0 + CL)^2, compared with the MCU's published maximum for each drive setting. A
  12.5 pF, 70 k 32.768 kHz crystal needed the highest drive setting (2.16 against
  limits of 0.48, 0.75, 1.7 and 2.7 uA/V); a 7 pF part needs 0.76 and passes at
  medium-high. An 8 MHz crystal at a distributor-listed 400 ohm ESR needs 0.79 mA/V
  against a 1 mA/V limit.
- **Departing from a vendor's reference crystal.** The RP2040 hardware design guide
  specifies a 10 pF, 50 ohm ESR crystal with 15 pF capacitors and 1 k in series, and
  warns that deviations may not oscillate. A basic-library 20 pF, 80 ohm part with
  33 pF capacitors needs about five times the gain, and the 1 k with 33 pF puts a
  pole below the crystal frequency. The boot ROM waits a fixed time for the
  oscillator, so a slow start shows as "no USB enumeration" and firmware cannot fix
  it. A 10 pF version of the same crystal family with the reference capacitors was
  fitted; its ESR is still 80 ohm, and start-up is a bring-up check.
- **Polyfuse hold current derates with temperature.** A 0.5 A part holds 0.42 A at
  40 C against a 0.43 A worst-case load. But oversizing has its own failure: a
  1.1 A part trips at 2.2 A, which a current-limited buck regulator may never draw
  from the input with its output shorted. 0.75 A was the answer here; read the
  derating table and the trip current, not just the headline rating.
- **Regulator absolute maximum close to the input voltage** (6 V on a 5 V input)
  with only ceramic input capacitance is worth a hot-plug ringing estimate.

### Things that depend on firmware and should not

- **Memory-card bus pull-ups.** With no external pull-ups the card works only if
  firmware enables internal ones, which a devicetree copied from another board may
  not. Five resistors were added at the next re-route.
- **A debug-probe function that depends on the firmware version.** The probe's
  target-reset pin was compiled out before a certain release of the stock firmware.
  State the minimum version on the schematic.
- **An MCU peripheral wired without optional signals** (no collision or carrier-sense
  lines on an Ethernet MAC) constrains firmware to full duplex. Write it down where
  the firmware author will see it.
- **Boot-mode button with nothing to boot from.** A BOOT button is only useful if a
  ROM bootloader interface is reachable on the pins as assigned. Check the vendor's
  boot-mode application note against the pin map.

### Footprints

- **Exposed-pad size is part of the footprint choice.** A VQFN-32 was given a generic
  5 x 5 mm footprint with a 3.1 mm pad; the part's pad is 2.1 mm. The stock library
  had the maker's exact footprint under the maker's package code.
- **Four-pad parts.** For each crystal, switch and DIP switch, establish from the
  maker's drawing which pads are common. A 4-pad tactile switch has two pairs; the
  symbol's two pins must land on different pairs.
- **LED terminal numbering differs between makers**; the netlist can be right and the
  placement rotation still wrong. Flag it for the assembly preview.
- **A footprint pad with no symbol pin** (a sensor's exposed pad that must float or
  be grounded) should be a decision, with paste and pour handled to match.

### Requirements

- Reviewers compare against the requirements, so wrong requirements surface: a
  voltage range nobody had asked for, a feature whose button reaches no usable
  function. Take these back to the owner.

## Layout

All on a board with zero DRC errors, zero unconnected items and clean parity.

- **Card socket backwards.** Rotated 180 degrees from the maker's drawing: the closed
  end at the board edge, the slot facing inboard over a capacitor.
- **Supply nets at signal width.** A 5 V rail 50 mm long at 0.127 mm (192 mohm) to
  cover 18 mm; switch node and regulator input at the same width; the whole regulator
  output entering the plane through one 0.25 mm via; the output capacitor 8 mm from
  it. Cause: a patch to the autorouter's input that forced one width on every net.
- **Tracks under screw heads**, 0.4 mm from the hole, on both sides, insulated by
  mask only; planes 0.25 mm from every unplated hole.
- **A pair length-matched by looping one line under the regulator's inductor**, and
  uncoupled for most of its length (about 120 ohm estimated against a 90 ohm target).
- **Feedback node 15 mm long**, running beside the input rail and the switch node,
  because the divider was auto-placed 13 mm from the regulator.
- **Decoupling near the IC but far from the pin**: a core-regulator output 13 mm of
  thin track from its capacitor; a PHY analogue supply 15 mm from its filter; a
  capacitor "belonging" to one IC being the nearest one to another IC's pin; a
  capacitor parked beside a strap pin that happens to be on the rail.
- **One ground via under each QFN** whose exposed pad is its only ground, with signal
  vias 0.14 mm from the pad under the package.
- **Reset capacitor beside the button**, 74 mm of track from the pin, the net passing
  under the Ethernet jack on both layers.
- **Planes under an integrated-magnetics jack** where the PHY datasheet says none.
- **Bottom-side labels composed in top-view order**, so the left word was beside the
  right pin when read from the bottom: supply and ground labels swapped.

And on the re-routed board, new:

- Two vias inside SMD pads, placed by the autorouter (moved by hand afterwards).
- Signal tracks on the component layer under two crystals.
- Two through-hole supply pins left on 0.18 mm slivers of plane by a new keep-out.
- Single ground vias on the regulator's capacitors.
- Two labels hidden under their own parts.

## What reviewers could not settle

Worth knowing so nobody assumes they were checked: assembly rotation of polarised
parts; oscillator start-up in circuit; behaviour of a translator in a partial-power
state its datasheet does not specify; whether a contradictory datasheet statement
(internal pull-downs listed in one section, "inputs must not float" in another) can
be relied on; part heights and 3D collisions; anything in the fabrication outputs.
