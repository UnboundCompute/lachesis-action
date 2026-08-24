#!/usr/bin/env python3
"""Apply reviewed, expiring suppression records to a SARIF report."""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Any


class SuppressionError(ValueError):
    """A malformed or expired suppression configuration."""


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SuppressionError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise SuppressionError(f"{path} is not valid JSON: {error}") from error


def _results(document: dict[str, Any], label: str) -> list[dict[str, Any]]:
    runs = document.get("runs")
    if not isinstance(runs, list) or not runs or not isinstance(runs[0], dict):
        raise SuppressionError(f"{label} has no SARIF runs")
    results = runs[0].get("results")
    if not isinstance(results, list):
        raise SuppressionError(f"{label} has no SARIF results array")
    return [result for result in results if isinstance(result, dict)]


def _location(result: dict[str, Any]) -> tuple[str, int | None]:
    locations = result.get("locations") or []
    physical = (locations[0] if locations else {}).get("physicalLocation") or {}
    artifact = physical.get("artifactLocation") or {}
    region = physical.get("region") or {}
    return str(artifact.get("uri", "")), region.get("startLine")


def _load_rules(path: Path) -> list[dict[str, Any]]:
    document = _load(path)
    if not isinstance(document, dict) or document.get("version") != 1:
        raise SuppressionError("suppression file version must be 1")
    entries = document.get("suppressions")
    if not isinstance(entries, list):
        raise SuppressionError("suppression file must contain a suppressions array")
    today = dt.date.today()
    rules = []
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise SuppressionError(f"suppression {position} must be an object")
        required = {"ruleId", "path", "reason", "expires"}
        if not required <= set(entry):
            missing = ", ".join(sorted(required - set(entry)))
            raise SuppressionError(f"suppression {position} missing: {missing}")
        if not all(isinstance(entry[key], str) and entry[key].strip() for key in required):
            raise SuppressionError(f"suppression {position} ruleId/path/reason/expires must be non-empty strings")
        try:
            expiry = dt.date.fromisoformat(entry["expires"])
        except ValueError as error:
            raise SuppressionError(f"suppression {position} expires must be YYYY-MM-DD") from error
        if expiry < today:
            raise SuppressionError(f"suppression {position} expired on {entry['expires']}")
        if "line" in entry and (not isinstance(entry["line"], int) or isinstance(entry["line"], bool) or entry["line"] <= 0):
            raise SuppressionError(f"suppression {position} line must be a positive integer")
        unknown = set(entry) - required - {"line"}
        if unknown:
            raise SuppressionError(f"suppression {position} has unknown field(s): {', '.join(sorted(unknown))}")
        rules.append(entry)
    return rules


def apply(document: dict[str, Any], rules: list[dict[str, Any]]) -> int:
    count = 0
    for result in _results(document, "current SARIF"):
        uri, line = _location(result)
        for rule in rules:
            if result.get("ruleId") != rule["ruleId"] or not fnmatch.fnmatch(uri, rule["path"]):
                continue
            if "line" in rule and line != rule["line"]:
                continue
            result.setdefault("suppressions", []).append({"kind": "external", "justification": rule["reason"]})
            result.setdefault("properties", {})["lachesis_suppression_expires"] = rule["expires"]
            count += 1
            break
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply expiring suppression records to SARIF in place.")
    parser.add_argument("current", type=Path, help="current SARIF report")
    parser.add_argument("--file", required=True, type=Path, help="suppression JSON file")
    args = parser.parse_args([] if argv is None else argv)
    try:
        current = _load(args.current)
        if not isinstance(current, dict):
            raise SuppressionError("current SARIF must be an object")
        count = apply(current, _load_rules(args.file))
        temporary = args.current.with_name(f".{args.current.name}.suppression.tmp")
        temporary.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, args.current)
    except (OSError, SuppressionError) as error:
        print(f"lachesis: {error}", file=sys.stderr)
        return 2
    print(f"lachesis: applied {count} suppression(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
