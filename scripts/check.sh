#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
if [ -z "${PYTHON_BIN:-}" ]; then
  for candidate in /usr/bin/python3 "/etc/profiles/per-user/$(id -un)/bin/python3"; do
    if [ -x "$candidate" ]; then
      PYTHON_BIN=$candidate
      break
    fi
  done
  PYTHON_BIN=${PYTHON_BIN:-$(command -v python3)}
fi

"$PYTHON_BIN" - "$REPO_ROOT" <<'PY'
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
required = (
    ".gitignore", "AGENTS.md", "README.md", "LICENSE", "NOTICE.md",
    "Dockerfile", "release.json", "install_theme.py", "ayeque.css",
    "ayeque-logo.webp", "favicon.png", "192.png", "512.png",
    "candidate-settings.yml", "scripts/check.sh",
    "scripts/package_corresponding_source.sh",
)
missing = [name for name in required if not (root / name).is_file()]
if missing:
    raise SystemExit("missing required files: " + ", ".join(missing))

release = json.loads((root / "release.json").read_text(encoding="utf-8"))
if release.get("schema") != "ayeque.searxng_theme_release.v2":
    raise SystemExit("unexpected release schema")

dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
if dockerfile.count("FROM " + release["upstream"]["image"]) != 1:
    raise SystemExit("Dockerfile does not contain the exact upstream image pin")
if dockerfile.count('art.ayeque.theme.revision="' + release["theme_revision"] + '"') != 1:
    raise SystemExit("Dockerfile theme revision differs from release.json")
if dockerfile.count('org.opencontainers.image.source="' + release["public_source"]["repository"] + '"') != 1:
    raise SystemExit("Dockerfile public source label differs from release.json")

installer = (root / "install_theme.py").read_text(encoding="utf-8")
for relative, digest in release["template_preimages"].items():
    if installer.count(f'"{relative}": "{digest}"') != 1:
        raise SystemExit(f"installer does not contain the recorded preimage for {relative}")
source_url = release["public_source"]["release"]
if installer.count(source_url) != 1:
    raise SystemExit("installer does not contain exactly one immutable source URL")

for name, expected in release["assets"].items():
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"asset hash mismatch for {name}: {actual}")

css = (root / "ayeque.css").read_text(encoding="utf-8")
if re.search(r"(?:@import\s+|url\(\s*['\"]?)https?://", css, re.I):
    raise SystemExit("theme CSS contains a remote runtime dependency")
for marker in (":focus-visible", "prefers-reduced-motion", ".ayeque-source-footer"):
    if marker not in css:
        raise SystemExit(f"theme CSS is missing {marker}")

for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "dist" in path.parts:
        continue
    if path.suffix.lower() in {".png", ".webp"} or path.name == "LICENSE":
        continue
    text = path.read_text(encoding="utf-8", errors="strict")
    forbidden = (
        "10.0." + "0.16", "/home/" + "dinozyavier",
        "github" + "_pat_", "gh" + "p_",
        "BEGIN OPENSSH " + "PRIVATE KEY", "BEGIN " + "PRIVATE KEY",
        "cookie" + "_secret", "client" + "_secret",
    )
    for marker in forbidden:
        if marker in text:
            raise SystemExit(f"forbidden private marker in {path.relative_to(root)}")

if hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest() != "57c8ff33c9c0cfc3ef00e650a1cc910d7ee479a8bc509f6c9209a7c2a11399d6":
    raise SystemExit("LICENSE differs from the exact upstream AGPL-3.0 text")

print("repository=ok")
print("upstream=" + release["upstream"]["version"])
print("theme_revision=" + release["theme_revision"])
print("source_release=" + source_url)
PY

"$PYTHON_BIN" "$REPO_ROOT/install_theme.py" --self-test
printf 'installer_self_test=ok\n'
