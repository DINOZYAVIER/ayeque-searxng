#!/usr/bin/env python3
"""Offline contract tests for the AYEQUE Kiwix SearXNG engine."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

sys.dont_write_bytecode = True


ENGINE_PATH = Path(__file__).resolve().parents[1] / "kiwix.py"
SPEC = importlib.util.spec_from_file_location("ayeque_kiwix_engine", ENGINE_PATH)
assert SPEC and SPEC.loader
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)


class Response:
    def __init__(self, content: bytes, status: int = 200, headers: dict[str, str] | None = None):
        self.content = content
        self.status_code = status
        self.headers = headers or {"content-length": str(len(content))}


def configure(language: str = "eng", alias: str = "wikipedia_en_all_maxi") -> None:
    ENGINE.base_url = "http://10.20.30.40:8080/wiki"
    ENGINE.public_base_url = "https://search.example.test"
    ENGINE.archive_lang = language
    ENGINE.archive_alias = alias
    ENGINE.result_count = 10
    ENGINE.max_response_bytes = 262_144
    ENGINE.mode = "search"


def xml(items: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel><title>synthetic</title>'
        f"{items}</channel></rss>"
    ).encode()


def item(title: str, link: str, description: str = "A <b>safe</b> snippet") -> str:
    return f"<item><title>{title}</title><link>{link}</link><description>{description}</description></item>"


def expect_error(fn) -> None:
    try:
        fn()
    except (RuntimeError, ValueError):
        return
    raise AssertionError("invalid Kiwix input was accepted")


def suggestions(entries) -> bytes:
    return json.dumps(entries, ensure_ascii=False).encode()


def suggest_mode() -> None:
    """The `/suggest` mode: the titles that start with the query."""

    configure()
    ENGINE.mode = "suggest"
    params = ENGINE.request("Київ & test", {"pageno": 2, "headers": {}})
    parsed = urlsplit(params["url"])
    assert parsed.scheme == "http" and parsed.hostname == "10.20.30.40"
    assert parsed.path == "/wiki/suggest"
    assert parse_qs(parsed.query) == {
        "content": ["wikipedia_en_all_maxi"],
        "term": ["Київ & test"],
        "count": ["10"],
        "start": ["10"],
    }
    assert params["headers"]["Accept"] == "application/json"
    assert params["soft_max_redirects"] == 0 and params["raise_for_httperror"] is True

    entries = [
        {"value": "Rust", "label": "<b>Rust</b>", "kind": "path", "path": "Rust"},
        {"value": "Rust &amp; Bone", "label": "x", "kind": "path", "path": "Rust_&_Bone"},
        {"value": "Rust (Baden)", "label": "x", "kind": "path", "path": "Rust_(Baden)"},
        {"value": "AC/DC", "label": "x", "kind": "path", "path": "AC/DC"},
        {"value": "Київ", "label": "x", "kind": "path", "path": "Київ"},
        # A full-text offer is not an article.
        {"value": "Rust ", "label": "containing 'Rust'...", "kind": "pattern"},
    ]
    results = ENGINE.response(Response(suggestions(entries)))
    base = "https://search.example.test/wiki/content/wikipedia_en_all_maxi/"
    assert results == [
        {"url": base + "Rust", "title": "Rust", "content": ""},
        {"url": base + "Rust_%26_Bone", "title": "Rust & Bone", "content": ""},
        {"url": base + "Rust_%28Baden%29", "title": "Rust (Baden)", "content": ""},
        {"url": base + "AC/DC", "title": "AC/DC", "content": ""},
        {"url": base + "%D0%9A%D0%B8%D1%97%D0%B2", "title": "Київ", "content": ""},
    ], results

    # Only the first `result_count` articles are kept.
    ENGINE.result_count = 2
    assert [r["title"] for r in ENGINE.response(Response(suggestions(entries)))] == ["Rust", "Rust & Bone"]
    ENGINE.result_count = 10

    # A path that leaves the book, or a malformed entry, is dropped.
    unsafe = [
        {"value": "x", "kind": "path", "path": "../escape"},
        {"value": "x", "kind": "path", "path": "a//b"},
        {"value": "x", "kind": "path", "path": ""},
        {"value": "x", "kind": "path", "path": "a/./b"},
        {"value": "x", "kind": "path", "path": 5},
        {"value": 7, "kind": "path", "path": "ok"},
        {"value": "  ", "kind": "path", "path": "blank"},
        {"value": "x", "kind": "other", "path": "ok"},
        "not an object",
    ]
    assert ENGINE.response(Response(suggestions(unsafe))) == []

    # The answer is bounded, UTF-8 JSON list; the status is checked as for search.
    expect_error(lambda: ENGINE.response(Response(b"{not json")))
    expect_error(lambda: ENGINE.response(Response(b'{"value": "x"}')))
    expect_error(lambda: ENGINE.response(Response(b"x" * 262_145)))
    expect_error(lambda: ENGINE.response(Response(b"[]", status=500)))
    assert ENGINE.response(Response(b"", status=404)) == []
    assert ENGINE.response(Response(b"[]")) == []

    # The same private-origin and mode contract as for search.
    ENGINE.mode = "other"
    expect_error(lambda: ENGINE.request("test", {"pageno": 1}))
    configure()
    ENGINE.mode = "suggest"
    ENGINE.base_url = "http://example.org:8080/wiki"
    expect_error(lambda: ENGINE.request("test", {"pageno": 1}))
    configure()
    ENGINE.mode = "suggest"
    ENGINE.result_count = 21
    expect_error(lambda: ENGINE.request("test", {"pageno": 1}))
    configure()


def main() -> None:
    configure()
    params = ENGINE.request("7900 xtx & test", {"pageno": 3, "headers": {}})
    parsed = urlsplit(params["url"])
    query = parse_qs(parsed.query)
    assert parsed.scheme == "http" and parsed.hostname == "10.20.30.40"
    assert parsed.path == "/wiki/search"
    assert query == {
        "pattern": ["7900 xtx & test"],
        "books.filter.lang": ["eng"],
        "books.filter.category": ["wikipedia"],
        "format": ["xml"],
        "pageLength": ["10"],
        "start": ["20"],
    }
    assert params["soft_max_redirects"] == 0

    body = xml(
        item("Canada &amp; North", "/wiki/content/wikipedia_en_all_maxi_2026-02/Canada")
        + item("Україна", "/wiki/content/wikipedia_en_all_maxi/%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D0%B0")
    )
    results = ENGINE.response(Response(body))
    assert results == [
        {
            "url": "https://search.example.test/wiki/content/wikipedia_en_all_maxi/Canada",
            "title": "Canada & North",
            "content": "A safe snippet",
        },
        {
            "url": "https://search.example.test/wiki/content/wikipedia_en_all_maxi/%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D0%B0",
            "title": "Україна",
            "content": "A safe snippet",
        },
    ]

    for language, alias in (
        ("eng", "wikipedia_en_all_maxi"),
        ("fra", "wikipedia_fr_all_maxi"),
        ("rus", "wikipedia_ru_all_maxi"),
        ("ukr", "wikipedia_uk_all_maxi"),
    ):
        configure(language, alias)
        result = ENGINE.response(Response(xml(item(language, f"/wiki/content/{alias}_2026-02/Article"))))
        assert result[0]["url"].endswith(f"/wiki/content/{alias}/Article")

    configure()
    unsafe = (
        "https://evil.example/wiki/content/wikipedia_en_all_maxi/Article",
        "/wiki/content/wikipedia_fr_all_maxi_2026-05/Article",
        "/wiki/content/wikipedia_en_all_maxi/../escape",
        "/wiki/content/wikipedia_en_all_maxi/%2Fescape",
        "/wiki/content/wikipedia_en_all_maxi//double",
        "/wiki/content/wikipedia_en_all_maxi/Article?next=https://evil.example",
    )
    for link in unsafe:
        assert ENGINE.response(Response(xml(item("unsafe", link.replace("&", "&amp;"))))) == []

    expect_error(lambda: ENGINE.response(Response(b"<rss>")))
    expect_error(lambda: ENGINE.response(Response(b'<!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss/>')))
    expect_error(lambda: ENGINE.response(Response(b"x" * 262_145)))
    expect_error(lambda: ENGINE.response(Response(body, headers={"content-length": "262145"})))
    assert ENGINE.response(Response(b"", status=404)) == []
    expect_error(lambda: ENGINE.response(Response(b"error", status=500)))

    configure()
    ENGINE.base_url = "http://example.org:8080/wiki"
    expect_error(lambda: ENGINE.request("test", {"pageno": 1}))
    configure()
    ENGINE.public_base_url = "http://search.example.test"
    expect_error(lambda: ENGINE.request("test", {"pageno": 1}))
    suggest_mode()
    print("kiwix_engine=ok")


if __name__ == "__main__":
    main()
