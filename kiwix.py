# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kiwix search adapter for the private AYEQUE Wikipedia library.

Two modes, one per engine: `search` (the full-text `/search` XML) and
`suggest` (the `/suggest` JSON, the titles that start with the query).
"""

from __future__ import annotations

import html
import ipaddress
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET


about = {
    "website": "https://www.kiwix.org/",
    "wikidata_id": "Q1408691",
    "official_api_documentation": "https://kiwix-tools.readthedocs.io/en/latest/kiwix-serve.html#search",
    "use_official_api": True,
    "require_api_key": False,
    "results": "XML-RSS, JSON",
}

categories = ["wikipedia"]
paging = True
timeout = 3.0

# Required per-engine settings. The defaults deliberately fail closed.
base_url = ""
public_base_url = ""
archive_lang = ""
archive_alias = ""
# `search` (full text, XML) or `suggest` (title prefixes, JSON).
mode = "search"
result_count = 10
max_response_bytes = 262_144

_MODES = ("search", "suggest")
_CONTENT_PREFIX = "/wiki/content/"
_LANGUAGES = {"eng": "en", "fra": "fr", "rus": "ru", "ukr": "uk"}
_WHITESPACE = re.compile(r"\s+")


def _internal_base() -> str:
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme != "http" or parsed.username or parsed.password:
        raise ValueError("Kiwix base must be unauthenticated private HTTP")
    if parsed.query or parsed.fragment or parsed.path.rstrip("/") != "/wiki":
        raise ValueError("Kiwix base must end at /wiki")
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as exc:
        raise ValueError("Kiwix host must be a literal private IP address") from exc
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError("Kiwix host must be a non-loopback private IP address")
    if parsed.port is None or not 1 <= parsed.port <= 65535:
        raise ValueError("Kiwix base requires an explicit port")
    return base_url.rstrip("/")


def _public_origin() -> str:
    parsed = urllib.parse.urlsplit(public_base_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("public base must be an HTTPS origin")
    return f"https://{parsed.hostname}"


def _language_contract() -> str:
    short = _LANGUAGES.get(archive_lang)
    if short is None or archive_alias != f"wikipedia_{short}_all_maxi":
        raise ValueError("Kiwix language/alias contract differs")
    return short


def request(query, params):
    """Build one bounded public `/search` or `/suggest` request for the fixed archive."""

    _internal_base()
    _public_origin()
    _language_contract()
    if mode not in _MODES:
        raise ValueError("Kiwix mode must be search or suggest")
    if not isinstance(result_count, int) or not 1 <= result_count <= 20:
        raise ValueError("Kiwix result_count is outside the accepted bound")
    page = params.get("pageno", 1)
    if not isinstance(page, int) or page < 1 or page > 100:
        raise ValueError("Kiwix page is outside the accepted bound")
    if mode == "suggest":
        # The titles that start with the query, in the one fixed book.
        args = {
            "content": archive_alias,
            "term": query,
            "count": result_count,
            "start": (page - 1) * result_count,
        }
        params["url"] = f"{_internal_base()}/suggest?{urllib.parse.urlencode(args)}"
        accept = "application/json"
    else:
        args = {
            "pattern": query,
            "books.filter.lang": archive_lang,
            "books.filter.category": "wikipedia",
            "format": "xml",
            "pageLength": result_count,
            "start": (page - 1) * result_count,
        }
        params["url"] = f"{_internal_base()}/search?{urllib.parse.urlencode(args)}"
        accept = "application/rss+xml, application/xml;q=0.9"
    params["raise_for_httperror"] = True
    params["soft_max_redirects"] = 0
    headers = params.setdefault("headers", {})
    headers["Accept"] = accept
    return params


def _text(element: ET.Element | None, limit: int) -> str:
    if element is None:
        return ""
    value = _WHITESPACE.sub(" ", "".join(element.itertext())).strip()
    return value[:limit]


def _stable_result_url(raw: str) -> str | None:
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return None
    prefix = _CONTENT_PREFIX
    if not parsed.path.startswith(prefix) or "\\" in parsed.path or "//" in parsed.path:
        return None
    remainder = parsed.path[len(prefix) :]
    try:
        name, article_path = remainder.split("/", 1)
    except ValueError:
        return None
    if not re.fullmatch(re.escape(archive_alias) + r"(?:_[0-9]{4}-[0-9]{2}[a-z]?)?", name):
        return None
    if not article_path or len(article_path) > 4096:
        return None
    for encoded in article_path.split("/"):
        try:
            decoded = urllib.parse.unquote(encoded, errors="strict")
        except UnicodeDecodeError:
            return None
        if decoded in ("", ".", "..") or "/" in decoded or "\\" in decoded:
            return None
        if any(ord(char) < 32 or ord(char) == 127 for char in decoded):
            return None
    return f"{_public_origin()}{prefix}{archive_alias}/{article_path}"


def response(resp):
    """Parse a bounded Kiwix RSS/XML or `/suggest` JSON answer."""

    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise RuntimeError("Kiwix search returned a non-success status")
    content_length = resp.headers.get("content-length") if hasattr(resp, "headers") else None
    if content_length:
        try:
            if int(content_length) > max_response_bytes:
                raise RuntimeError("Kiwix search response is oversized")
        except ValueError as exc:
            raise RuntimeError("Kiwix content length is invalid") from exc
    data = bytes(resp.content)
    if not isinstance(max_response_bytes, int) or not 4096 <= max_response_bytes <= 1_048_576:
        raise ValueError("Kiwix max_response_bytes is outside the accepted bound")
    if len(data) > max_response_bytes:
        raise RuntimeError("Kiwix search response is oversized")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Kiwix search response is not UTF-8") from exc
    if mode == "suggest":
        return _suggest_results(text)
    lowered = text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise RuntimeError("Kiwix search response contains a forbidden DTD")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise RuntimeError("Kiwix search response is malformed XML") from exc
    if root.tag != "rss":
        raise RuntimeError("Kiwix search response root differs")
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("Kiwix search response channel is absent")

    results = []
    for item in channel.findall("item")[:result_count]:
        title = _text(item.find("title"), 512)
        raw_url = _text(item.find("link"), 4096)
        stable_url = _stable_result_url(raw_url)
        if not title or stable_url is None:
            continue
        results.append(
            {
                "url": stable_url,
                "title": title,
                "content": _text(item.find("description"), 4096),
            }
        )
    return results


def _suggest_results(text: str) -> list:
    """The title matches of a `/suggest` JSON list, as same-origin results."""

    try:
        entries = json.loads(text)
    except ValueError as exc:
        raise RuntimeError("Kiwix suggest response is malformed JSON") from exc
    if not isinstance(entries, list):
        raise RuntimeError("Kiwix suggest response is not a list")
    results = []
    for entry in entries:
        # The last entry of a list is often "containing '...'", a full-text
        # offer and not an article: only `path` entries are articles.
        if not isinstance(entry, dict) or entry.get("kind") != "path":
            continue
        value, path = entry.get("value"), entry.get("path")
        if not isinstance(value, str) or not isinstance(path, str):
            continue
        title = _WHITESPACE.sub(" ", html.unescape(value)).strip()[:512]
        stable_url = _stable_result_url(
            f"{_CONTENT_PREFIX}{archive_alias}/{urllib.parse.quote(path, safe='/')}"
        )
        if not title or stable_url is None:
            continue
        results.append({"url": stable_url, "title": title, "content": ""})
        if len(results) == result_count:
            break
    return results
