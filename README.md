# Whatnick Energy Monitor Skills

Portable Agent Skills for KiCad energy-monitor PCB design, based on the Agent Skills specification at https://agentskills.io/specification.

The skills capture recurring whatnick energy-monitor board families present in the workspace: large analog-connector boards, breadboard-only breakouts, PCI/riser DIN-rail modules, and FeatherWing boards.

Each top-level skill directory contains a required `SKILL.md` file and optional `references/` or `scripts/` resources. Skill names match their directory names and use lowercase hyphenated identifiers.

## Skills

- `whatnick-energy-monitor-circuit-design`: datasheet-first schematic and analog front-end design for metering IC breakouts.
- `whatnick-energy-monitor-bom-sourcing`: preferred reusable MPNs, schematic sourcing fields, DigiKey/Mouser checks, and CSV/XLSX BOM export discipline for bulk reel buying.
- `whatnick-energy-monitor-layout-design`: placement, connector grouping, form-factor conventions, STEP model practices, references, markings, and silkscreen cleanup.
- `whatnick-energy-monitor-routing`: routing priorities, net classes, GND planes, Freerouting, and DRC validation.
- `whatnick-energy-monitor-pcb-size-shape`: large analog-connector, breadboard-only, PCI/riser, FeatherWing, compact, and bench-board form-factor choices.
- `ade9000-breakout`: ADE9000_Breakout project overlay for local scripts, topology facts, and KiCad 10 pitfalls.

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

Full spec validation can be run with the Agent Skills reference validator when available:

```powershell
skills-ref validate .\whatnick-energy-monitor-routing
```
