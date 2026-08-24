# Changelog

All notable changes to the Lachesis GitHub Action are recorded here.

## Unreleased

- Add opt-in `candidate-report: census` output for Atropos-backed obligation
  coverage in the GitHub Actions job summary.
- Expose generated SARIF and candidate-census paths as composite-action outputs so
  callers can archive or upload artifacts through generic CI integrations.
- Pin development defaults to the reviewed Lachesis `v0.1.7` and Atropos `v1.7.1`
  releases.
- Record the analysis projection, engine/catalog commits, and toolchain fingerprint
  in SARIF driver properties.

## [1.0.5]

- De-duplicate inline comments: when one sink is reached by several distinct
  taint witnesses, the finding is posted once per `(rule, file, line)` instead of
  once per witness path, so the bot no longer stacks identical comments on a line.

## [1.0.4]

- Deliver findings as inline pull-request comments from the Lachesis GitHub App
  (**Lachesis[bot]**) via the hosted poster, using a short-lived GitHub Actions OIDC
  token to prove the run's repository. This replaces the GitHub code-scanning upload
  as the single delivery path.
- Remove the `upload` and `branded-comments` inputs; the workflow now requires
  `permissions: id-token: write` instead of `security-events: write`.
- Point `report-endpoint` at the hosted poster by default so the App path works with
  no extra configuration.
- Feature `fail-on: error` for blocking, and document that a hard merge gate also
  needs the `scan` job marked as a required status check.
- When the Lachesis app is not installed on the repository, surface a one-click
  install message instead of a raw error, and continue non-fatally.

## [1.0.3]

- Update the example-workflow regression test for the current reviewed Lachesis tag.

## [1.0.2]

- Document release-tag-only engine and catalog inputs and use the current reviewed
  release tags in the example workflow.

## [1.0.1]

- Release the merged `main` tag-reference and production-readiness updates.

- Added a machine-readable `VERSION` file; release CI now checks semantic tags against
  it and prevents a major tag from crossing release lines.
- The local Action gate now checks that `VERSION` and the stable changelog heading stay
  synchronized before a release is tagged.
- Action runs now warn when engine or catalog refs remain on mutable `main`, while
  retaining that default for development convenience.
- Dependency installation now disables pip prompts and version checks and applies a
  60-second network timeout, preventing unattended setup from hanging on a runner.
- Dependency Git checkouts now abort stalled HTTP transfers after 60 seconds below the
  low-speed threshold, bounding another setup-time hang mode.

- Reject `analyze-args` values that try to override the Action's `frontend-timeout`,
  keeping the documented execution bound effective for unattended scans.
- Bound SARIF graph queries with the configurable `query-timeout` input so a stalled
  query cannot leave an Action step waiting indefinitely.
- Added a configurable 30-minute default `build-timeout`; expired graph builds now
  terminate their whole process group instead of leaving an Action step running forever.
- Corrected release guidance to describe the actual Python 3.11 verification jobs,
  rather than implying the Action itself runs a Python-version matrix.

- Corrected the example workflow so its optional `lachesis-ref` does not suggest
  the Action's `v1.0.0` tag as an engine release; consumers must provide an actual
  reviewed engine release tag.
- Engine and catalog Git checkouts now disable terminal credential prompts so a
  missing credential fails fast instead of hanging a CI runner.
- SARIF path normalization now preserves hidden files and parent components while
  removing only explicit `./` prefixes, keeping changed-file and exclude filters exact.
- Added a `make check` developer gate; CI, release verification, and contributor
  instructions now use the same command.
- Added contributor guidance covering the local gate, pinned workflow refs, and
  release-safe Action changes.
- Action preflight now rejects empty Lachesis and Atropos refs before starting
  network checkouts.
- Ref validation also rejects option-like or whitespace-containing values before
  they reach Git.
- Added an explicit `frontend-timeout` input so Action users can bound each
  analyzer frontend without embedding timeout flags in `analyze-args`.
- The `fail-on` gate now reports readable errors for missing, malformed, or
  structurally invalid SARIF instead of exposing a Python traceback.
- Use shallow ref-aware source clones in the composite action to reduce cold-start
  transfer and checkout cost while retaining branch, tag, and SHA inputs.
- Pin the Action's own workflows and published usage examples to the v1.0.0
  release commit; mutable major tags remain an explicit opt-in.
- Validate Action inputs before installing the engine so malformed thresholds,
  resource limits, paths, or analyzer quoting fail fast with actionable errors.
- Check that the configured source directory exists before installing dependencies,
  avoiding expensive partial runs for checkout/path mistakes.
- Check that the SARIF output's parent directory exists before starting the scan.
- Run the complete dependency-free test suite in CI, release verification, and the
  release checklist rather than only the SARIF exporter test.
- Hardened configurable inputs, dependency checkouts, cache invalidation, and
  partial-clone fallback behavior for production runners.

## [1.0.0]

- First stable composite Action release for GitHub code scanning.
