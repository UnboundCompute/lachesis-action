# Lachesis Security Scan

**Find the endpoint that forgot the authorization check, the one its sibling remembered.**

A GitHub Action that builds a compiler-precise code property graph of your repo,
traces untrusted input to dangerous sinks, and posts what it finds straight onto
the pull request as **Lachesis[bot]** — inline on the changed lines, leveled by
guard status. The analysis runs entirely on your own runner.

[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Lachesis-8250df?logo=github)](https://github.com/marketplace/actions/lachesis-security-scan)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

Security reporting guidance is in [`SECURITY.md`](./SECURITY.md). Contributor and
local-gate guidance is in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

For local development and CI, run the same dependency-free gate with `make check`.

---

## Why it's different

Most scanners pattern-match one function at a time. Lachesis reasons about your code
as a graph, so it can see something a line-by-line tool can't: **two functions that
reach the same sink, where one authorizes the caller and one doesn't.**

That guard differential is the classic missing-authorization bug. `getInvoice`
checks the session, `getDocument` forgot to, and it's exactly the finding Lachesis
ranks as an `error`:

> **Untrusted input reaches a sink with no authorization check, while a sibling
> function guards the identical sink.**

<!-- Render demo/demo.tape with `vhs demo/demo.tape` and commit demo/demo.gif, then: -->
<!-- ![demo](./demo/demo.gif) -->

## See it find the bug

Three commands: build the graph, ask for the overview, then look at the handler
that forgot the check.

```console
$ lachesis-analyze ./project graph.kuzu --prune --incremental
   building code graph... done

$ lachesis-query graph.kuzu overview --format text | grep -i 'guard differential'
Guard differentials: 1

$ lachesis-query graph.kuzu handler-security getDocument --format text
handler: getDocument
status: UNGUARDED
differential_siblings: ["getInvoice"]
  getInvoice guards the identical sink; getDocument does not.
```

The Action runs exactly this on every PR and posts the `UNGUARDED` sibling as an
`error` comment on the offending line, signed by **Lachesis[bot]**.

## Quickstart

Two things are needed: install the **Lachesis GitHub App** on the repo (or org),
then add the workflow.

1. Install the app: **[github.com/apps/lachesis-security](https://github.com/apps/lachesis-security)** →
   click **Install** → pick the repos it may comment on. (This is the one-time step
   that gives the bot permission to post; the scan itself still runs in your CI.)
2. Add `.github/workflows/lachesis.yml`:

```yaml
name: lachesis
on:
  pull_request:

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write          # lets the action prove the repo to the Lachesis app
    steps:
      - uses: actions/checkout@v4
      - uses: UnboundCompute/lachesis-action@v1.0.3
        with:
          source: "."
          fail-on: "error"     # optional: fail the check on guard differentials
```

Open a PR and the findings appear as inline comments from **Lachesis[bot]** on the
lines they touch, with a summary at the top of the review.

### Blocking merge on findings

`fail-on` makes the scan **job** fail at or above a level (`note` / `warning` /
`error`) — the bot still posts its comments first, then the check turns red. A red
check only *blocks merge* if you also make the `scan` job a **required status check**
in the repo's **Settings → Branches → Branch protection** (or a ruleset). Without
that, `fail-on` is a visible signal but not a gate.

## What you get

Each tainted source-to-sink path becomes one PR comment, anchored at the sink,
carrying the data-flow that reaches it, and leveled by guard status:

| Level | Rule | Meaning |
|---|---|---|
| 🔴 `error` | `lachesis/unguarded-sink-differential` | Unguarded sink **and** a sibling guards the identical sink: a guard differential. |
| 🟡 `warning` | `lachesis/unguarded-sink` | Untrusted input reaches a sink with no authorization check on the path. |
| ⚪ `note` | `lachesis/guarded-sink` | The path reaches a sink but passes an authorization check. |

Findings are **leads, not verdicts**: high-signal places to look first, not confirmed vulns.

Languages: **Python, TypeScript/JavaScript, and C.**

## Inputs

| Input | Default | Notes |
|---|---|---|
| `source` | `.` | Directory to analyze. |
| `python-version` | `3.11` | Python runtime for the engine. Override only with a version tested against the Lachesis/Kùzu dependency set. |
| `kuzu-buffer-pool-size` | `1073741824` | Kùzu buffer-pool ceiling in bytes. Raise it for very large trees; lower it on constrained runners. |
| `exclude` | `` | Drop findings under these paths/globs (e.g. a `fixtures` or `vendor` dir). |
| `changed-files` | `` | If set, only report findings in these files. |
| `analyze-args` | `--prune --incremental` | Flags for the graph build. |
| `c-jobs` | empty (adaptive) | Optional Clang frontend concurrency override; use `1` to cap memory or `2` for a measured medium-tree runner. |
| `frontend-timeout` | `300` | Maximum seconds for one Lachesis frontend invocation. |
| `query-timeout` | `300` | Maximum seconds for one SARIF graph query. |
| `build-timeout` | `1800` | Maximum seconds for the complete graph build. |
| `lachesis-ref` | `main` | Lachesis release tag to install. Use a reviewed tag for reproducibility. |
| `atropos-repo` | `https://github.com/UnboundCompute/atropos` | Atropos catalog repository to load. |
| `atropos-ref` | `main` | Atropos release tag. Use a reviewed tag for reproducible findings. |
| `fail-on` | `none` | Fail the check at `note` / `warning` / `error` and above. Other values fail configuration validation. |
| `sarif-file` | `lachesis.sarif` | Output path for the intermediate SARIF report. |
| `report-endpoint` | `` | Hosted Lachesis poster URL. Leave at the default unless you self-host the poster. |
| `oidc-audience` | `lachesis-bot` | Audience requested for the OIDC token; must match the poster. |

The Action validates its resource limits, output path, threshold values, and
quoted analyzer arguments before cloning or installing anything. Invalid configuration
fails with exit code 2 and an actionable message, so a misconfigured workflow does not
spend runner time on a partial scan.

Dependency installation is noninteractive and uses bounded network behavior: Git aborts
transfers below 1,000 bytes/second for 60 seconds, and pip uses a 60-second socket
timeout. Credential prompts and pip's version-check request cannot leave a runner waiting.

## How posting works

The scan runs entirely in your CI. When it finds something, the action requests a
short-lived GitHub Actions **OIDC token** (this is why the workflow needs
`permissions: id-token: write`) and sends the SARIF plus the PR context to the
hosted Lachesis poster. The poster verifies the token proves the run really came
from your repository, then posts the review as the **Lachesis GitHub App**.

Only the findings leave your runner — the SARIF report and the PR number, over
which the poster has write access solely to comment. No source checkout, no API
key of yours, and no long-lived secret is sent; the app's own credentials never
touch your CI. If the poster is unreachable the step warns and the run continues,
so posting never blocks your pipeline (the `fail-on` gate reads the SARIF locally,
independent of posting).

## Reproducible production use

Set `lachesis-ref` to a reviewed Lachesis release tag in production workflows. The
default `main` ref is intended for development and follows engine changes. Set
`atropos-ref` to a reviewed catalog release tag as well. The Action itself is released
under its own `v1` tag; release verification and
rollback guidance are in [`RELEASING.md`](./RELEASING.md).

## How it works

1. Installs the [Lachesis engine](https://github.com/UnboundCompute/lachesis) (uses a blob-filtered checkout, then vendors its TypeScript frontend; pure Python, no `npm`).
2. Installs and validates the [Atropos catalog](https://github.com/UnboundCompute/atropos) from a blob-filtered checkout,
   exporting `ATROPOS_ROOT` so model binding is explicit rather than dependent on a
   sibling checkout.
3. Restores the incremental frontend bundles when the source, lockfiles, engine, and catalog refs match, then
   builds a light pruned graph; the data-flow tier folds lazily. The cache is only a
   compile reuse hint: Lachesis still validates file digests and output-affecting flags.
4. Traces every source-to-sink path, classifies its guard status, and renders SARIF.
5. Posts the findings on the PR as **Lachesis[bot]** via the hosted poster.

The analysis stays on your runner; only the findings are sent onward to be posted.

## Add the badge to your repo

Show your project runs Lachesis:

```markdown
[![Lachesis](https://img.shields.io/badge/security-Lachesis-8250df)](https://github.com/UnboundCompute/lachesis-action)
```

## License

[MIT](./LICENSE). The Action runs in your CI and does not link into or relicense
your code. (The Lachesis engine it installs is separately licensed.)
