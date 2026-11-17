# pcbnew scripting notes for KiCad 10

Everything here was observed on KiCad 10.0.8, using the Python that ships with it
(3.9.13). Items marked "inferred" were not isolated in a
test.

## Environment

- Only the interpreter that ships with KiCad can import `pcbnew`; a system `python3`
  cannot. Find it in the KiCad install and pass it to scripts as a setting (the
  examples in these skills call it `KICAD_PYTHON`) instead of writing its path into
  them.
- Stock libraries are in the install's `symbols`, `footprints` and `3dmodels`
  directories. Take their location from a setting or from KiCad's path variables
  (Preferences > Configure Paths), not a literal path in the script.
- No numpy in that interpreter. Python 3.9: no `itertools.pairwise`, no `match`
  statement, no `X | Y` type unions at run time.
- Every script prints `assert "traits" failed in Get(): create wxApp before calling
  this` and a run of wx image-handler debug lines on start, and
  `swig/python detected a memory leak of type 'ZONE *'` (or `PCB_TRACK *`) when
  objects are removed. All harmless. Filter them from logs, but filter narrowly: a
  blanket `grep -v Debug` also removes every line that mentions a sheet or net with
  "Debug" in its name, and hid real failures on the reference project.

## Wrapper pitfalls

- **Collections stop iterating.** After items have been removed from a board, or
  after earlier wrapper objects have been garbage collected, `board.GetTracks()`,
  `board.Zones()` and `board.GetFootprints()` can raise
  `TypeError: 'SwigPyObject' object is not iterable`. Take `list(...)` of each once,
  straight after loading, keep those lists alive for the life of the script, and read
  any pad positions you will need before removing tracks.
- **Do not reload and strip a routed board to start again.** Rebuild it from the
  netlist instead. The script that removed zones and tracks from a reloaded board hit
  the pitfall above; rebuilding is also what guarantees the result does not depend on
  history.
- `LSET.Seq()` returns a swig vector; wrap it in `list()` before comparing to a list.

## Project settings and the Specctra export

- `pcbnew.SaveBoard` writes the `.kicad_pcb` only. Design rules, net classes and
  net-class patterns live in the `.kicad_pro` JSON
  (`board.design_settings.rules`, `net_settings.classes`,
  `net_settings.netclass_patterns`); write that file from the script. `kicad-cli pcb
  drc` reads it, and custom rules from a `.kicad_dru` beside it.
- **Export the DSN from a fresh process.** Verified by experiment: when a script
  creates or first loads a board at a path before the `.kicad_pro` exists and then,
  in the same process, writes the project file and calls `pcbnew.LoadBoard` on that
  path again, `ExportSpecctraDSN` emits KiCad's built-in defaults (track and
  clearance 0.2 mm, via 0.6/0.3 mm, one class). A new process loading the same two
  files exports the project's classes correctly (for example default 0.127 mm, a
  0.25 mm pair class, a 0.4 mm power class, 0.45/0.25 mm via). So build the board in
  one process and export in another, and check the widths in the DSN before routing.
- The export marks every copper layer `(type signal)`, plane layers included, in
  either case. See the freerouting-batches skill.
- The via padstack the DSN offers (`"Via[0-3]_450:250_um"`) is the project's via size
  when the project is seen, and 600:300 when it is not.

## Calls that work

Build and identity:

```python
fp = pcbnew.FootprintLoad(str(lib_dir / f"{lib}.pretty"), name)
fp.SetReference(ref); fp.SetValue(value)
fp.SetFPID(pcbnew.LIB_ID(lib, name))
fp.SetPath(pcbnew.KIID_PATH(f"/{sheet_uuid}/{symbol_uuid}"))   # from the netlist's sheetpath and tstamps
fp.SetSheetname(sheet_name)
fp.SetField("MPN", mpn); fp.GetField("MPN").SetVisible(False)  # GetFieldByName does not exist
for pad in fp.Pads():
    pad.SetNet(net_for[(ref, pad.GetNumber())])                 # a pcbnew.NETINFO_ITEM(board, name), added to the board first
board.Add(fp)
```

- Fields added with `SetField` are visible on the silkscreen layer until hidden.
- For a do-not-populate part set `FP_DNP` only. Also setting exclude-from-BOM or
  exclude-from-position on the footprint when the symbol does not have them fails
  parity with `footprint_symbol_mismatch`.
- `fp.GetCourtyard(pcbnew.F_CrtYd).BBox()` gives the courtyard box after
  `fp.BuildCourtyardCaches()` (fall back to `fp.GetBoundingBox(False)` when the footprint
  has no courtyard); position parts by courtyard centre.
- The symbol path set with `SetPath` is what `--schematic-parity` matches on; with it
  set, a script-built board reported zero parity issues.
- A later loop that sets `Reference().SetVisible(True)` for every footprint undoes an
  earlier hide. Decide visibility in one place.

Tracks and vias:

```python
via = pcbnew.PCB_VIA(board)
via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
via.SetDrill(pcbnew.FromMM(0.25))
via.SetWidth(pcbnew.F_Cu, pcbnew.FromMM(0.45))    # the one-argument form also still works
via.SetNet(pad.GetNet()); board.Add(via)

track = pcbnew.PCB_TRACK(board)
track.SetStart(...); track.SetEnd(...); track.SetWidth(pcbnew.FromMM(0.2))
track.SetLayer(pcbnew.F_Cu); track.SetNet(pad.GetNet()); track.SetLocked(True); board.Add(track)
```

- `PCB_VIA.GetWidth()` with no layer argument prints an assertion warning; use
  `GetWidth(pcbnew.F_Cu)` or `GetFrontWidth()`.
- Distinguish with `item.GetClass()`: `"PCB_VIA"`, `"PCB_TRACK"`, `"PCB_ARC"`.

Zones, rule areas, fill:

```python
zone = pcbnew.ZONE(board)
zone.SetLayer(pcbnew.In1_Cu); zone.SetNet(board.FindNet("GND"))
outline = zone.Outline(); outline.NewOutline()
for x, y in corners: outline.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
zone.SetMinThickness(pcbnew.FromMM(0.2)); zone.SetLocalClearance(pcbnew.FromMM(0.2))
board.Add(zone)

area = pcbnew.ZONE(board)                 # keep-out
area.SetIsRuleArea(True); area.SetZoneName("screw head")
layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.B_Cu)
area.SetLayerSet(layers)
area.SetDoNotAllowTracks(True); area.SetDoNotAllowVias(True); area.SetDoNotAllowZoneFills(True)
area.SetDoNotAllowPads(False); area.SetDoNotAllowFootprints(False)
# outline as above, then board.Add(area)

fill = pcbnew.ZONES()
for z in zones:                            # a list taken earlier
    if not z.GetIsRuleArea(): fill.append(z)
pcbnew.ZONE_FILLER(board).Fill(fill)
```

- Rule areas reach the Specctra export as `keepout` polygons per layer, so the
  autorouter honours them.
- `zone.GetFilledPolysList(layer).OutlineCount()` after a fill tells you whether a
  plane is in one piece.

Specctra:

```python
pcbnew.ExportSpecctraDSN(board, "board.dsn")    # returns False on failure
pcbnew.ImportSpecctraSES(board, "board.ses")
```

## 3D models

- KiCad ships no model for many connectors and some IC packages even though the
  stock footprint names one. A footprint whose `(model ...)` file is missing renders
  as bare pads.
- `uvx easyeda2kicad --lcsc_id C12345 --3d --output DIR/C12345` fetched a STEP file
  for every part tried (RJ45 with magnetics, USB-C, microSD, tactile switch, VQFN),
  sending only the LCSC number. Point the footprint's model at
  `${KIPRJMOD}/lib/3d/NAME.step`. One of five needed an offset, found by rendering.
- The redistribution terms of those models were not established; the reference
  project keeps them out of version control and commits a fetch script instead.

## DRC from the command line

```bash
kicad-cli pcb drc --format json --severity-all --schematic-parity --output drc.json BOARD.kicad_pcb
```

The JSON has `violations` (each with `type`, `severity`, `items[].description`,
`items[].pos`), `unconnected_items` and `schematic_parity`. Positions are in the
file's coordinates, not relative to the board corner. Check option names with
`kicad-cli pcb drc --help` on a new KiCad version before relying on them.
