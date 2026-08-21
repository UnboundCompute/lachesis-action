# Releasing the Lachesis Action

The Action is a composite action and is released independently from the Lachesis
engine. Keep the Action tag stable while engine versions advance through the
`lachesis-ref` input.

Every release must update [`VERSION`](VERSION) and have a matching heading in
[`CHANGELOG.md`](CHANGELOG.md). The
release workflow accepts either `## [VERSION]` or `## VERSION`, so the existing `v1`
major tag and future semantic-version tags use the same gate.

The default runtime is Python 3.11 because it is the interpreter used by the Action
gate and the Lachesis release verification job. If changing `python-version`, verify
the Kùzu wheel and full Action workflow on that interpreter before publishing a tag.

## Verification

Run the dependency-free Action gate:

```bash
make check
```

For a release candidate, run the example workflow against a reviewed Lachesis release tag and
verify that the generated SARIF passes GitHub's SARIF upload action. Check both an empty
report and a fixture with a guard differential, including `--changed-files` and
`--exclude` filters.

Every `v*` tag also runs the dependency-free release verification workflow. It checks
the composite-action metadata and test suite but does not publish or move any tag.

## Tagging and rollback

Create an annotated `vMAJOR` or `vMAJOR.MINOR.PATCH` tag only after the release candidate
workflow is green. The workflow checks exact semantic tags against `VERSION` and checks
major tags against its major component.
Production workflows should set `lachesis-ref` to a reviewed Lachesis release tag;
the Action's moving default exists for development convenience and must not be used as
an audit reproducibility boundary. Never overwrite a published tag—cut a patch tag and
retain the previous tag for rollback.
