# ayeque-searxng

Public AGPL source for the pinned AYEQUE presentation layer applied to one
exact SearXNG release.

## Files

- `Dockerfile` derives the runtime from the exact upstream image digest.
- `release.json` records upstream, theme, public-source and asset identities.
- `install_theme.py` applies fail-closed template changes and the source offer.
- `ayeque.css` and the PNG/WebP files are locally served presentation assets.
- `candidate-settings.yml` is synthetic test configuration, never production
  configuration.
- `scripts/check.sh` validates the repository and template patch contract.
- `scripts/package_corresponding_source.sh` creates the complete source release
  containing the exact upstream SearXNG source and this overlay.

## Rules

- Keep this repository public while a deployed covered version points to it.
- Never add production settings, credentials, cookies, queries, logs, private
  hostnames, user information or deployment backups.
- Never replace the upstream digest, revision, source-archive hash or template
  preimage hashes without inspecting that exact upstream and rerunning the
  complete browser, functional and rollback matrix.
- Keep the patch narrow and fail closed when an upstream template changes.
- Keep the visible `Source` offer present on every page using `simple/base.html`.
- Do not add JavaScript, remote fonts, analytics or external runtime assets.
- Publish the generated complete source archive and checksum with every tag
  used by a deployed image.

