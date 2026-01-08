
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any, Optional
from types import SimpleNamespace
import uuid
from datetime import datetime

from app.main import app
from app.api.dependencies import (
    get_crawler_execution_service,
    get_integration_settings_service,
    get_library_service,
    get_pdf_seed_service,
    get_paper_catalog_service,
    get_paper_metadata_service,
    get_seed_selection_service,
    get_seed_session_service,
    get_staging_service,
    get_zotero_seed_service,
)
from app.core.container import Container
from app.schemas.seeds import MatchedSeed, SeedMatchResult, UnmatchedSeed
from app.schemas.papers import (
    PaginatedPaperSummaries,
    PaperSummary,
    PaperMarkResponse,
    ColumnOptionsPage,
    PaperDetail,
)
from app.schemas.staging import (
    ColumnFilterOption,
    StagingPaper,
    StagingPaperCreate,
    StagingListResponse,
)


@pytest.fixture(scope="function")
def app_client(
    mock_staging_service,
    mock_seed_selection_service,
    mock_seed_session_service,
    mock_library_service,
    mock_pdf_service,
    mock_zotero_service,
    mock_integration_settings_service,
    mock_crawler_execution_service,
    mock_paper_catalog_service,
    mock_paper_metadata_service,
):
    """Create a FastAPI test client with dependency overrides."""
    overrides = {
        get_staging_service: lambda: mock_staging_service,
        get_seed_selection_service: lambda: mock_seed_selection_service,
        get_seed_session_service: lambda: mock_seed_session_service,
        get_library_service: lambda: mock_library_service,
        get_pdf_seed_service: lambda: mock_pdf_service,
        get_zotero_seed_service: lambda: mock_zotero_service,
        get_integration_settings_service: lambda: mock_integration_settings_service,
        get_crawler_execution_service: lambda: mock_crawler_execution_service,
        get_paper_catalog_service: lambda: mock_paper_catalog_service,
        get_paper_metadata_service: lambda: mock_paper_metadata_service,
    }
    app.dependency_overrides.update(overrides)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        for dep in overrides:
            app.dependency_overrides.pop(dep, None)


@pytest.fixture
def test_session_id():
    """Generate a unique session ID for testing."""
    return f"test-session-{uuid.uuid4()}"


@pytest.fixture
def sample_paper_ids():
    """Sample paper IDs for testing."""
    return [
        "W2741809807",
        "W2964141474",
        "W2950950274",
        "10.1038/nature12373",
        "arXiv:1706.03762"
    ]


@pytest.fixture
def sample_matched_seeds():
    """Sample matched seed objects."""
    return [
        MatchedSeed(
            paper_id="W2741809807",
            title="Attention Is All You Need",
            authors="Ashish Vaswani, Noam Shazeer",
            year=2017,
            venue="NeurIPS",
            doi="10.48550/arXiv.1706.03762",
            abstract="The dominant sequence transduction models...",
            source="openalex"
        ),
        MatchedSeed(
            paper_id="W2964141474",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors="Jacob Devlin, Ming-Wei Chang",
            year=2019,
            venue="NAACL",
            doi="10.18653/v1/N19-1423",
            abstract="We introduce a new language representation model...",
            source="openalex"
        ),
        MatchedSeed(
            paper_id="W2950950274",
            title="Deep Learning",
            authors="Yann LeCun, Yoshua Bengio, Geoffrey Hinton",
            year=2015,
            venue="Nature",
            doi="10.1038/nature14539",
            abstract="Deep learning allows computational models...",
            source="openalex"
        )
    ]


@pytest.fixture
def sample_staging_papers():
    """Sample staging papers."""
    return [
        StagingPaper(
            staging_id=1,
            session_id="test-session-123",
            source="manual",
            source_type="manual",
            title="Attention Is All You Need",
            authors="Ashish Vaswani, Noam Shazeer",
            year=2017,
            venue="NeurIPS",
            doi="10.48550/arXiv.1706.03762",
            is_selected=False
        ),
        StagingPaper(
            staging_id=2,
            session_id="test-session-123",
            source="pdf",
            source_type="pdf",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors="Jacob Devlin, Ming-Wei Chang",
            year=2019,
            venue="NAACL",
            doi="10.18653/v1/N19-1423",
            is_selected=False
        ),
        StagingPaper(
            staging_id=3,
            session_id="test-session-123",
            source="zotero",
            source_type="zotero",
            title="Deep Learning",
            authors="Yann LeCun, Yoshua Bengio, Geoffrey Hinton",
            year=2015,
            venue="Nature",
            doi="10.1038/nature14539",
            is_selected=False
        )
    ]


@pytest.fixture
def mock_seed_selection_service(sample_matched_seeds):
    """Mock seed selection service with dynamic matching."""
    mock_service = Mock()

    lookup: Dict[str, MatchedSeed] = {}

    def register_key(key: Optional[str], seed: MatchedSeed):
        if key:
            lookup[key] = seed

    for seed in sample_matched_seeds:
        if seed.paper_id:
            register_key(seed.paper_id, seed)
            register_key(seed.paper_id.lower(), seed)
            register_key(seed.paper_id.upper(), seed)
            register_key(f"https://openalex.org/{seed.paper_id}", seed)
            register_key(f"https://openalex.org/{seed.paper_id}".lower(), seed)
        if seed.doi:
            doi_clean = seed.doi.strip()
            doi_lower = doi_clean.lower()
            doi_no_prefix = doi_lower.replace("https://doi.org/", "").replace("http://doi.org/", "")
            register_key(doi_clean, seed)
            register_key(doi_lower, seed)
            register_key(doi_no_prefix, seed)
            register_key(f"https://doi.org/{doi_no_prefix}", seed)
            register_key(f"http://doi.org/{doi_no_prefix}", seed)
    
    def match_ids(ids, api_provider="openalex"):
        """Match paper IDs dynamically."""
        matched = []
        unmatched = []

        for id_val in ids:
            identifier = (id_val or "").strip()
            candidates = [
                identifier,
                identifier.lower(),
                identifier.upper(),
            ]
            lowered = identifier.lower()
            if "doi.org/" in lowered:
                candidates.append(lowered.split("doi.org/")[1])
            if lowered.startswith("doi:"):
                candidates.append(lowered.replace("doi:", ""))
            if "openalex.org/" in lowered:
                candidates.append(lowered.split("openalex.org/")[1])

            seed = None
            for cand in candidates:
                seed = lookup.get(cand)
                if seed:
                    matched.append(seed)
                    break

            if not seed:
                unmatched.append(
                    UnmatchedSeed(
                        input_id=id_val,
                        error="Paper metadata not found in provider"
                    )
                )
        
        return SeedMatchResult(
            matched_seeds=matched,
            unmatched_seeds=unmatched,
            total_matched=len(matched),
            total_unmatched=len(unmatched)
        )
    
    mock_service.match_paper_ids = Mock(side_effect=match_ids)
    
    return mock_service


@pytest.fixture
def mock_seed_session_service(sample_matched_seeds):
    """Mock seed session service."""
    mock_service = Mock()
    
    mock_service.start_session = Mock(return_value=Mock(
        session_id="test-session-123",
        use_case="library_creation",
        created_at=datetime.utcnow()
    ))
    
    mock_service.get_session = Mock(return_value=Mock(
        session_id="test-session-123",
        use_case="library_creation",
        seeds=sample_matched_seeds,
        total_seeds=len(sample_matched_seeds),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ))
    
    mock_service.add_seeds_to_session = Mock(return_value=Mock(
        session_id="test-session-123",
        added_count=1,
        duplicate_count=0,
        total_seeds=3
    ))
    
    mock_service.set_seeds_for_session = Mock(return_value=Mock(
        session_id="test-session-123",
        added_count=3,
        duplicate_count=0,
        total_seeds=3
    ))
    
    return mock_service


@pytest.fixture
def mock_staging_service(sample_staging_papers):
    """Mock staging service."""
    mock_service = Mock()
    mock_service.logger = Mock()
    
    mock_service.list_rows = Mock(return_value=StagingListResponse(
        session_id="test-session-123",
        rows=sample_staging_papers,
        total_rows=len(sample_staging_papers),
        filtered_rows=len(sample_staging_papers),
        selected_count=0,
        page=1,
        page_size=25,
        total_pages=1,
    ))
    
    mock_service.add_rows = Mock(return_value=sample_staging_papers)
    
    _selected_rows: dict[str, list[int]] = {}
    
    def _set_selection(session_id: str, staging_ids: list[int], is_selected: bool) -> int:
        if is_selected:
            _selected_rows[session_id] = staging_ids
        else:
            _selected_rows.pop(session_id, None)

        target_ids = set(staging_ids)
        for idx, row in enumerate(sample_staging_papers):
            if row.staging_id in target_ids:
                sample_staging_papers[idx] = row.model_copy(update={"is_selected": is_selected})

        return len(staging_ids)
    
    def _get_selected_rows(session_id: str):
        ids = _selected_rows.get(session_id)
        if not ids:
            return []
        by_id = {row.staging_id: row for row in sample_staging_papers}
        return [by_id.get(i) for i in ids if i in by_id]
    
    mock_service.set_selection = Mock(side_effect=_set_selection)
    mock_service.get_selected_rows = Mock(side_effect=_get_selected_rows)
    
    mock_service.update_row = Mock(return_value=sample_staging_papers[0])
    
    mock_service.remove_rows = Mock(return_value=1)
    
    _match_storage: dict[str, list] = {}
    
    def _store_match_rows(session_id: str, rows: list):
        _match_storage[session_id] = rows
    
    def _get_match_rows(session_id: str):
        return _match_storage.get(session_id, [])
    
    mock_service.store_match_rows = Mock(side_effect=_store_match_rows)
    mock_service.get_match_rows = Mock(side_effect=_get_match_rows)
    
    mock_service.get_row = Mock(return_value=sample_staging_papers[0])
    
    mock_service.clear_session = Mock()
    
    return mock_service


@pytest.fixture
def mock_library_service():
    """Mock library service."""
    mock_service = Mock()
    
    mock_service.set_details = Mock(return_value={
        "name": "Test Library",
        "path": "/tmp/test-library",
        "description": "A test library"
    })
    
    mock_service.get_details = Mock(return_value={
        "name": "Test Library",
        "path": "/tmp/test-library",
        "description": "A test library"
    })
    
    mock_service.preview = Mock(return_value={
        "session_id": "test-session-123",
        "name": "Test Library",
        "path": "/tmp/test-library",
        "description": "A test library",
        "total_papers": 3
    })
    
    mock_service.create = Mock(return_value={
        "session_id": "test-session-123",
        "name": "Test Library",
        "base_path": "/tmp/test-library",
        "total_requested": 3,
        "saved_count": 3,
        "papers": []
    })
    
    return mock_service


@pytest.fixture
def mock_zotero_service():
    """Mock Zotero service."""
    mock_service = Mock()
    
    mock_service.check_zotero_availability = Mock(return_value=(True, None))
    
    mock_service.get_collections = Mock(return_value=[
        {
            "key": "ABC123",
            "name": "Machine Learning Papers",
            "num_items": 10
        },
        {
            "key": "DEF456",
            "name": "NLP Research",
            "num_items": 5
        }
    ])
    
    sample_items = [
        SimpleNamespace(
            zotero_key="ITEM001",
            collection_key="ABC123",
            title="Sample Zotero Paper",
            authors=["Author One", "Author Two"],
            year=2020,
            publication="Zotero Journal",
            doi="10.1234/zotero.1",
            url="https://example.com/zotero1",
            abstract="Sample abstract",
        )
    ]
    mock_service.get_collection_items = Mock(return_value=("Machine Learning Papers", sample_items))
    mock_service.stage_items = Mock(return_value=len(sample_items))
    mock_service.get_staged_items = Mock(return_value=sample_items)
    mock_service.remove_staged_item = Mock()
    mock_service.match_staged_items = Mock(return_value=[])
    mock_service.get_confirmed_seeds = Mock(return_value=[])
    mock_service.clear_staging = Mock()
    mock_service._collections_cache = {}
    mock_service._match_results_storage = {}
    mock_service._manual_selections_storage = {}
    
    return mock_service


@pytest.fixture
def mock_pdf_service():
    """Mock PDF service."""
    mock_service = Mock()
    
    mock_service.check_grobid_availability = Mock(return_value=(True, None))
    
    metadata = SimpleNamespace(
        filename="test.pdf",
        title="Extracted Paper Title",
        authors="Author One, Author Two",
        year=2020,
        venue="Test Venue",
        doi="10.1234/example",
    )
    
    mock_service.upload_pdfs = Mock(return_value={
        "upload_id": "pdf-upload-123",
        "filenames": ["test.pdf"],
        "total_files": 1,
        "created_at": datetime.utcnow()
    })
    mock_service.extract_metadata = Mock(return_value={
        "upload_id": "pdf-upload-123",
        "results": [
            {
                "filename": metadata.filename,
                "success": True,
                "metadata": {
                    "filename": metadata.filename,
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "year": metadata.year,
                    "doi": metadata.doi,
                    "venue": metadata.venue,
                }
            }
        ],
        "successful_count": 1,
        "failed_count": 0
    })
    mock_service.review_metadata = Mock(return_value=None)
    mock_service.match_against_api = Mock(return_value={
        "upload_id": "pdf-upload-123",
        "results": [
            {
                "filename": metadata.filename,
                "metadata": {
                    "filename": metadata.filename,
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "year": metadata.year,
                    "doi": metadata.doi,
                    "venue": metadata.venue,
                },
                "matched": True,
                "paper_id": "W2741809807",
                "title": metadata.title,
                "authors": metadata.authors,
                "year": metadata.year,
                "venue": metadata.venue,
                "confidence": 0.95,
                "match_method": "doi",
            }
        ],
        "matched_count": 1,
        "unmatched_count": 0
    })
    mock_service.get_reviewed_metadata = Mock(return_value=[metadata])
    mock_service.cleanup_session = Mock()
    mock_service.get_matched_seeds = Mock(return_value=[
        {
            "paper_id": "W2741809807",
            "title": "Attention Is All You Need",
            "authors": metadata.authors,
            "year": metadata.year,
            "venue": metadata.venue,
            "confidence": 0.95,
            "match_method": "doi",
            "source_id": "W2741809807",
        }
    ])
    
    return mock_service


@pytest.fixture
def mock_crawler_execution_service():
    """Mock crawler execution service."""
    mock_service = Mock()
    mock_service.get_job_status = Mock(return_value={"status": "completed"})
    mock_service.start_crawler = Mock(return_value="job_mock")
    mock_service.get_results = Mock(return_value=None)
    return mock_service


@pytest.fixture
def mock_paper_catalog_service():
    """Mock paper catalog service."""
    mock_service = Mock()
    default_summary = PaperSummary(
        paper_id="W1",
        title="Sample Paper",
        authors=["Alice"],
        venue="TestConf",
        year=2021,
        doi="10.1000/sample",
        url="https://example.org/W1",
        citation_count=5,
        centrality_in=0.1,
        centrality_out=0.2,
        is_seed=True,
        is_retracted=False,
        selected=False,
        mark="standard",
        nmf_topic=1,
        lda_topic=None,
    )
    default_response = PaginatedPaperSummaries(
        page=1,
        page_size=25,
        total=1,
        papers=[default_summary],
        column_options={
            "title": [ColumnFilterOption(value="Sample Paper", label="Sample Paper", count=1)]
        },
    )
    mock_service.list_papers = Mock(return_value=default_response)
    column_page = ColumnOptionsPage(
        column="title",
        page=1,
        page_size=50,
        total=1,
        options=[ColumnFilterOption(value="Sample Paper", label="Sample Paper", count=1)],
    )
    mock_service.list_column_options = Mock(return_value=column_page)
    mock_service.export_catalog = Mock(return_value=b"excel-bytes")
    mock_service.update_mark = Mock(
        return_value=PaperMarkResponse(paper_id="W1", mark="good")
    )
    return mock_service


@pytest.fixture
def mock_paper_metadata_service():
    """Mock paper metadata service."""
    mock_service = Mock()
    detail = PaperDetail(
        paper_id="W1",
        title="Sample Paper",
        abstract="Example abstract",
        authors=["Alice"],
        institutions=["Example University"],
        year=2021,
        venue="TestConf",
        doi="10.1000/sample",
        url="https://example.org/W1",
        cited_by_count=5,
        references_count=10,
    )
    mock_service.get_paper_details = Mock(return_value=detail)
    return mock_service


@pytest.fixture
def mock_integration_settings_service():
    """Mock integration settings service."""
    mock_service = Mock()

    state = {
        "openalex": {
            "email": None,
            "configured": False
        },
        "zotero": {
            "library_id": None,
            "library_type": "user",
            "has_api_key": False,
            "configured": False
        }
    }

    def clone_state():
        return {
            "openalex": {
                "email": state["openalex"].get("email"),
                "configured": state["openalex"].get("configured", False),
            },
            "zotero": {
                "library_id": state["zotero"].get("library_id"),
                "library_type": state["zotero"].get("library_type", "user"),
                "has_api_key": state["zotero"].get("has_api_key", False),
                "configured": state["zotero"].get("configured", False),
            },
        }

    mock_service.get_settings = Mock(side_effect=clone_state)

    def update_openalex(payload):
        state["openalex"]["email"] = payload.email
        state["openalex"]["configured"] = bool(payload.email)
        return clone_state()

    def update_zotero(payload):
        state["zotero"]["library_id"] = payload.library_id
        state["zotero"]["library_type"] = payload.library_type or "user"
        has_key = bool(payload.api_key)
        state["zotero"]["has_api_key"] = has_key
        state["zotero"]["configured"] = bool(payload.library_id and has_key)
        return clone_state()

    mock_service.update_openalex = Mock(side_effect=update_openalex)
    mock_service.update_zotero = Mock(side_effect=update_zotero)
    
    return mock_service


@pytest.fixture(autouse=True)
def mock_api_provider():
    """Mock ArticleCrawler API provider."""
    with patch('ArticleCrawler.api.api_factory.create_api_provider') as mock:
        provider = Mock()
        provider.fetch_paper_metadata = AsyncMock(return_value={
            "paper_id": "W2741809807",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani"],
            "year": 2017
        })
        mock.return_value = provider
        yield mock


@pytest.fixture(autouse=True)
def mock_pdf_matcher():
    """Mock PDF metadata matcher."""
    with patch('ArticleCrawler.pdf_processing.api_matcher.APIMetadataMatcher') as mock:
        matcher = Mock()

        def match_metadata(metadata_list):
            results = []
            for meta in metadata_list:
                paper_id = getattr(meta, "doi", None) or "W2741809807"
                results.append(
                    SimpleNamespace(
                        metadata=meta,
                        matched=True,
                        paper_id=paper_id if paper_id.startswith("W") else "W2741809807",
                        confidence=0.95,
                        match_method="doi" if getattr(meta, "doi", None) else "title",
                    )
                )
            return results

        matcher.match_metadata = Mock(side_effect=match_metadata)
        mock.return_value = matcher
        yield mock


@pytest.fixture(autouse=True)
def reset_container():
    """Reset dependency injection container between tests."""
    yield
