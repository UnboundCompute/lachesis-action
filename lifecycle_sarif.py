#!/usr/bin/env python3
"""Annotate current SARIF results with cross-run lifecycle state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def finding_id(result: dict[str, Any]) -> str:
    properties = result.get("properties") or {}
    envelope = properties.get("lachesisFinding") or {}
    value = envelope.get("finding_id")
    if not isinstance(value, str) or not value:
        value = (result.get("partialFingerprints") or {}).get("lachesisFinding", "")
    return value if isinstance(value, str) else ""


def apply_lifecycle(current: dict[str, Any], previous: dict[str, Any]) -> int:
    previous_lifecycle = previous.get("finding_lifecycle") or {}
    previous_ids = {
        value for value in previous_lifecycle.get("observed_finding_ids", [])
        if isinstance(value, str) and value
    }
    run = current["runs"][0]
    changed = 0
    for result in run.get("results", []):
        if not isinstance(result, dict):
            continue
        identifier = finding_id(result)
        if not identifier:
            continue
        state = "unchanged" if identifier in previous_ids else "new"
        result["baselineState"] = state
        result.setdefault("properties", {})["lachesis_lifecycle"] = state
        changed += 1
    run.setdefault("properties", {})["lachesis_lifecycle_state"] = "compared"
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current", type=Path)
    parser.add_argument("--previous-evidence", required=True, type=Path)
    args = parser.parse_args(argv)
    current = json.loads(args.current.read_text(encoding="utf-8"))
    previous = json.loads(args.previous_evidence.read_text(encoding="utf-8"))
    changed = apply_lifecycle(current, previous)
    args.current.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"lachesis: annotated {changed} SARIF finding lifecycle state(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
