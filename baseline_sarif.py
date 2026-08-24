#!/usr/bin/env python3
"""Filter SARIF results already present in a trusted baseline report."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


class BaselineError(ValueError):
    """A malformed or unreadable SARIF baseline."""


def _document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise BaselineError(f"cannot read SARIF file {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise BaselineError(f"SARIF file {path} is not valid JSON: {error}") from error
    if not isinstance(document, dict) or not isinstance(document.get("runs"), list) or not document["runs"]:
        raise BaselineError(f"SARIF file {path} has no runs")
    if not isinstance(document["runs"][0], dict) or not isinstance(document["runs"][0].get("results"), list):
        raise BaselineError(f"SARIF file {path} has no results array")
    return document


def _key(result: dict[str, Any]) -> tuple[str, str, int | None]:
    locations = result.get("locations") or []
    physical = (locations[0] if locations else {}).get("physicalLocation") or {}
    artifact = physical.get("artifactLocation") or {}
    region = physical.get("region") or {}
    return (str(result.get("ruleId", "")), str(artifact.get("uri", "")), region.get("startLine"))


def _fingerprint(result: dict[str, Any]) -> str:
    fingerprints = result.get("partialFingerprints") or {}
    return str(fingerprints.get("lachesisFinding", ""))


def filter_document(current: dict[str, Any], baseline: dict[str, Any]) -> int:
    baseline_keys = {
        _key(result)
        for result in baseline["runs"][0]["results"]
        if isinstance(result, dict)
    }
    baseline_fingerprints = {
        fingerprint
        for result in baseline["runs"][0]["results"]
        if isinstance(result, dict)
        for fingerprint in [_fingerprint(result)]
        if fingerprint
    }
    results = current["runs"][0]["results"]
    def is_baselined(result: Any) -> bool:
        if not isinstance(result, dict):
            return False
        fingerprint = _fingerprint(result)
        return (fingerprint and fingerprint in baseline_fingerprints) or _key(result) in baseline_keys

    kept = [result for result in results if not is_baselined(result)]
    removed = len(results) - len(kept)
    current["runs"][0]["results"] = kept
    current.setdefault("runs", [{}])[0].setdefault("properties", {})["lachesis_baseline_removed"] = removed
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove SARIF findings present in a baseline report.")
    parser.add_argument("current", type=Path, help="current SARIF report to filter in place")
    parser.add_argument("--baseline", required=True, type=Path, help="trusted baseline SARIF report")
    args = parser.parse_args([] if argv is None else argv)
    try:
        current = _document(args.current)
        baseline = _document(args.baseline)
        removed = filter_document(current, baseline)
        temporary = args.current.with_name(f".{args.current.name}.baseline.tmp")
        temporary.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, args.current)
    except (OSError, BaselineError) as error:
        print(f"lachesis: {error}", file=sys.stderr)
        return 2
    print(f"lachesis: baseline removed {removed} existing finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
