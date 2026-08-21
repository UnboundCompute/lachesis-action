# Releasing the Lachesis Action

The Action is a composite action and is released independently from the Lachesis
engine. Keep the Action tag stable while engine versions advance through the
`lachesis-ref` input.

The default runtime is Python 3.11 because it is covered by the engine and Action
test matrix. If changing `python-version`, verify the Kùzu wheel and full Action
workflow on that interpreter before publishing a tag.

## Verification

Run the dependency-free SARIF tests:

```bash
python3 -m unittest test_sarif_export.py
```

For a release candidate, run the example workflow against a pinned Lachesis commit and
verify that the generated SARIF passes GitHub's SARIF upload action. Check both an empty
report and a fixture with a guard differential, including `--changed-files` and
`--exclude` filters.

Every `v*` tag also runs the dependency-free release verification workflow. It checks
the composite-action metadata and test suite but does not publish or move any tag.

## Tagging and rollback

Create an annotated `vMAJOR` tag only after the release candidate workflow is green.
Production workflows should pin `lachesis-ref` to an immutable Lachesis tag or SHA;
the Action's moving default exists for development convenience and must not be used as
an audit reproducibility boundary. Never overwrite a published tag—cut a patch tag and
retain the previous tag for rollback.
