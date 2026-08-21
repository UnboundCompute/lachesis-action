# Changelog

All notable changes to the Lachesis GitHub Action are recorded here.

## Unreleased

- Corrected the example workflow so its optional `lachesis-ref` does not suggest
  the Action's `v1.0.0` tag as an engine release; consumers must provide an actual
  immutable engine tag or commit SHA.
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
