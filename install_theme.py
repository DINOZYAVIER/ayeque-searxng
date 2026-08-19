#!/usr/bin/env python3
"""Install the AYEQUE theme into one exact SearXNG template revision."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


TEMPLATE_ROOT = Path("/usr/local/searxng/searx/templates")
EXPECTED = {
    "simple/base.html": "6e70d235e7297a32c223441ce2e22a7f2569959d164f251c4c4ead00907ac40d",
    "simple/index.html": "91d2065c452099c023ab1910885bacdab9aed6dc049e954bf1ac96eca679fd96",
    "simple/page_with_header.html": "5cfc88b74e55b22b7d69be53e6fb2b88991203d7ea6b699b55009ee06246c9dc",
    "simple/search.html": "5544f212c49bf5d1a3eb5dc664985f69ca6650d60db644b11d08fc61e99336d5",
    "simple/preferences/theme.html": "c1aae439722d068bdf95c0da792d9813a025fe3839d116b34af6c7020cee9b17",
}

SOURCE_RELEASE_URL = "https://github.com/dinozyavier/ayeque-searxng/releases/tag/v2026.3.29-aya29.2"

BASE_STYLES = """  {% if rtl %}
  <link rel="stylesheet" href="{{ url_for('static', filename='sxng-rtl.min.css') }}" type="text/css" media="screen">
  {% else %}
  <link rel="stylesheet" href="{{ url_for('static', filename='sxng-ltr.min.css') }}" type="text/css" media="screen">
  {% endif %}"""

AYEQUE_STYLES = BASE_STYLES + """
  <link rel="stylesheet" href="{{ url_for('static', filename='ayeque.css') }}" type="text/css" media="screen">"""

INDEX_TITLE = '<div class="index">\n    <div class="title"><h1>SearXNG</h1></div>'
INDEX_BRAND = """<div class="index">
    <div class="title"><a class="ayeque-home-link" href="https://ayeque.art/" aria-label="AYEQUE home"><img class="ayeque-logo" src="{{ url_for('static', filename='img/ayeque-logo.webp') }}" alt="AYEQUE"></a></div>"""

SEARCH_WORDMARK = """      <span hidden>SearXNG</span>
      {% include 'simple/searxng-wordmark.min.svg' without context %}"""
SEARCH_BRAND = """      <span hidden>AYEQUE</span>
      <img class="ayeque-wordmark" src="{{ url_for('static', filename='img/ayeque-logo.webp') }}" alt="">"""

PAGE_LOGO = '<img class="logo" src="{{ url_for(\'static\', filename=\'img/searxng.png\') }}" alt="SearXNG">'
PAGE_BRAND = '<img class="logo" src="{{ url_for(\'static\', filename=\'img/ayeque-logo.webp\') }}" alt="AYEQUE">'

SVG_FAVICON = "  <link rel=\"icon\" href=\"{{ url_for('static', filename='img/favicon.svg') }}\" type=\"image/svg+xml\">\n"

UPSTREAM_FOOTER = """  <footer>
    <p>
    {{ _('Powered by') }} <a href="{{ url_for('info', pagename='about') }}">SearXNG</a> - {{ searxng_version }} — {{ _('a privacy-respecting, open metasearch engine') }}<br>
        <a href="{{ searxng_git_url }}">{{ _('Source code') }}</a>
        | <a href="{{ get_setting('brand.issue_url') }}">{{ _('Issue tracker') }}</a>
        {% if enable_metrics %}| <a href="{{ url_for('stats') }}">{{ _('Engine stats') }}</a>{% endif %}
        {% if get_setting('brand.public_instances') %}
        | <a href="{{ get_setting('brand.public_instances') }}">{{ _('Public instances') }}</a>
        {% endif %}
        {% if get_setting('general.privacypolicy_url') %}
        | <a href="{{ get_setting('general.privacypolicy_url') }}">{{ _('Privacy policy') }}</a>
        {% endif %}
        {% if get_setting('general.contact_url') %}
        | <a href="{{ get_setting('general.contact_url') }}">{{ _('Contact instance maintainer') }}</a>
        {% endif %}
        {% for title, link in get_setting('brand.custom.links').items() %}
        | <a href="{{ link }}">{{ _(title) }}</a>
        {% endfor %}
    </p>
  </footer>"""

AYEQUE_FOOTER = f"""  <footer class="ayeque-source-footer">
    <p>Copyright © 2026 Arthur Konovalov · <a href="{SOURCE_RELEASE_URL}" rel="external">Source</a> · AGPL-3.0 · No warranty</p>
  </footer>"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one patch anchor, found {count}")
    return text.replace(old, new, 1)


def remove_style_preference(text: str) -> str:
    marker = '<legend id="pref_simple_style">'
    marker_position = text.find(marker)
    if marker_position < 0:
        raise RuntimeError("preferences/theme.html: simple_style fieldset is missing")
    start = text.rfind("<fieldset>", 0, marker_position)
    end = text.find("</fieldset>", marker_position)
    if start < 0 or end < 0:
        raise RuntimeError("preferences/theme.html: simple_style fieldset bounds are missing")
    end += len("</fieldset>")
    updated = text[:start] + text[end:]
    if marker in updated:
        raise RuntimeError("preferences/theme.html: simple_style fieldset was not removed")
    return updated


def install(root: Path) -> None:
    files: dict[str, str] = {}
    for relative, expected_hash in EXPECTED.items():
        path = root / relative
        data = path.read_bytes()
        actual_hash = sha256(data)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"{relative}: expected SHA-256 {expected_hash}, got {actual_hash}"
            )
        files[relative] = data.decode("utf-8")

    base = replace_once(files["simple/base.html"], BASE_STYLES, AYEQUE_STYLES, "base.html stylesheet")
    base = replace_once(base, SVG_FAVICON, "", "base.html SVG favicon")
    base = replace_once(base, UPSTREAM_FOOTER, AYEQUE_FOOTER, "base.html source footer")
    index = replace_once(files["simple/index.html"], INDEX_TITLE, INDEX_BRAND, "index.html brand")
    page_header = replace_once(
        files["simple/page_with_header.html"], PAGE_LOGO, PAGE_BRAND, "page_with_header.html brand"
    )
    search = replace_once(files["simple/search.html"], SEARCH_WORDMARK, SEARCH_BRAND, "search.html brand")
    preferences = remove_style_preference(files["simple/preferences/theme.html"])

    outputs = {
        "simple/base.html": base,
        "simple/index.html": index,
        "simple/page_with_header.html": page_header,
        "simple/search.html": search,
        "simple/preferences/theme.html": preferences,
    }
    for relative, text in outputs.items():
        (root / relative).write_text(text, encoding="utf-8")

    if base.count("filename='ayeque.css'") != 1:
        raise RuntimeError("base.html: AYEQUE stylesheet hook is not unique")
    if base.count(SOURCE_RELEASE_URL) != 1 or base.count("ayeque-source-footer") != 1:
        raise RuntimeError("base.html: public source offer is not unique")
    if (
        index.count("ayeque-logo.webp") != 1
        or page_header.count("ayeque-logo.webp") != 1
        or search.count("ayeque-logo.webp") != 1
    ):
        raise RuntimeError("brand asset hooks are not unique")
    if index.count('href="https://ayeque.art/"') != 1:
        raise RuntimeError("index.html: AYEQUE home link is not unique")
    if "pref_simple_style" in preferences:
        raise RuntimeError("simple_style preference remains visible")


def self_test() -> None:
    assert replace_once("a TOKEN b", "TOKEN", "VALUE", "test") == "a VALUE b"
    try:
        replace_once("TOKEN TOKEN", "TOKEN", "VALUE", "test")
    except RuntimeError:
        pass
    else:
        raise RuntimeError("replace_once accepted duplicate anchors")

    sample = "<fieldset>theme</fieldset>\n<fieldset><legend id=\"pref_simple_style\">style</legend></fieldset>\n<p>end</p>"
    updated = remove_style_preference(sample)
    assert "theme" in updated and "pref_simple_style" not in updated and "<p>end</p>" in updated
    assert "Source" in AYEQUE_FOOTER and SOURCE_RELEASE_URL in AYEQUE_FOOTER


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=TEMPLATE_ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    install(args.root)


if __name__ == "__main__":
    main()
