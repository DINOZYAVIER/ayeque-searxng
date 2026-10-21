# AYEQUE SearXNG

This repository contains the AYEQUE theme and reproducible modification layer
for the SearXNG instance at `search.ayeque.art`.

The current release derives from SearXNG `2026.10.19+81371861f` at commit
`81371861f67226091d1c4df2e3908a11d3b54eb9`. The upstream image, source archive,
template preimages and local assets are pinned in `release.json`.

The AYA-34 overlay also installs the bounded `kiwix.py` engine used for the
private four-language Wikipedia library. Runtime addresses and production
settings are deliberately excluded from this public source repository.
The derived image applies three exact hash-locked dependency-only upgrades
recorded in `security-requirements.txt`; the upstream SearXNG revision and
templates remain unchanged.

## Verify

```sh
scripts/check.sh
```

## Build the runtime image

```sh
docker build --tag ayeque-searxng:2026.10.19-81371861f-aya35.1 .
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
