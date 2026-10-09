#!/usr/bin/env python3
"""Check that Compose Watch ignores every pattern from .dockerignore files."""

from pathlib import Path
import sys

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML is required for this check. Install it with "
        "`python3 -m pip install PyYAML` or run it from an environment that "
        "already provides PyYAML."
    )

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "docker-compose.yml"
WATCH_IGNORE_KEY = "x-local-watch-ignore"


def normalize(pattern):
    pattern = pattern.strip().strip('"').strip("'")
    pattern = pattern.lstrip("/")
    while pattern.endswith("/"):
        pattern = pattern[:-1]
    return pattern


def dockerignore_patterns(path):
    base = path.parent.relative_to(ROOT)
    patterns = []

    for line_number, raw_line in enumerate(path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            sys.exit(
                f"{path}:{line_number}: negated dockerignore patterns are "
                "not supported by the Compose Watch ignore check."
            )

        pattern = normalize(line)
        if base != Path("."):
            pattern = normalize(str(base / pattern))
        patterns.append(pattern)

    return patterns


def load_compose_watch_ignore():
    with COMPOSE_FILE.open() as compose:
        config = yaml.safe_load(compose)

    if not isinstance(config, dict) or WATCH_IGNORE_KEY not in config:
        sys.exit(f"{COMPOSE_FILE} does not define {WATCH_IGNORE_KEY}.")

    watch_ignore = config[WATCH_IGNORE_KEY]
    if not isinstance(watch_ignore, list):
        sys.exit(f"{WATCH_IGNORE_KEY} must be a YAML list.")

    invalid = [item for item in watch_ignore if not isinstance(item, str)]
    if invalid:
        sys.exit(f"{WATCH_IGNORE_KEY} must contain only string patterns.")

    return {normalize(item) for item in watch_ignore}


def main():
    dockerignore_files = sorted(ROOT.rglob(".dockerignore"))
    required = set()
    for path in dockerignore_files:
        required.update(dockerignore_patterns(path))

    watch_ignore = load_compose_watch_ignore()
    missing = sorted(required - watch_ignore)

    if missing:
        print(
            "Compose Watch does not ignore every pattern listed in "
            ".dockerignore files.",
            file=sys.stderr,
        )
        print("\nMissing from x-local-watch-ignore:", file=sys.stderr)
        for pattern in missing:
            print(f"  - {pattern}", file=sys.stderr)
        return 1

    print("Compose Watch ignore patterns cover .dockerignore patterns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
