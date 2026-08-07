"""Tests for organization cross-links exposed by the knowledgebase UI."""

from __future__ import annotations

from materialized_enhancements.gene_data import ORG_GENE_LIST
from materialized_enhancements.pages.knowledgebase import (
    _organization_sources,
    _program_type,
    _programs_lazyframe,
    _split_key_people,
)


def test_program_view_preserves_every_valid_org_gene_link() -> None:
    rows = _programs_lazyframe().collect().to_dicts()

    assert len(rows) == len(ORG_GENE_LIST)
    assert {row["Program type"] for row in rows} == {
        "Research program",
        "Therapy / offering",
    }
    assert all(row["Organization"] and row["Gene"] for row in rows)
    assert all("Experiment rows" in row for row in rows)


def test_program_type_does_not_equate_commercial_status_with_efficacy() -> None:
    assert _program_type("commercial") == "Therapy / offering"
    assert _program_type("phase_1") == "Therapy / offering"
    assert _program_type("preclinical") == "Research program"


def test_key_people_are_display_only_until_profile_is_verified() -> None:
    people = _split_key_people("Liz Parrish (CEO), George Church (co-founder)")

    assert people == [
        {
            "name": "Liz Parrish",
            "role": "CEO",
            "profile_url": "",
            "profile_status": "Unverified",
            "profile_source": "",
        },
        {
            "name": "George Church",
            "role": "co-founder",
            "profile_url": "",
            "profile_status": "Unverified",
            "profile_source": "",
        },
    ]


def test_organization_sources_are_deduplicated() -> None:
    sources = _organization_sources("klothea_bio")
    urls = [entry["url"] for entry in sources]

    assert urls
    assert len(urls) == len(set(urls))
