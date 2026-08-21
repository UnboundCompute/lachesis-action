# Security Policy

Do not disclose Action vulnerabilities in public issues or pull requests. Use
GitHub Private Vulnerability Reporting and include the Action tag or commit, the
workflow inputs, a minimal reproducer, and the impact.

In scope are unsafe shell/input handling, unintended code or credential exposure
on runners, SARIF boundary mistakes, and dependency or cache behavior that crosses
repository boundaries. The Action runs on the caller's runner; never include
secrets or private source in a report.

Production users should pin both the Action tag/SHA and the `lachesis-ref` and
`atropos-ref` inputs.
