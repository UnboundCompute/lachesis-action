"""Apply the Lachesis Action's fail-on threshold to a SARIF report."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ORDER = {"note": 1, "warning": 2, "error": 3}


class SarifError(ValueError):
    """A user-actionable SARIF shape or read error."""


def _results(path: str | Path) -> list[dict[str, Any]]:
    report_path = Path(path)
    try:
        with report_path.open(encoding="utf-8") as stream:
            document = json.load(stream)
    except OSError as error:
        raise SarifError(f"cannot read SARIF report {report_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise SarifError(f"SARIF report {report_path} is not valid JSON: {error}") from error

    if not isinstance(document, dict):
        raise SarifError("SARIF document must be a JSON object")
    runs = document.get("runs")
    if not isinstance(runs, list) or not runs:
        raise SarifError("SARIF document has no runs")
    first = runs[0]
    if not isinstance(first, dict) or not isinstance(first.get("results"), list):
        raise SarifError("SARIF first run has no results array")
    return [result for result in first["results"] if isinstance(result, dict)]


def findings_at_or_above(path: str | Path, threshold: str) -> list[dict[str, Any]]:
    """Return results whose SARIF level meets ``threshold``."""
    if threshold not in ORDER:
        raise SarifError(
            f"invalid fail-on value {threshold!r}; expected note, warning, or error"
        )
    gate = ORDER[threshold]
    return [
        result
        for result in _results(path)
        if not result.get("suppressions")
        if ORDER.get(str(result.get("level", "warning")).lower(), 2) >= gate
    ]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: gate_sarif.py REPORT.sarif note|warning|error", file=sys.stderr)
        return 2
    try:
        hits = findings_at_or_above(args[0], args[1])
    except SarifError as error:
        print(f"lachesis: {error}", file=sys.stderr)
        return 2
    if hits:
        print(f"lachesis: {len(hits)} finding(s) at or above '{args[1]}'")
        return 1
    print(f"lachesis: no findings at or above '{args[1]}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
