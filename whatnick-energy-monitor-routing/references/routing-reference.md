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

## DRC Gate

Final routed boards must have:

- Zero DRC errors.
- Zero unconnected items.
- No non-library violations introduced by routing, pours, holes, or silkscreen.
- Remaining warnings are understood and documented.
