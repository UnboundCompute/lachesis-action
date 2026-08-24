#!/usr/bin/env python3
"""Write a compact, stable provenance manifest beside a Lachesis SARIF report."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("runs"), list) or not document["runs"]:
        raise ValueError("SARIF document has no runs")
    if not isinstance(document["runs"][0], dict) or not isinstance(document["runs"][0].get("results"), list):
        raise ValueError("SARIF first run has no results array")
    return document


def build_manifest(
    sarif_path: Path,
    *,
    engine_sha: str,
    catalog_sha: str,
    toolchain_fingerprint: str,
    repository: str = "",
    commit_sha: str = "",
) -> dict[str, Any]:
    document = _read(sarif_path)
    results = [result for result in document["runs"][0]["results"] if isinstance(result, dict)]
    levels = Counter(str(result.get("level", "warning")) for result in results)
    suppressed = sum(bool(result.get("suppressions")) for result in results)
    run_properties = document["runs"][0].get("properties") or {}
    return {
        "format": "lachesis-evidence",
        "schema_version": 1,
        "analysis_projection": "security-paths",
        "repository": repository,
        "commit_sha": commit_sha,
        "engine_sha": engine_sha,
        "catalog_sha": catalog_sha,
        "toolchain_fingerprint": toolchain_fingerprint,
        "sarif": {
            "path": str(sarif_path),
            "sha256": hashlib.sha256(sarif_path.read_bytes()).hexdigest(),
            "results": len(results),
            "active_results": len(results) - suppressed,
            "suppressed_results": suppressed,
            "levels": dict(sorted(levels.items())),
            "baseline_removed": int(run_properties.get("lachesis_baseline_removed", 0)),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a Lachesis evidence manifest for a SARIF report.")
    parser.add_argument("sarif", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-sha", required=True)
    parser.add_argument("--catalog-sha", required=True)
    parser.add_argument("--toolchain-fingerprint", required=True)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""))
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    manifest = build_manifest(
        args.sarif, engine_sha=args.engine_sha, catalog_sha=args.catalog_sha,
        toolchain_fingerprint=args.toolchain_fingerprint,
        repository=args.repository, commit_sha=args.commit_sha,
    )
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"lachesis: wrote evidence manifest to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
