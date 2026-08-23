# scripts/

Public, secret-free checks and corresponding-source packaging for the exact
AYEQUE SearXNG overlay.

- `check.sh` validates release identities, assets and adapter tests.
- `test_kiwix_engine.py` exercises the Kiwix XML engine without production
  network access or SearXNG settings.
- `package_corresponding_source.sh` builds the complete AGPL source archive.

The build may install only the exact hashed packages in
`security-requirements.txt` using the pinned uv image recorded by the
Dockerfile and release metadata.

Keep fixtures synthetic and inline. Never add queries, internal addresses,
credentials, production settings or response captures.
