# Contributing to the Lachesis Action

The Action is a dependency-free composite action. Changes should keep the
metadata, shell workflow, and standalone Python helpers usable on a clean
GitHub runner.

## Local gate

Run the same gate used by CI and release verification:

```bash
make check
```

It runs the SARIF exporter, input-validation, and findings-gate tests with the
standard library only. Keep diagnostics on stderr and reserve stdout for
machine-readable output where a helper participates in an Action protocol.

## Workflow and release changes

- Keep third-party `uses:` references on reviewed version tags.
- Add or update tests when changing input validation, SARIF filtering, or exit
  behavior.
- Keep the Action's `lachesis-ref` and `atropos-ref` inputs explicit; production
  examples should use reviewed engine/catalog release tags.
- Update [`CHANGELOG.md`](./CHANGELOG.md) for user-visible behavior.

For a tagged release, follow [`RELEASING.md`](./RELEASING.md) after the local
gate is green.
