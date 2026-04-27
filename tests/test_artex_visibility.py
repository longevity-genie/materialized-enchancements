from __future__ import annotations

from materialized_enhancements.state import _has_artex_integration_settings


def test_artex_settings_require_url_token_and_display() -> None:
    assert _has_artex_integration_settings("http://127.0.0.1:8787", "abcd", "test-wall")


def test_artex_settings_missing_token_are_not_configured() -> None:
    assert not _has_artex_integration_settings("http://127.0.0.1:8787", "", "test-wall")


def test_artex_settings_ignore_whitespace_values() -> None:
    assert not _has_artex_integration_settings("  ", "abcd", "test-wall")
    assert not _has_artex_integration_settings("http://127.0.0.1:8787", "  ", "test-wall")
    assert not _has_artex_integration_settings("http://127.0.0.1:8787", "abcd", "  ")
