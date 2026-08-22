"""Post Lachesis SARIF findings to the hosted poster as Lachesis[bot].

Runs inside the consumer's CI on pull_request. It requests a GitHub Actions
OIDC token (needs `permissions: id-token: write`), then POSTs the SARIF plus the
PR context to the hosted poster. The poster verifies the OIDC token and posts
the review as the Lachesis GitHub App.

This script sends no secrets: the OIDC token is short-lived and repo-scoped, and
the app private key lives only on the poster side.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _fail(msg: str) -> "None":
    print(f"::warning title=Lachesis branded comments::{msg}")
    # Non-fatal: branded comments are an add-on, not the gate. Exit 0 so the
    # scan result (and the code-scanning upload) still stands.
    sys.exit(0)


def _oidc_token(audience: str) -> str:
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    tok = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not tok:
        _fail("id-token unavailable — add 'permissions: id-token: write' to the workflow.")
    req = urllib.request.Request(f"{url}&audience={audience}")
    req.add_header("Authorization", f"bearer {tok}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["value"]


def main() -> None:
    if len(sys.argv) < 2:
        _fail("no SARIF file argument")
    sarif_path = sys.argv[1]

    endpoint = os.environ.get("LACHESIS_REPORT_ENDPOINT", "").strip()
    if not endpoint:
        _fail("report-endpoint not set; skipping branded comments.")

    repository = os.environ.get("GITHUB_REPOSITORY", "")
    pr_number = os.environ.get("GITHUB_PR_NUMBER", "")
    commit_sha = os.environ.get("GITHUB_SHA", "")
    if not repository or not pr_number:
        _fail("missing PR context; branded comments run only on pull_request.")

    try:
        with open(sarif_path, encoding="utf-8") as fh:
            sarif = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"cannot read SARIF: {exc}")

    audience = os.environ.get("LACHESIS_OIDC_AUDIENCE", "lachesis-bot")
    oidc = _oidc_token(audience)

    body = json.dumps(
        {
            "repository": repository,
            "pull_number": int(pr_number),
            "commit_sha": commit_sha,
            "sarif": sarif,
        }
    ).encode()

    req = urllib.request.Request(endpoint, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {oidc}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read() or "{}")
        print(f"lachesis: posted {result.get('posted', '?')} comment(s) as Lachesis[bot]")
    except urllib.error.HTTPError as exc:
        _fail(f"poster returned {exc.code}: {exc.read().decode(errors='replace')}")
    except urllib.error.URLError as exc:
        _fail(f"poster unreachable: {exc}")


if __name__ == "__main__":
    main()
