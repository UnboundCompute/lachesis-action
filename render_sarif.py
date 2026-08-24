#!/usr/bin/env python3
"""Render Lachesis SARIF as portable Markdown or standalone HTML."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("runs"), list) or not value["runs"]:
        raise ValueError("SARIF document has no runs")
    return value


def _results(document: dict[str, Any]) -> list[dict[str, Any]]:
    return [value for value in document["runs"][0].get("results", []) if isinstance(value, dict)]


def _location(result: dict[str, Any]) -> str:
    try:
        physical = result["locations"][0]["physicalLocation"]
        uri = physical["artifactLocation"]["uri"]
        line = physical.get("region", {}).get("startLine")
        return f"{uri}:{line}" if line else str(uri)
    except (KeyError, IndexError, TypeError):
        return "unknown location"


def _lifecycle(result: dict[str, Any]) -> str:
    properties = result.get("properties") or {}
    return str(properties.get("lachesis_lifecycle") or result.get("baselineState") or "")


def _flow(result: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    for thread in result.get("codeFlows", []):
        for location in thread.get("threadFlows", [{}])[0].get("locations", []):
            physical = location.get("location", {}).get("physicalLocation", {})
            uri = physical.get("artifactLocation", {}).get("uri")
            line = physical.get("region", {}).get("startLine")
            if uri:
                steps.append(f"{uri}:{line}" if line else str(uri))
    return steps


def render_markdown(document: dict[str, Any], evidence: dict[str, Any] | None = None) -> str:
    results = _results(document)
    lines = ["# Lachesis findings", "", f"Results: {len(results)}", ""]
    if evidence:
        sarif = evidence.get("sarif") or {}
        lines.extend([
            f"Evidence SHA-256: `{sarif.get('sha256', 'unknown')}`",
            f"Engine: `{evidence.get('engine_sha', 'unknown')}`  ",
            f"Catalog: `{evidence.get('catalog_sha', 'unknown')}`", "",
        ])
    if not results:
        lines.append("No results.")
        return "\n".join(lines) + "\n"
    for index, result in enumerate(results, 1):
        lifecycle = _lifecycle(result)
        suffix = f" · lifecycle: `{lifecycle}`" if lifecycle else ""
        lines.extend([
            f"## {index}. `{result.get('ruleId', 'unknown')}`{suffix}",
            f"- Level: `{result.get('level', 'warning')}`",
            f"- Location: `{_location(result)}`",
            f"- Message: {result.get('message', {}).get('text', 'No message.')}",
        ])
        flow = _flow(result)
        if flow:
            lines.append("- Code flow:")
            lines.extend(f"  - `{step}`" for step in flow)
        lines.append("")
    return "\n".join(lines)


def render_html(document: dict[str, Any], evidence: dict[str, Any] | None = None) -> str:
    results = _results(document)
    title = "Lachesis findings"
    cards = []
    for result in results:
        lifecycle = _lifecycle(result)
        flow = _flow(result)
        details = "".join(f"<li><code>{html.escape(step)}</code></li>" for step in flow)
        cards.append(
            "<details open><summary><strong>{}</strong> <code>{}</code></summary>"
            "<p><b>Location:</b> <code>{}</code><br><b>Level:</b> <code>{}</code>{}</p>"
            "<p>{}</p>{}</details>".format(
                html.escape(str(result.get("ruleId", "unknown"))),
                html.escape(str(result.get("level", "warning"))),
                html.escape(_location(result)),
                html.escape(str(result.get("level", "warning"))),
                f"<br><b>Lifecycle:</b> <code>{html.escape(lifecycle)}</code>" if lifecycle else "",
                html.escape(str(result.get("message", {}).get("text", "No message."))),
                f"<p><b>Code flow</b><ol>{details}</ol></p>" if details else "",
            )
        )
    return "<!doctype html><meta charset='utf-8'><title>{}</title><style>body{{font:16px system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}}details{{border:1px solid #ddd;padding:1rem;margin:1rem 0}}code{{background:#f3f3f3;padding:.1rem .25rem}}</style><h1>{}</h1><p>Rendered from Lachesis SARIF. The original SARIF and evidence receipt remain authoritative.</p>{}\n".format(
        title, title, "".join(cards)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sarif", type=Path)
    parser.add_argument("--format", choices=("markdown", "html"), default="markdown")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    document = _read(args.sarif)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8")) if args.evidence else None
    rendered = render_markdown(document, evidence) if args.format == "markdown" else render_html(document, evidence)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"lachesis: wrote {args.format} report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
