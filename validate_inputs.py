"""Validate configurable Lachesis Action inputs before starting a scan."""

from __future__ import annotations

import os
import shlex
import sys


def validate(
    *,
    upload: str,
    fail_on: str,
    buffer_pool_size: str,
    c_jobs: str,
    analyze_args: str,
    sarif_file: str,
) -> list[str]:
    errors: list[str] = []

    if upload not in {"true", "false"}:
        errors.append("upload must be exactly 'true' or 'false'")

    if fail_on not in {"none", "note", "warning", "error"}:
        errors.append("fail-on must be one of: none, note, warning, error")

    for label, value in (
        ("kuzu-buffer-pool-size", buffer_pool_size),
        ("c-jobs", c_jobs),
    ):
        if not value and label == "c-jobs":
            continue
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = 0
        if parsed <= 0:
            errors.append(f"{label} must be a positive integer")

    try:
        shlex.split(analyze_args)
    except ValueError as error:
        errors.append(f"analyze-args has invalid shell quoting: {error}")

    if not sarif_file.strip():
        errors.append("sarif-file must not be empty")

    return errors


def main() -> int:
    errors = validate(
        upload=os.environ.get("LACHESIS_UPLOAD", ""),
        fail_on=os.environ.get("LACHESIS_FAIL_ON", ""),
        buffer_pool_size=os.environ.get("LACHESIS_KUZU_BUFFER_POOL_SIZE", ""),
        c_jobs=os.environ.get("LACHESIS_C_JOBS", ""),
        analyze_args=os.environ.get("LACHESIS_ANALYZE_ARGS", ""),
        sarif_file=os.environ.get("LACHESIS_SARIF_FILE", ""),
    )
    if errors:
        for error in errors:
            print(f"lachesis: invalid Action input: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
