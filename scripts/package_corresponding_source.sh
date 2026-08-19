#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
RELEASE_FILE="$REPO_ROOT/release.json"
OUTPUT_DIR=${1:-"$REPO_ROOT/dist"}
if [ -z "${PYTHON_BIN:-}" ]; then
  for candidate in /usr/bin/python3 "/etc/profiles/per-user/$(id -un)/bin/python3"; do
    if [ -x "$candidate" ]; then
      PYTHON_BIN=$candidate
      break
    fi
  done
  PYTHON_BIN=${PYTHON_BIN:-$(command -v python3)}
fi

read_release() {
  "$PYTHON_BIN" - "$RELEASE_FILE" "$1" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
for part in sys.argv[2].split("."):
    value = value[part]
print(value)
PY
}

release_tag=$(read_release release_tag)
archive_name=$(read_release public_source.archive_name)
upstream_revision=$(read_release upstream.revision)
upstream_url=$(read_release upstream.source_archive_url)
upstream_sha256=$(read_release upstream.source_archive_sha256)
bundle_name="ayeque-searxng-${release_tag}-source"

mkdir -p "$OUTPUT_DIR"
tmp_dir=$(mktemp -d)
trap 'rm -rf -- "$tmp_dir"' EXIT

upstream_archive=${SEARXNG_UPSTREAM_ARCHIVE:-"$tmp_dir/upstream.tar.gz"}
if [ -z "${SEARXNG_UPSTREAM_ARCHIVE:-}" ]; then
  curl --fail --location --silent --show-error --max-time 180 \
    "$upstream_url" --output "$upstream_archive"
fi
test -f "$upstream_archive" || {
  printf 'missing upstream archive: %s\n' "$upstream_archive" >&2
  exit 1
}
actual_upstream_sha256=$(sha256sum "$upstream_archive" | awk '{print $1}')
test "$actual_upstream_sha256" = "$upstream_sha256" || {
  printf 'upstream source hash mismatch: expected %s, got %s\n' \
    "$upstream_sha256" "$actual_upstream_sha256" >&2
  exit 1
}

bundle_root="$tmp_dir/$bundle_name"
mkdir -p "$bundle_root/upstream-searxng" "$bundle_root/ayeque-overlay/scripts"
tar -xzf "$upstream_archive" -C "$bundle_root/upstream-searxng" --strip-components=1

for path in \
  .gitignore AGENTS.md README.md LICENSE NOTICE.md Dockerfile release.json \
  install_theme.py ayeque.css ayeque-logo.webp favicon.png 192.png 512.png \
  candidate-settings.yml; do
  cp -a "$REPO_ROOT/$path" "$bundle_root/ayeque-overlay/$path"
done
cp -a "$REPO_ROOT/scripts/check.sh" "$bundle_root/ayeque-overlay/scripts/check.sh"
cp -a "$REPO_ROOT/scripts/package_corresponding_source.sh" \
  "$bundle_root/ayeque-overlay/scripts/package_corresponding_source.sh"

cat >"$bundle_root/SOURCE-README.txt" <<EOF
Complete corresponding source for AYEQUE SearXNG ${release_tag}.

upstream-searxng/ contains SearXNG revision ${upstream_revision}.
ayeque-overlay/ contains the AYEQUE modifications and build/install scripts.

See ayeque-overlay/README.md and ayeque-overlay/NOTICE.md.
EOF

(
  cd "$bundle_root"
  find . -type f ! -name MANIFEST.sha256 -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 sha256sum > MANIFEST.sha256
)

archive_path="$OUTPUT_DIR/$archive_name"
(
  cd "$tmp_dir"
  tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner \
    -cf - "$bundle_name" | gzip -n -9 > "$archive_path"
)
archive_sha256=$(sha256sum "$archive_path" | awk '{print $1}')
printf '%s  %s\n' "$archive_sha256" "$archive_name" \
  > "$OUTPUT_DIR/SHA256SUMS"

printf 'source_archive=%s\n' "$archive_path"
printf 'source_sha256=%s\n' "$archive_sha256"
printf 'upstream_sha256=%s\n' "$actual_upstream_sha256"
