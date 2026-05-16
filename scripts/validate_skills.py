from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\r?\n(?P<body>.*?)\r?\n---\r?\n", re.DOTALL)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter")

    metadata: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if not line.strip() or line.startswith("  "):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return ["missing SKILL.md"]

    try:
        metadata = parse_frontmatter(skill_file)
    except ValueError as exc:
        return [str(exc)]

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    compatibility = metadata.get("compatibility", "")

    if name != skill_dir.name:
        errors.append(f"name {name!r} does not match directory {skill_dir.name!r}")
    if not NAME_RE.fullmatch(name):
        errors.append(f"name {name!r} is not lowercase hyphenated")
    if len(name) > 64:
        errors.append("name exceeds 64 characters")
    if not description:
        errors.append("description is empty")
    if len(description) > 1024:
        errors.append("description exceeds 1024 characters")
    if compatibility and len(compatibility) > 500:
        errors.append("compatibility exceeds 500 characters")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    skill_dirs = sorted(path for path in root.iterdir() if path.is_dir() and (path / "SKILL.md").exists())
    if not skill_dirs:
        print("No skill directories found", file=sys.stderr)
        return 1

    failed = False
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        if errors:
            failed = True
            print(f"FAIL {skill_dir.name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {skill_dir.name}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
