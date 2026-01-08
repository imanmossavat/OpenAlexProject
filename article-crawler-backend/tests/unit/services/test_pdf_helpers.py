from __future__ import annotations

import logging
from types import SimpleNamespace

from app.schemas.seeds import MatchedSeed
from app.services.workflows.pdf_helpers import (
    PDFMatchedSeedBuilder,
    PDFSeedEnricher,
    PDFStagingRowBuilder,
)


def test_pdf_staging_row_builder_links_files_to_rows():
    reviewed = [
        SimpleNamespace(
            filename="paper1.pdf",
            title="Paper One",
            authors="Doe",
            year=2021,
            venue="Conf A",
            doi="10.123/abc",
            abstract="Abstract text",
        ),
        SimpleNamespace(
            filename="paper2.pdf",
            title="Paper Two",
            authors=None,
            year=None,
            venue=None,
            doi=None,
            abstract=None,
        ),
    ]
    stored_files = {"paper1.pdf": "file-1"}

    builder = PDFStagingRowBuilder()
    rows = builder.build_from_reviewed(reviewed, stored_files)

    assert len(rows) == 2
    assert rows[0].source == "Uploaded Files"
    assert rows[0].source_type == "pdf"
    assert rows[0].source_file_id == "file-1"
    assert rows[0].source_file_name == "paper1.pdf"
    assert rows[0].source_id == "10.123/abc"

    assert rows[1].source_file_id is None
    assert rows[1].source_file_name is None
    assert rows[1].source_id == "paper2.pdf"


def test_pdf_matched_seed_builder_sets_defaults():
    seeds_data = [
        {
            "paper_id": "W123",
            "title": "Paper",
            "authors": "Author",
            "year": 2020,
            "venue": "Venue",
            "confidence": 0.95,
            "match_method": "doi",
            "source_id": "src-123",
        }
    ]

    builder = PDFMatchedSeedBuilder()
    seeds = builder.build(seeds_data)

    assert len(seeds) == 1
    seed = seeds[0]
    assert isinstance(seed, MatchedSeed)
    assert seed.paper_id == "W123"
    assert seed.source == "Uploaded Files"
    assert seed.source_type == "pdf"
    assert seed.source_id == "src-123"


def test_pdf_seed_enricher_enriches_with_openalex_metadata():
    base_seed = MatchedSeed(
        paper_id="W1",
        title="Sample",
        authors="Doe",
        source="Uploaded Files",
        source_type="pdf",
        source_id="src-1",
    )

    payload = {
        "doi": "10.999/xyz",
        "primary_location": {"landing_page_url": "https://example.com/paper"},
        "abstract": None,
        "abstract_inverted_index": {"hello": [0], "world": [1]},
        "cited_by_count": 7,
        "referenced_works": ["a", "b", "c"],
        "authorships": [
            {"institutions": [{"display_name": "Institute One"}]},
            {"institutions": [{"name": "Institute Two"}]},
        ],
    }

    class FakeAPI:
        def get_paper_metadata_only(self, paper_id):
            assert paper_id == "W1"
            return payload

    enricher = PDFSeedEnricher(
        logger=logging.getLogger("test"),
        api_factory=lambda provider: FakeAPI(),
    )

    enriched = enricher.enrich([base_seed])
    assert len(enriched) == 1
    result = enriched[0]

    assert result.doi == "10.999/xyz"
    assert result.url == "https://example.com/paper"
    assert result.abstract == "hello world"
    assert result.cited_by_count == 7
    assert result.references_count == 3
    assert result.institutions == ["Institute One", "Institute Two"]
    assert result.source == base_seed.source
    assert result.source_type == base_seed.source_type
