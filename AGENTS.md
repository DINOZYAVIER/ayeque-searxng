# ayeque-searxng

Public AGPL source for the pinned AYEQUE presentation layer applied to one
exact SearXNG release.

## Files

- `Dockerfile` derives the runtime from the exact upstream image digest.
- `release.json` records upstream, theme, public-source and asset identities.
- `install_theme.py` applies fail-closed template changes and the source offer.
- `kiwix.py` is the bounded adapter for four private Kiwix Wikipedia
  archives, each in two engines: `mode = search` (full-text `/search` XML) and
  `mode = suggest` (`/suggest` JSON, titles that start with the query); it must
  never expose its internal origin in result URLs.
- `security-requirements.in` and `security-requirements.txt` pin the narrow
  dependency-only repairs applied to the unchanged upstream image. Keep every
  wheel hash locked and never add an unreviewed transitive upgrade.
- `ayeque.css` and the PNG/WebP files are locally served presentation assets.
- `candidate-settings.yml` is synthetic test configuration, never production
  configuration.
- `scripts/check.sh` validates the repository and template patch contract.
- `scripts/test_kiwix_engine.py` runs synthetic adapter security/URL tests.
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
- Keep Kiwix search on the public `/search` XML API and the `/suggest` JSON API,
  private HTTP addresses, fixed language aliases and same-origin HTTPS result
  URLs.
- Publish the generated complete source archive and checksum with every tag
  used by a deployed image.
