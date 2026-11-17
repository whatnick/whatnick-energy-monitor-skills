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

The same flow in a POSIX shell, with `KICAD_PYTHON` set to the interpreter that ships
with KiCad (the only one that can import `pcbnew`) and `kicad-cli` and `java` on
`PATH`:

```bash
"$KICAD_PYTHON" scripts/clear_routes_text.py BOARD.kicad_pcb
"$KICAD_PYTHON" scripts/clear_zones_text.py BOARD.kicad_pcb
"$KICAD_PYTHON" -c "import pcbnew; b=pcbnew.LoadBoard('BOARD.kicad_pcb'); pcbnew.ExportSpecctraDSN(b, 'BOARD.dsn')"
java -jar freerouting.jar -de BOARD.dsn -do BOARD.ses \
  --router.autorouter.max_passes=30 --router.job_timeout=00:20:00
"$KICAD_PYTHON" -c "import pcbnew; p='BOARD.kicad_pcb'; b=pcbnew.LoadBoard(p); pcbnew.ImportSpecctraSES(b, 'BOARD.ses'); pcbnew.SaveBoard(p, b)"
kicad-cli pcb drc --format json --severity-all --output drc.json BOARD.kicad_pcb
```

With Freerouting 2.5.0, `-mp N` still works but is reported as deprecated in favour of
`--router.autorouter.max_passes=N`, and a job with no `--router.job_timeout` was cut
off after about two minutes on a 300-part board.

## KiCad 10 Notes

- Export DSN with `pcbnew.ExportSpecctraDSN`.
- Import SES with `pcbnew.ImportSpecctraSES`.
- For KiCad 10 vias, avoid `PCB_VIA.GetWidth()` without layer context; use `GetFrontWidth()` or set width directly.
- Clear zones before rerouting if filled zones obscure DRC diagnosis or affect DSN export.
- The DSN export writes `(type signal)` for every copper layer. On a board with plane
  layers, change those layers to `(type power)` in the DSN or the autorouter will
  route through the planes.
- Tracks and vias marked locked in KiCad are exported as `(type fix)` and are kept by
  the autorouter; rule areas are exported as `keepout` polygons.
- Export the DSN from a process that loaded the saved board and its `.kicad_pro` from
  disk. Exported from the same process that created the board and then wrote the
  project file, it carried 0.2 mm track and clearance and a 0.6/0.3 mm via whatever
  the project said.
- `PCB_VIA.SetWidth(width)` and `SetWidth(layer, width)` both work in 10.0.8;
  `GetWidth()` without a layer prints an assertion warning.
- After removing items from a board in Python, take `list(board.GetTracks())` and
  `list(board.Zones())` once and keep them; the wrappers can stop iterating.
- `kicad-cli pcb drc` applies custom rules from `BOARD.kicad_dru` beside the board as
  well as the constraints in `BOARD.kicad_pro`.

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

Passing this gate does not mean the layout is good; it means it is ready to be
reviewed for the things DRC does not check.
