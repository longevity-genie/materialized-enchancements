from __future__ import annotations

from urllib.parse import unquote_plus

from materialized_enhancements.ai_prompts import (
    GITHUB_CSV_BASE_URL,
    GITHUB_CSV_FILES,
    GITHUB_DATABASE_URL,
    build_gene_ai_assistant_url,
    build_gene_ai_links,
    build_gene_ai_prompt,
    build_profile_ai_links,
    build_profile_ai_prompt,
    csv_file_url,
    format_gene_ai_dossier,
)


def test_profile_prompt_queries_all_selected_genes_from_public_sqlite() -> None:
    prompt = build_profile_ai_prompt(
        gene_ids=["foxo3", "klotho", "foxo3"],
        character_name="Test character",
        character_note="Built for an exhibit.",
        revision="test-dolt-revision",
    )

    assert GITHUB_DATABASE_URL in prompt
    assert "gene_id values: foxo3, klotho" in prompt
    assert "Filter: gene_id IN ('foxo3', 'klotho')" in prompt
    assert "keep ALL matches, no LIMIT" in prompt
    assert "gene_confidence WHERE is_primary=1" in prompt
    assert "test-dolt-revision" in prompt
    assert "<profile_label>Test character</profile_label>" in prompt
    assert "<character_note>Built for an exhibit.</character_note>" in prompt
    assert "never memory" in prompt
    assert "No treatment" in prompt
    assert "PRIMARY DELIVERABLE" in prompt
    assert "portrait-format character-card image" in prompt
    assert "Upper 60–70%" in prompt
    assert "Lower 30–40%" in prompt
    assert "90–140 words" in prompt
    assert "MUST be visibly typeset inside the generated card image" in prompt
    assert "regenerate the card rather than accepting a plain portrait" in prompt
    assert "repeat the exact title, subtitle, and card lore" in prompt
    assert "SCIENCE AND ASSUMPTIONS" in prompt
    assert "non-biologists first" in prompt


def test_profile_prompt_prefers_csv_urls_over_binary_sqlite() -> None:
    prompt = build_profile_ai_prompt(gene_ids=["cirbp"], revision="revision")

    assert "Prefer text CSV downloads" in prompt
    assert "cannot fetch binary SQLite" in prompt
    assert GITHUB_CSV_BASE_URL in prompt
    assert all(csv_file_url(filename) in prompt for filename in GITHUB_CSV_FILES)
    assert "Do not web-search" in prompt
    assert "browse GitHub/DoltHub pages" in prompt
    assert "https://www.dolthub.com" not in prompt
    assert "request the listed CSV files" in prompt
    assert "do not use general knowledge" in prompt


def test_profile_ai_links_encode_same_compact_prompt_for_each_provider() -> None:
    links = build_profile_ai_links(
        gene_ids=["klotho"],
        character_name="Profile",
    )

    assert [link["label"] for link in links] == [
        "ChatGPT",
        "Claude",
        "Grok",
    ]
    assert [link["icon_src"] for link in links] == [
        "/images/icons/openai.svg",
        "/images/icons/claude.svg",
        "/images/icons/grok.svg",
    ]
    for link in links:
        encoded_prompt = link["url"].split("=", maxsplit=1)[1]
        decoded_prompt = unquote_plus(encoded_prompt)
        assert GITHUB_DATABASE_URL in decoded_prompt
        assert "gene_id values: klotho" in decoded_prompt


def test_profile_ai_links_are_empty_without_selected_genes() -> None:
    assert build_profile_ai_links(gene_ids=[]) == []


def test_gene_prompt_embeds_dossier_and_csv_fallbacks() -> None:
    prompt = build_gene_ai_prompt(gene_id="klotho", revision="test-revision")

    assert "EMBEDDED PROJECT DOSSIER" in prompt
    assert "Target: Klotho (gene_id klotho)" in prompt
    assert "gene_id: klotho" in prompt
    assert "Short description:" in prompt
    assert "PRIMARY (mammal/human enhancement potential)" in prompt
    assert "OPTIONAL DEEPER EVIDENCE" in prompt
    assert "cannot download binary SQLite" in prompt
    assert all(csv_file_url(filename) in prompt for filename in GITHUB_CSV_FILES)
    assert "gene_id = 'klotho'" in prompt
    assert "commercial offering is not evidence of efficacy" in prompt
    assert "most readers are NOT biologists" in prompt
    assert "decide whether to SELECT this gene" in prompt
    assert "Pros of selecting it for the profile" in prompt
    assert "Cons / reasons to skip" in prompt
    assert "Decision takeaway" in prompt
    assert "In everyday words" in prompt
    assert "For biologists" in prompt
    assert "Never open with the gene/therapy name" in prompt
    assert "Label speculation explicitly" in prompt
    assert "test-revision" in prompt
    assert GITHUB_DATABASE_URL in prompt


def test_gene_dossier_stays_within_url_budget_for_heavy_genes() -> None:
    dossier = format_gene_ai_dossier(
        {
            "gene_id": "tert",
            "gene": "TERT",
            "manipulation": "overexpression",
            "category": "Longevity & Genome",
            "trait": "Telomere",
            "species_common_names": "Human",
            "species_scientific_names": "Homo sapiens",
            "evidence_basis": "T5",
            "short_description": "Telomerase.",
            "achievements": "Longer telomeres in mice.",
            "mechanism": "Extends telomeres.",
            "narrative": "x" * 4000,
            "translational_gaps": "Cancer risk.",
            "key_references": "doi:10.example/tert",
            "notes": "Caveat.",
            "confidence_primary": {
                "value": "High",
                "argument": "mammalian evidence",
                "description": "Works in mice.",
                "primary": True,
            },
            "confidence_details": [],
            "testing_entries": [
                {
                    "host": "Human",
                    "tissue_or_system": "blood",
                    "intervention": "gene_therapy",
                    "delivery": "AAV",
                    "key_result": f"result {idx}",
                    "effect_size": "2x",
                    "positive": "yes",
                    "reference_short": f"NCT{idx:08d}",
                    "doi": f"https://example.com/{idx}",
                    "year": "2020",
                }
                for idx in range(40)
            ],
            "org_entries": [],
        }
    )

    assert len(dossier) <= 7500
    assert "gene_id: tert" in dossier
    assert "Testing evidence:" in dossier
    assert "gene_testing.csv" in dossier


def test_gene_links_are_available_for_each_provider() -> None:
    links = build_gene_ai_links(gene_id="foxo3")

    assert [link["label"] for link in links] == [
        "ChatGPT",
        "Claude",
        "Grok",
    ]
    for link in links:
        decoded = unquote_plus(link["url"].split("=", maxsplit=1)[1])
        assert "Target: FOXO3 (gene_id foxo3)" in decoded
        assert "EMBEDDED PROJECT DOSSIER" in decoded
        assert csv_file_url("gene_testing.csv") in decoded
        assert len(link["url"]) < 20000


def test_gene_assistant_url_builds_one_provider_on_demand() -> None:
    url = build_gene_ai_assistant_url(gene_id="foxo3", provider="chatgpt")

    assert url.startswith("https://chatgpt.com/?q=")
    decoded = unquote_plus(url.split("=", maxsplit=1)[1])
    assert "Target: FOXO3 (gene_id foxo3)" in decoded
    assert build_gene_ai_assistant_url(gene_id="foxo3", provider="nope") == ""
