# Publishing to GitHub Marketplace

This repo is Marketplace-ready: `action.yml` is at the root, has a unique `name`
and a `branding` block, and the `README.md` becomes the listing body.

## One-time publish steps

1. Cut a release tag (see below), then on GitHub open **Releases → Draft a new
   release**. Select the tag.
2. Check **"Publish this Action to the GitHub Marketplace."** (Requires 2FA on the
   account, enable it first if prompted.)
3. Accept the Marketplace agreement.
4. **Categories**, pick:
   - Primary: **Security**
   - Secondary: **Code quality**
5. Publish the release. The listing goes live at
   `https://github.com/marketplace/actions/lachesis-security-scan`.

## Release tagging (do this on THIS repo, not the engine repo)

```bash
git tag -a v1.0.0 -m "Lachesis Security Scan v1.0.0"
git push origin v1.0.0

# Moving major tag consumers pin to; re-point it on every v1.x release:
git tag -f v1 v1.0.0
git push -f origin v1
```

Consumers then use `UnboundCompute/lachesis-action@v1`.

> Reproducibility note: for a locked release, set the `lachesis-ref` default in
> `action.yml` to the engine's stable ref (e.g. its `v1.0.0` tag) at the moment you
> cut this tag, so `@v1` pins both the wrapper and the engine it installs.

## Listing copy (paste-ready)

- **Name:** Lachesis Security Scan
- **Tagline (≤125 chars):** Trace untrusted input to sinks and catch the endpoint
  that forgot the authorization check, inline in GitHub code scanning.
- **Description:** see `README.md` (rendered as the listing body).

## Discoverability checklist

- [ ] Marketplace listing published (Security + Code quality categories)
- [ ] `demo/demo.gif` rendered from `demo/demo.tape` and referenced in the README
- [ ] Added to awesome lists: `awesome-actions`, `awesome-static-analysis`, `awesome-security`
- [ ] README badge snippet shared for consumers to embed
- [ ] Engine repo (`lachesis`) README links here as the official Action
