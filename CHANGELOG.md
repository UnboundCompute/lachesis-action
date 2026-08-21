# Changelog

All notable changes to the Lachesis GitHub Action are recorded here.

## Unreleased

- Added a `make check` developer gate; CI, release verification, and contributor
  instructions now use the same command.
- Action preflight now rejects empty Lachesis and Atropos refs before starting
  network checkouts.
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
