# Routing Reference

## Freerouting Flow

Use fresh DSN/SES files and avoid stale in-memory board state.

```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" .\scripts\clear_routes_text.py .\BOARD.kicad_pcb
& "C:\Program Files\KiCad\10.0\bin\python.exe" .\scripts\clear_zones_text.py .\BOARD.kicad_pcb
& "C:\Program Files\KiCad\10.0\bin\python.exe" -c "import pcbnew; board=pcbnew.LoadBoard(r'BOARD.kicad_pcb'); pcbnew.ExportSpecctraDSN(board, r'BOARD.dsn')"
& "C:\path\to\java.exe" -jar "C:\path\to\freerouting.jar" -de .\BOARD.dsn -do .\BOARD.ses -mp 100
& "C:\Program Files\KiCad\10.0\bin\python.exe" -c "import pcbnew; path=r'BOARD.kicad_pcb'; board=pcbnew.LoadBoard(path); pcbnew.ImportSpecctraSES(board, r'BOARD.ses'); pcbnew.SaveBoard(path, board)"
```

## KiCad 10 Notes

- Export DSN with `pcbnew.ExportSpecctraDSN`.
- Import SES with `pcbnew.ImportSpecctraSES`.
- For KiCad 10 vias, avoid `PCB_VIA.GetWidth()` without layer context; use `GetFrontWidth()` or set width directly.
- Clear zones before rerouting if filled zones obscure DRC diagnosis or affect DSN export.

## Form-Factor Routing Patterns

- Large analog-connector boards: route connector-to-filter analog paths by channel first, route supply rails with an explicit power netclass, then add GND planes after the critical paths are stable.
- Breadboard-only breakouts: preserve header escape routes and bottom-side test-pad fanout before optimizing cosmetic trace symmetry; dense 0.15 mm rules are often appropriate.
- PCI/riser modules: fan out the edge/backplane connector first, reserve lanes for repeated measurement channels, and keep high-current or field-wiring nets away from host bus traces where possible.
- FeatherWings: route Feather header power/host bus pins early, keep analog sampling away from USB/battery/high-current host areas, and verify stacked-header clearance after routing.
- DIN-rail/backplane boards should be validated mechanically as well as electrically because edge connector geometry is part of the routed interface.

## CT Escape Routing After Connector Setback

1. Freeze the enclosure datum, connector pinout, burden topology and separation boundaries. Identify each CT connector-to-burden branch separately from the burden-to-meter sense branch. Reserve paths for both legs before completing either one.
2. Measure actual copper, not just pin pitch: a single trace between two pads needs at least `trace width + clearance to each pad`. That is only a straight-line check; bends, adjacent escapes, vias, drills and assembly tolerances can still close the corridor. Check both layers before changing track widths or vias, and keep changes inside existing electrical and fabrication constraints.
3. Use a bounded rip-up in a scratch copy. Include the immediate blocking routes when needed, but require every disturbed net to reconnect. A smaller ratsnest count is not acceptance if previously connected channels regress. Keep unrelated routing, power/ground domains, slots and safety clearances intact.
4. If copper routing stalls, try a 0-ohm chip crossover in a **sense branch after the burden tap**, not in series with the burden or as a substitute for it. Keep the CT burden connected locally even with the link unpopulated. Use the actual footprint and check the gap between lands, what copper passes under the body, solder mask, nearby component courtyards and installed height. Package name alone does not determine the gap. A crossover is not an isolation barrier. Select the part from its maximum resistance and current specs; preserve pair balance, small loop area and distance from switching nodes. Verify gain, phase and noise over the measurement bandwidth on a safe test setup before accepting signal integrity.
5. If a link is used, add it to the schematic and BOM with distinct nets on its two sides; run ERC. Refill zones and compare before/after DRC with the same KiCad version, project rules and library configuration. Inspect missing connections by net and endpoint as well as counts; also review new copper, thermal and mask violations. Recheck the populated assembly against the enclosure and mating parts.

### Example: two-layer DIN current-input fanout

In the [DIN power-board fit prototype](https://github.com/whatnick/din_power_atm90e26/tree/6f0ef16adf11d8c8b4b1da72f517e23ae0198bc4), recessing the Nano-Fit bank and burdens by 2 mm left three sense connections open to the fixed riser socket. Adjacent pins at 2.50 mm pitch with 1.90 mm copper pads left 0.60 mm; a 0.25 mm trace with 0.20 mm clearance on each side needed 0.65 mm. Even the existing 0.20 mm track minimum only met that idealized gap exactly.

A bounded five-net rip-up and refilled-zone DRC closed `IA1+` and `IB1-`, but left `IA1-` open and reopened `IB1+`. The original CT-to-burden branches were retained in the trial. A geometric search for same-layer chip crossovers found no candidate for the two remaining opens in that trial; that is not proof that no placement exists, and no jumper was validated or added. The trial was not promoted. Reserve complete pair escapes earlier or change the local fanout placement before relying on narrower tracks or jumper footprints to rescue a congested connector move.

## DRC Gate

Final routed boards must have:

- Zero DRC errors.
- Zero unconnected items.
- No non-library violations introduced by routing, pours, holes, or silkscreen.
- Remaining warnings are understood and documented.
