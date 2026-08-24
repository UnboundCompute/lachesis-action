# Publishing to GitHub Marketplace

This repo is Marketplace-ready: `action.yml` is at the root, has a unique `name`
and a `branding` block, and the `README.md` becomes the listing body. The current
reviewed Action release is `v1.0.5`.

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
git tag -a v1.0.5 -m "Lachesis Security Scan v1.0.5"
git push origin v1.0.5

# Moving major tag consumers pin to; re-point it on every v1.x release:
git tag -f v1 v1.0.5
git push -f origin v1
```

Consumers should use `UnboundCompute/lachesis-action@v1` for the moving major
channel, or `UnboundCompute/lachesis-action@v1.0.5` when the wrapper itself must
remain fixed.

> Reproducibility note: for a locked release, set the `lachesis-ref` and
> `atropos-ref` inputs to reviewed release tags. Pinning the wrapper
> commit alone does not freeze the engine or model catalog it installs.

## Listing copy (paste-ready)

- **Name:** Lachesis Security Scan
- **Tagline (≤125 chars):** Trace untrusted input to sinks and catch the endpoint
  that forgot the authorization check, posted inline on the PR as Lachesis[bot].
- **Description:** see `README.md` (rendered as the listing body).

## Discoverability checklist

- [ ] Marketplace listing published (Security + Code quality categories)
- [x] `demo/demo.gif` rendered from `demo/demo.tape` and referenced in the README
- [ ] Added to awesome lists: `awesome-actions`, `awesome-static-analysis`, `awesome-security`
- [x] README badge snippet shared for consumers to embed
- [x] Engine repo (`lachesis`) README links here as the official Action
