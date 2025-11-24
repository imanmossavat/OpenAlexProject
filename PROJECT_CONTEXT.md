# ArticleCrawler FastAPI Backend - Project Context

## Project Overview

We are building a **FastAPI backend** for the ArticleCrawler CLI tool to enable web-based access to its functionality. The backend follows **SOLID principles** and provides a RESTful API.

### Current Status: ✅ Seed Selection Module Complete

We have successfully implemented the **Seed Selection** workflow for the Crawler Wizard use case, which includes:
- ✅ Paper ID matching against APIs
- ✅ Session-based seed management
- ✅ PDF upload and metadata extraction (5-step workflow)

---

## Architecture & Design Principles

### 1. SOLID Architecture

The backend is organized following SOLID principles:

```
app/
├── core/                   # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── container.py       # Dependency injection container
│   ├── exceptions.py      # Custom exceptions
│   └── logging.py         # Logging configuration
├── api/                   # API layer
│   ├── v1/
│   │   ├── router.py      # Main API router
│   │   ├── seeds.py       # Direct seed matching endpoints
│   │   ├── seed_sessions.py  # Session management endpoints
│   │   └── pdf_seeds.py   # PDF workflow endpoints
│   └── dependencies.py    # Dependency injection
├── services/              # Business logic (Use ArticleCrawler)
│   ├── seed_selection_service.py    # Shared seed matching service
│   ├── seed_session_service.py      # Session management service
│   └── pdf_seed_service.py          # PDF workflow service
├── schemas/               # Pydantic models (API contracts)
│   ├── seeds.py          # Seed-related schemas
│   ├── seed_session.py   # Session schemas
│   └── pdf_seeds.py      # PDF workflow schemas
└── main.py               # FastAPI application entry point
```

### 2. Key Design Decisions

**Services are thin wrappers around ArticleCrawler:**
- Services delegate heavy lifting to ArticleCrawler
- Only handle: format conversion, session management, API adaptation
- Don't duplicate ArticleCrawler functionality

**Shared services for reusability:**
- `SeedSelectionService` is used by multiple use cases (crawler wizard, library creation)
- Session-based approach allows multi-step workflows across HTTP requests

**Environment Configuration:**
```env
ARTICLECRAWLER_PATH=F:/OpenAlexProject/fakenewscitationnetwork
OPENALEX_EMAIL=your.email@example.com
```

ArticleCrawler is imported as: `from ArticleCrawler.module.file import Class`

---

## Implemented Features

### 1. Paper ID Seed Matching

**Endpoint:** `POST /api/v1/seeds/paper-ids`

**What it does:**
- Accepts list of paper IDs (OpenAlex, DOI, S2)
- Matches against API (OpenAlex or Semantic Scholar)
- Uses ArticleCrawler's `create_api_provider()` and `get_paper_metadata_only()`
- Returns matched seeds with metadata (title, authors, year, venue)

**Key implementation detail:**
- Uses `get_paper_metadata_only()` instead of `get_paper()` to avoid fetching citations (much faster!)

**Example request:**
```json
{
  "paper_ids": ["W2741809807", "10.1109/TBME.2020.3013489"],
  "api_provider": "openalex"
}
```

---

### 2. Seed Session Management

**Purpose:** Allow users to collect seeds from multiple sources before proceeding

**Endpoints:**
```
POST   /api/v1/seeds/session/start
GET    /api/v1/seeds/session/{session_id}
POST   /api/v1/seeds/session/{session_id}/paper-ids
POST   /api/v1/seeds/session/{session_id}/seeds
DELETE /api/v1/seeds/session/{session_id}/seeds/{paper_id}
POST   /api/v1/seeds/session/{session_id}/finalize
DELETE /api/v1/seeds/session/{session_id}
```

**Session Storage:**
- Currently in-memory (dict)
- Auto-deduplicates seeds by paper_id

**Workflow:**
1. Start session → get session_id
2. Add seeds from multiple sources (paper IDs, PDFs, Zotero)
3. View all seeds in session
4. Finalize when ready → proceed to next step (keywords, config)

---

### 3. PDF Seed Selection (5-Step Workflow)

**Full workflow matching ArticleCrawler CLI:**

#### Step 1: Upload PDFs
**Endpoint:** `POST /api/v1/seeds/session/{session_id}/pdfs/upload`
- Upload up to 20 PDFs (max 10MB each)
- Checks GROBID availability first
- Stores files temporarily
- Returns upload_id

#### Step 2: Extract Metadata
**Endpoint:** `POST /api/v1/seeds/session/{session_id}/pdfs/{upload_id}/extract`
- Uses ArticleCrawler's `PDFProcessor.process_pdfs()`
- ArticleCrawler handles:
  - GROBID processing
  - Temp file management (auto-cleanup)
  - XML metadata extraction
- Returns extracted metadata for each PDF

#### Step 3: Review Metadata
**Endpoint:** `POST /api/v1/seeds/session/{session_id}/pdfs/{upload_id}/review`
- User can accept/edit/skip each PDF
- Example request:
```json
{
  "reviews": [
    {"filename": "paper1.pdf", "action": "accept"},
    {"filename": "paper2.pdf", "action": "edit", "edited_metadata": {...}},
    {"filename": "paper3.pdf", "action": "skip"}
  ]
}
```

#### Step 4: Match Against API
**Endpoint:** `POST /api/v1/seeds/session/{session_id}/pdfs/{upload_id}/match`
- Uses ArticleCrawler's `APIMetadataMatcher`
- Tries DOI first, then title search
- Returns match results with confidence scores

#### Step 5: Confirm Seeds
**Endpoint:** `POST /api/v1/seeds/session/{session_id}/pdfs/{upload_id}/confirm`
- User chooses: "use_all" or "skip_all"
- Adds matched seeds to session
- Cleans up temp files

**Key implementation details:**
- `PDFSeedService` is a thin wrapper around ArticleCrawler
- ArticleCrawler handles: GROBID, temp files, extraction, matching
- Our service handles: storing uploads between API calls, format conversion, session management

---

## ArticleCrawler Integration

### Import Patterns

```python
# API
from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.api.base_api import BaseAPIProvider

# PDF Processing
from ArticleCrawler.pdf_processing.pdf_processor import PDFProcessor
from ArticleCrawler.pdf_processing.docker_manager import DockerManager
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher

# Validation
from ArticleCrawler.cli.ui.validators import validate_paper_id
```

### What ArticleCrawler Handles (Don't Duplicate!)

**PDF Processing:**
- ✅ GROBID availability check: `DockerManager.is_grobid_running()`
- ✅ GROBID processing with temp file management: `GrobidClientWrapper.process_pdfs()`
- ✅ Metadata extraction from XML: `PDFMetadataExtractor.extract()`
- ✅ Complete pipeline: `PDFProcessor.process_pdfs()`

**API Matching:**
- ✅ Paper retrieval: `api.get_paper_metadata_only()` (fast, no citations)
- ✅ PDF metadata matching: `APIMetadataMatcher.match_metadata()`
- ✅ Rate limiting built-in

**Temp File Management:**
- ✅ `GrobidClientWrapper` uses `tempfile.TemporaryDirectory()` - auto-cleanup!
- ❌ Don't create temp dirs for GROBID processing (ArticleCrawler does it)
- ✅ Only store uploaded files between HTTP requests

---

## Dependency Injection

Using `dependency-injector` library:

**Container (`app/core/container.py`):**
```python
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    logger = providers.Singleton(logging.getLogger, "ArticleCrawlerAPI")
    
    seed_selection_service = providers.Factory(SeedSelectionService, logger=logger)
    seed_session_service = providers.Singleton(SeedSessionService, logger=logger)
    pdf_seed_service = providers.Singleton(PDFSeedService, logger=logger)
```

**Dependencies (`app/api/dependencies.py`):**
```python
@inject
async def get_seed_selection_service(
    service=Depends(Provide[Container.seed_selection_service])
):
    return service
```

**Wiring in `main.py`:**
```python
container.wire(modules=[
    "app.api.v1.router",
    "app.api.v1.seeds",
    "app.api.v1.seed_sessions",
    "app.api.v1.pdf_seeds",
    "app.api.dependencies",
])
```

---

## Error Handling

**Custom Exceptions (`app/core/exceptions.py`):**
```python
class CrawlerException(Exception): pass
class InvalidInputException(CrawlerException): pass
class LibraryNotFoundException(CrawlerException): pass

def to_http_exception(e: Exception) -> HTTPException:
    if isinstance(e, InvalidInputException):
        return HTTPException(status_code=400, detail=str(e))
    elif isinstance(e, LibraryNotFoundException):
        return HTTPException(status_code=404, detail=str(e))
    # ...
```

**Usage in endpoints:**
```python
@router.post("/endpoint")
async def endpoint(service = Depends(get_service)):
    try:
        return service.do_something()
    except Exception as e:
        raise to_http_exception(e)
```

---

## Testing the Implemented Features

### 1. Test Paper ID Matching
```bash
curl -X POST "http://localhost:8000/api/v1/seeds/paper-ids" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["W2741809807"],
    "api_provider": "openalex"
  }'
```

### 2. Test Session Workflow
```bash
# Start session
curl -X POST "http://localhost:8000/api/v1/seeds/session/start" \
  -H "Content-Type: application/json" \
  -d '{"use_case": "crawler_wizard"}'

# Add paper IDs to session
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/paper-ids" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["W2741809807"],
    "api_provider": "openalex"
  }'

# View session
curl "http://localhost:8000/api/v1/seeds/session/{session_id}"

# Finalize
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/finalize"
```

### 3. Test PDF Workflow
```bash
# 1. Upload
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/pdfs/upload" \
  -F "files=@paper1.pdf" \
  -F "files=@paper2.pdf"

# 2. Extract
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/pdfs/{upload_id}/extract"

# 3. Review
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/pdfs/{upload_id}/review" \
  -H "Content-Type: application/json" \
  -d '{
    "reviews": [
      {"filename": "paper1.pdf", "action": "accept"},
      {"filename": "paper2.pdf", "action": "accept"}
    ]
  }'

# 4. Match
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/pdfs/{upload_id}/match" \
  -F "api_provider=openalex"

# 5. Confirm
curl -X POST "http://localhost:8000/api/v1/seeds/session/{session_id}/pdfs/{upload_id}/confirm" \
  -H "Content-Type: application/json" \
  -d '{"action": "use_all"}'
```

---

## Next Steps (Not Yet Implemented)

### 1. Zotero Seed Selection
- List Zotero collections
- Select items from collection
- Match against API
- Add to session

### 2. Keywords & Expressions
- Add keyword filters
- Validate expressions (balanced parentheses)
- Support boolean operators

### 3. Crawler Configuration
- Basic config (max iterations, papers per iteration)
- Advanced config (algorithm, topics, author nodes)

### 4. Start Crawling
- Execute crawler with all collected config
- Return job ID for monitoring

---

## Important Notes for Continuation

### DO:
✅ Always delegate to ArticleCrawler for core functionality
✅ Services should be thin wrappers (format conversion, session management)
✅ Use `get_paper_metadata_only()` instead of `get_paper()` when you don't need citations
✅ Follow SOLID principles - single responsibility per service
✅ Use dependency injection for all services
✅ Handle errors with custom exceptions + `to_http_exception()`

### DON'T:
❌ Don't duplicate ArticleCrawler functionality
❌ Don't create temp files for GROBID (ArticleCrawler handles it)
❌ Don't fetch citations when you only need metadata
❌ Don't forget to wire new modules in main.py
❌ Don't make services too complex - delegate to ArticleCrawler

### Code Style:
- Use type hints everywhere
- Pydantic models for all API contracts
- Descriptive variable names
- Comprehensive docstrings
- Follow existing patterns in implemented code

---

## Files to Reference

All implemented code is in the project. Key files:
- `app/main.py` - Application entry point
- `app/core/container.py` - DI container
- `app/services/seed_selection_service.py` - Seed matching logic
- `app/services/seed_session_service.py` - Session management
- `app/services/pdf_seed_service.py` - PDF workflow
- `app/api/v1/*.py` - API endpoints
- `app/schemas/*.py` - Pydantic models

Backend tree structure is in `BACKEND_TREE.txt`.
ArticleCrawler structure is in the project's `Tree` file.

---

## Current Working State

- ✅ FastAPI app runs on port 8000
- ✅ GROBID must be running on port 8070 for PDF features
- ✅ All seed selection endpoints tested and working
- ✅ Sessions stored in-memory
- ✅ Environment variables configured in `.env`

**Ready to continue with:** Zotero integration OR Keywords module OR Configuration module
