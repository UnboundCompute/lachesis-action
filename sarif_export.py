#!/usr/bin/env python3
"""Export Lachesis security findings as SARIF 2.1.0.

v1. This is a thin, dependency-free renderer: it drives the existing
`lachesis-query` CLI (nothing private, no new engine) and maps the
source-to-sink paths and guard verdicts it already computes onto SARIF
results. The hosted poster consumes this SARIF and renders it as inline
PR comments signed by the Lachesis GitHub App.

    python3 action/sarif_export.py graph.kuzu -o lachesis.sarif

It reads one query when the engine supports it:
  * `security-paths` -> every reachable path's guard verdict, source, and sink
                        location in a single graph load (one process, not N).
Older engines that lack the batch command fall back to `overview` +
per-path `security-path` calls, which is correct but pays a graph reload each.

Findings are anchored at the sink call site, carry the tainted flow as a SARIF
codeFlow, and are leveled by guard status:
  UNGUARDED + guarded sibling exists -> error   (a real guard differential)
  UNGUARDED                          -> warning
  GUARDED                            -> note

Design notes for the next pass (kept deliberately simple for v1):
  * Rules are minted on demand; tune ids/help text later.
  * `--changed-files` does a post-hoc path filter. True seed-scoping
    (analyze only the changed cone) is a core-engine feature, not here.
  * Everything comes from public query output, so this stays OSS-clean.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shlex
import subprocess
import sys
from typing import Any, Dict, List, Optional

SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
INFO_URI = "https://github.com/UnboundCompute/lachesis"
DEFAULT_QUERY_TIMEOUT_SECONDS = 300

# Guard status -> (ruleId, SARIF level, one-line rule description)
RULES: Dict[str, Dict[str, str]] = {
    "unguarded-differential": {
        "id": "lachesis/unguarded-sink-differential",
        "level": "error",
        "desc": "Untrusted input reaches a sink with no authorization check, "
                "while a sibling function guards the identical sink.",
    },
    "unguarded": {
        "id": "lachesis/unguarded-sink",
        "level": "warning",
        "desc": "Untrusted input reaches a sink with no authorization check on the path.",
    },
    "guarded": {
        "id": "lachesis/guarded-sink",
        "level": "note",
        "desc": "Untrusted input reaches a sink, but the path passes an authorization check.",
    },
    "reachable": {
        "id": "lachesis/reachable-sink",
        "level": "warning",
        "desc": "Untrusted input reaches a sink; guard status could not be determined.",
    },
}


def normalize_uri(path: str) -> str:
    """Normalize separators and optional ``./`` prefixes without changing names.

    ``str.lstrip('./')`` is tempting but removes every leading dot, which corrupts
    legitimate hidden paths such as ``.github/workflows/scan.yml``. Keep parent
    traversals and hidden components intact so filters remain lossless.
    """
    path = path.replace(os.sep, "/")
    while path.startswith("./"):
        path = path[2:]
    return path or "."


def run_query(query_cmd: List[str], graph: str, *args: str,
              timeout: int = DEFAULT_QUERY_TIMEOUT_SECONDS) -> Dict[str, Any]:
    completed = subprocess.run(
        [*query_cmd, "--format", "json", graph, *args],
        text=True, capture_output=True, check=True, timeout=timeout,
    )
    return json.loads(completed.stdout)


def classify(guard: Dict[str, Any]) -> str:
    status = (guard.get("status") or "").upper()
    if status == "UNGUARDED":
        return "unguarded-differential" if guard.get("differential_siblings") else "unguarded"
    if status == "GUARDED":
        return "guarded"
    return "reachable"


def rel_uri(path: Optional[str], repo_root: Optional[str]) -> Optional[str]:
    """Normalize a file path to a repo-root-relative POSIX uri for SARIF."""
    if not path:
        return None
    if os.path.isabs(path) and repo_root:
        try:
            path = os.path.relpath(path, repo_root)
        except ValueError:
            pass
    return normalize_uri(path)


def step_location(step: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    loc = (step.get("locator") or {}).get("location") or {}
    # Prefer the absolute path so rel_uri can rebase it on the repo root; this keeps
    # SARIF uris repo-root-relative even when `source` is a subdirectory (the query's
    # own `file` is relative to the analyzed source dir, not the repo root).
    return {
        "file": loc.get("absolute_file") or loc.get("file"),
        "line": loc.get("start_line"),
    }


def sarif_location(uri: Optional[str], line: Optional[int], message: Optional[str] = None) -> Dict[str, Any]:
    region: Dict[str, Any] = {}
    if line:
        region["startLine"] = int(line)
    phys: Dict[str, Any] = {"artifactLocation": {"uri": uri or "<unknown>"}}
    if region:
        phys["region"] = region
    out: Dict[str, Any] = {"physicalLocation": phys}
    if message:
        out["message"] = {"text": message}
    return out


def finding_fingerprint(rule_id: str, handler: str, sinks: str,
                        steps: List[Dict[str, Any]], repo_root: Optional[str]) -> str:
    """Return a stable identity that does not change when line numbers move.

    The sink line remains the SARIF anchor, but durable lifecycle systems need an
    identity that survives harmless edits above the finding. Use normalized source
    and sink paths plus labels and rule semantics; retain the engine path id as a
    separate diagnostic fingerprint for exact witness tracing.
    """
    endpoints = []
    for step in (steps[0], steps[-1]):
        location = step_location(step)
        endpoints.append({
            "file": rel_uri(location["file"], repo_root),
            "label": step.get("label") or "",
            "kind": step.get("kind") or "",
        })
    payload = json.dumps({
        "rule": rule_id,
        "handler": handler,
        "sinks": sinks,
        "endpoints": endpoints,
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_result(
    path_query: Dict[str, Any],
    detail: Dict[str, Any],
    repo_root: Optional[str],
) -> Optional[Dict[str, Any]]:
    summary = detail.get("summary") or {}
    guard = summary.get("guard") or {}
    steps = (detail.get("sections") or {}).get("path") or []
    if not steps:
        return None

    kind = classify(guard)
    rule = RULES[kind]

    label = path_query.get("label") or detail.get("focus", {}).get("label") or "tainted flow"
    handler = guard.get("handler_label") or "handler"
    sinks = ", ".join(guard.get("sink_names") or []) or "sink"
    siblings = ", ".join(guard.get("differential_siblings") or [])

    # Anchor at the sink (last path step); fall back to the guard's handler location.
    sink_loc = step_location(steps[-1])
    sink_uri = rel_uri(sink_loc["file"], repo_root)
    sink_line = sink_loc["line"]
    if not sink_uri:
        sink_uri = rel_uri(guard.get("file"), repo_root)
        sink_line = guard.get("line")
    if not sink_uri:
        # Nothing to anchor the finding to; SARIF requires a valid uri, so skip it
        # rather than emit an invalid "<unknown>" location.
        return None

    msg = f"Tainted flow reaches `{sinks}` in `{handler}`: {(guard.get('status') or 'REACHABLE')}. Flow: {label}."
    if siblings:
        msg += f" Sibling `{siblings}` guards the same sink (guard differential)."
    confidence = guard.get("confidence")
    if confidence:
        msg += f" [confidence: {confidence}]"

    # Full flow as a SARIF codeFlow so the PR view can walk source -> sink.
    thread_locs = []
    for st in steps:
        sl = step_location(st)
        uri = rel_uri(sl["file"], repo_root)
        if not uri:
            # A step with no resolvable file would emit an invalid uri; skip it.
            continue
        thread_locs.append({
            "location": sarif_location(
                uri, sl["line"],
                f"{st.get('kind', 'step')}: {st.get('label', '')}".strip(),
            )
        })

    result: Dict[str, Any] = {
        "ruleId": rule["id"],
        "level": rule["level"],
        "message": {"text": msg},
        "locations": [sarif_location(sink_uri, sink_line)],
        "partialFingerprints": {
            "lachesisFinding": finding_fingerprint(rule["id"], handler, sinks, steps, repo_root),
            "lachesisPathId": path_query.get("id", ""),
        },
    }
    finding_id = result["partialFingerprints"]["lachesisFinding"]
    result["properties"] = {
        "lachesisFinding": {
            "schema_version": "0.1",
            "finding_id": finding_id,
            "status": "lead",
            "analysis": {
                "projection": "security-paths",
                "confidence": confidence or "unresolved",
                "limitations": [],
            },
            "locations": result["locations"],
            "witness": {
                "steps": steps,
                "guards": {
                    "status": guard.get("status") or "UNRESOLVED",
                    "differential_siblings": guard.get("differential_siblings") or [],
                },
            },
        }
    }
    if thread_locs:
        result["codeFlows"] = [{"threadFlows": [{"locations": thread_locs}]}]
    return result


def collect_paths(query_cmd: List[str], graph: str,
                  timeout: int = DEFAULT_QUERY_TIMEOUT_SECONDS) -> List[Dict[str, Any]]:
    """Return [{path_query, detail}] for every reachable path.

    Prefers the batch `security-paths` query: it loads and materializes the graph
    once, so N findings cost one graph load instead of N. Falls back to per-path
    `security-path` calls when the installed engine predates the batch command
    (the Action may install an older `lachesis-ref`).
    """
    try:
        batch = run_query(query_cmd, graph, "security-paths", timeout=timeout)
        entries = batch.get("paths")
        if entries is not None:
            return [
                {"pq": {"id": e.get("id"), "label": e.get("label")},
                 "detail": e.get("detail") or {}}
                for e in entries
            ]
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        pass  # older engine: fall back below
    overview = run_query(query_cmd, graph, "overview", timeout=timeout)
    security = (overview.get("manifest") or {}).get("security") or {}
    return [
        {"pq": pq, "detail": run_query(query_cmd, graph, "security-path", pq["id"], timeout=timeout)}
        for pq in (security.get("path_queries") or [])
    ]


def build_sarif(
    graph: str,
    query_cmd: List[str],
    repo_root: Optional[str],
    changed: Optional[set],
    excluded: Optional[List[str]] = None,
    query_timeout: int = DEFAULT_QUERY_TIMEOUT_SECONDS,
    provenance: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    used_rules: Dict[str, Dict[str, str]] = {}
    # One taint sink can be reached by many distinct witness paths, so the query
    # yields several path slices that anchor to the same (rule, file, line) with
    # the same message. Emitting each as its own SARIF result would post a stack
    # of identical PR comments on one line. Collapse them to the first occurrence;
    # a genuinely different finding differs by rule, file, or line.
    seen: set = set()
    for entry in collect_paths(query_cmd, graph, timeout=query_timeout):
        res = build_result(entry["pq"], entry["detail"], repo_root)
        if res is None:
            continue
        loc = res["locations"][0]["physicalLocation"]
        uri = loc["artifactLocation"]["uri"]
        if changed is not None and uri not in changed:
            continue
        if is_excluded(uri, excluded):
            continue
        anchor = (res["ruleId"], uri, loc.get("region", {}).get("startLine"))
        if anchor in seen:
            continue
        seen.add(anchor)
        results.append(res)
        for meta in RULES.values():
            if meta["id"] == res["ruleId"]:
                used_rules[meta["id"]] = meta

    rules = [
        {
            "id": meta["id"],
            "name": meta["id"].split("/")[-1].replace("-", " ").title().replace(" ", ""),
            "shortDescription": {"text": meta["desc"]},
            "defaultConfiguration": {"level": meta["level"]},
            "helpUri": INFO_URI,
        }
        for meta in used_rules.values()
    ]

    properties: Dict[str, str] = {
        "analysis_projection": "security-paths",
    }
    for key in ("engine_sha", "catalog_sha", "toolchain_fingerprint"):
        if provenance and provenance.get(key):
            properties[key] = provenance[key]

    return {
        "$schema": SCHEMA,
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "Lachesis",
                "informationUri": INFO_URI,
                "rules": rules,
                "properties": properties,
            }},
            "results": results,
        }],
    }


def load_changed(args: argparse.Namespace) -> Optional[set]:
    raw: List[str] = []
    if args.changed_from_file:
        with open(args.changed_from_file) as fh:
            raw.extend(fh.read().split())
    for chunk in args.changed_files or []:
        raw.extend(chunk.replace(",", " ").split())
    if not raw:
        return None
    return {normalize_uri(p) for p in raw if p.strip()}


def load_excluded(args: argparse.Namespace) -> List[str]:
    """Normalize the --exclude patterns to repo-root-relative POSIX form."""
    raw: List[str] = []
    for chunk in args.exclude or []:
        raw.extend(chunk.replace(",", " ").split())
    return [normalize_uri(p).rstrip("/") for p in raw if p.strip()]


def is_excluded(uri: str, patterns: Optional[List[str]]) -> bool:
    """True if a finding's file uri sits under, equals, or globs an excluded path.

    A bare directory (``a/b/fixtures``) drops everything beneath it; a glob
    (``**/fixtures/**``, ``*.min.js``) is matched with fnmatch. This is a report
    filter: the excluded code is still analyzed, its findings just aren't emitted.
    """
    if not patterns:
        return False
    for pat in patterns:
        if uri == pat or uri.startswith(pat + "/") or fnmatch.fnmatch(uri, pat):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Render Lachesis security findings as SARIF 2.1.0.")
    ap.add_argument("graph", help="path to the .kuzu store built by lachesis-analyze")
    ap.add_argument("-o", "--output", default="-", help="SARIF output file (default: stdout)")
    ap.add_argument("--repo-root", default=os.environ.get("GITHUB_WORKSPACE") or os.getcwd(),
                    help="root the SARIF uris are relative to (default: $GITHUB_WORKSPACE or cwd)")
    default_query = shlex.join([sys.executable, "-m", "lachesis.cli.query"])
    ap.add_argument("--query-cmd", default=default_query,
                    help=f"how to invoke the query CLI (default: {default_query!r})")
    ap.add_argument("--changed-files", action="append",
                    help="only report findings in these files (repeatable / comma-separated)")
    ap.add_argument("--changed-from-file", help="read the changed-file list from this path")
    ap.add_argument("--exclude", action="append",
                    help="drop findings under these paths/globs, e.g. a fixtures or "
                         "vendor dir (repeatable / comma-separated)")
    ap.add_argument("--query-timeout", type=int, default=DEFAULT_QUERY_TIMEOUT_SECONDS,
                    help="maximum seconds for each graph query")
    ap.add_argument("--engine-sha", help="engine commit recorded in SARIF provenance")
    ap.add_argument("--catalog-sha", help="Atropos commit recorded in SARIF provenance")
    ap.add_argument("--toolchain-fingerprint", help="toolchain fingerprint recorded in SARIF provenance")
    args = ap.parse_args()

    if args.query_timeout <= 0:
        ap.error("--query-timeout must be a positive integer")

    query_cmd = shlex.split(args.query_cmd)
    changed = load_changed(args)
    excluded = load_excluded(args)
    sarif = build_sarif(
        args.graph, query_cmd, args.repo_root, changed, excluded,
        query_timeout=args.query_timeout,
        provenance={
            "engine_sha": args.engine_sha or "",
            "catalog_sha": args.catalog_sha or "",
            "toolchain_fingerprint": args.toolchain_fingerprint or "",
        },
    )

    text = json.dumps(sarif, indent=2)
    n = len(sarif["runs"][0]["results"])
    if args.output == "-":
        print(text)
    else:
        with open(args.output, "w") as fh:
            fh.write(text)
    print(f"lachesis: wrote {n} finding(s) to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
