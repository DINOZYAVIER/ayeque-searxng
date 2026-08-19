# AYEQUE SearXNG

This repository contains the AYEQUE theme and reproducible modification layer
for the SearXNG instance at `search.ayeque.art`.

The current release derives from SearXNG `2026.3.29+7ac4ff39f` at commit
`7ac4ff39fee4cdde223dbab6a83af9c26b56366e`. The upstream image, source archive,
template preimages and local assets are pinned in `release.json`.

## Verify

```sh
scripts/check.sh
```

## Build the runtime image

```sh
docker build --tag ayeque-searxng:2026.3.29-aya29.1 .
```

The build intentionally fails if any patched upstream template differs from
the recorded preimage.

## Build the complete source release

```sh
scripts/package_corresponding_source.sh
```

The command downloads and verifies the exact upstream source, then creates a
complete source archive and checksum under `dist/`. Set
`SEARXNG_UPSTREAM_ARCHIVE` to an already downloaded archive for an offline
build.

Production configuration, authentication secrets, logs and user data are not
part of this repository and are not required to build the covered version.

## License

SearXNG and these modifications are distributed under the GNU Affero General
Public License, version 3. See `LICENSE` and `NOTICE.md`.

