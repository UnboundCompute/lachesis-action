# Changelog

All notable changes to the Lachesis GitHub Action are recorded here.

## Unreleased

- Use shallow ref-aware source clones in the composite action to reduce cold-start
  transfer and checkout cost while retaining branch, tag, and SHA inputs.
- Hardened configurable inputs, dependency checkouts, cache invalidation, and
  partial-clone fallback behavior for production runners.

## [1]

- First stable composite Action release for GitHub code scanning.
