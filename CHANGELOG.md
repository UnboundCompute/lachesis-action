# Changelog

All notable changes to the Lachesis GitHub Action are recorded here.

## Unreleased

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
