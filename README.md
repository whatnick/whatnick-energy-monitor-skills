# Whatnick Energy Monitor Skills

Portable Agent Skills for KiCad energy-monitor PCB design, based on the Agent Skills specification at https://agentskills.io/specification.

The skills capture recurring whatnick energy-monitor board families present in the workspace: large analog-connector boards, breadboard-only breakouts, PCI/riser DIN-rail modules, and FeatherWing boards.

Each top-level skill directory contains a required `SKILL.md` file and optional `references/` or `scripts/` resources. Skill names match their directory names and use lowercase hyphenated identifiers.

## Skills

- `whatnick-energy-monitor-circuit-design`: datasheet-first schematic and analog front-end design for metering IC breakouts.
- `whatnick-energy-monitor-bom-sourcing`: preferred reusable MPNs, schematic sourcing fields, DigiKey/Mouser checks, and CSV/XLSX BOM export discipline for bulk reel buying.
- `whatnick-energy-monitor-layout-design`: placement, connector grouping, form-factor conventions, STEP model practices, references, markings, and silkscreen cleanup.
- `whatnick-energy-monitor-routing`: routing priorities, net classes, GND planes, Freerouting, and DRC validation.
- `whatnick-energy-monitor-elecrow-ordering`: verified PCB/PCBA packages,
  authenticated Playwright submissions, quote/workbook and service-order
  audits, duplicate/build tracking, lifecycle handoff, privacy, and safe gates
  before payment or production.
- `whatnick-energy-monitor-pcb-size-shape`: large analog-connector, breadboard-only, PCI/riser, FeatherWing, compact, and bench-board form-factor choices.
- `whatnick-energy-monitor-schematic-generation`: KiCad 10 schematics emitted from Python, the file-format details that needs, and the intent-against-netlist check that catches what ERC cannot.
- `whatnick-energy-monitor-scripted-layout`: boards built, placed and pre-routed by pcbnew scripts; plane vias, keep-outs, scripted critical nets, routing variants, and KiCad 10 pcbnew notes.
- `whatnick-energy-monitor-freerouting-batches`: checking and patching the Specctra DSN, Freerouting 2.x settings, parallel batches of differing attempts, and reading the results.
- `whatnick-energy-monitor-jlcpcb-assembly`: dated JLCPCB 4-layer rules, impedance-calculator readings, part classes and assembly fees, cost modelling, and what is still owed before an order.
- `whatnick-energy-monitor-design-review`: independent schematic and layout review by fresh reviewers, briefs, triage, and a catalogue of faults found on DRC-clean designs.
- `ade9000-breakout`: ADE9000_Breakout project overlay for local scripts, topology facts, and KiCad 10 pitfalls.
- `stpm3x-breakout`: STPM3x_Breakout project overlay for the compact STPM32
  analog front end, pin contracts, ground domains, silkscreen, generation
  scripts, and tool-neutral reconstruction.

## Layout

```text
skill-name/
  SKILL.md
  references/
  scripts/
```

## Validation

Basic local checks:

```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" .\scripts\validate_skills.py
```

Any Python 3.9+ runs the validator. Scripts that import `pcbnew` need the Python
interpreter that ships with KiCad; the skills write it as `$KICAD_PYTHON`, which you
set to wherever your KiCad install keeps it:

```bash
python3 scripts/validate_skills.py
"$KICAD_PYTHON" whatnick-energy-monitor-design-review/scripts/audit_board.py BOARD.kicad_pcb
```

The last five skills above came from a 4-layer microcontroller board designed almost
entirely by script (KiCad 10, JLCPCB assembly). They are not specific to
energy monitors; they keep the repository's naming prefix so they install alongside
the others.

Full spec validation can be run with the Agent Skills reference validator when available:

```powershell
skills-ref validate .\whatnick-energy-monitor-routing
```
