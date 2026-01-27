# Backend Component (`article-crawler-backend/`)

FastAPI exposes every crawler capability over HTTP so the frontend (and external automations) can seed jobs, monitor progress, download vaults, and administer metadata. The backend is intentionally modular: routers (`app/api/v1/*.py`) stay thin, while services orchestrate crawler runs, staging, retraction cache management, and library uploads.

## Project Layout & Primary Modules

| Module | Purpose |
| ------ | ------- |
| `app/main.py` | FastAPI application factory. Mounts `/api/v1`, configures CORS, logging, and lifespan hooks (e.g., loading retraction cache hashes). |
| `app/api/dependencies.py` | Dependency injection container; wires routers to service singletons (crawler execution, staging, keyword management, etc.). |
| `app/api/v1` | Versioned routers. Each file handles a domain: `seeds.py`, `seed_sessions.py`, `crawler_execution.py`, `crawler_rerun.py`, `library.py`, `papers.py`, `topics.py`, `author_topic_evolution.py`, etc. |
| `app/services` | Business logic. Each subpackage (e.g., `crawler`, `staging`, `keyword`, `library`, `retraction`, `providers/zotero`) encapsulates workflows and persistence. |
| `app/core` | Infrastructure (background executor, job stores, settings loader, file utilities). |
| `retraction_cache/` | Includes `retraction_watch.csv` plus `retraction_watch_version.txt`. Updated via scripts or manual sync; backend loads it into memory to flag retracted IDs quickly. |
| `uploaded_dumps/` | Temporary folder for zipped vault deliveries and staged PDF uploads. |
| `tests/` | API + service tests (pytest).

## Router Overview

- **`crawler_execution.py`** – Start new jobs (`POST /{session_id}/start`), resume existing ones, fetch job lists/status, and expose topic/entity drill-down endpoints (`/jobs/{job_id}/topics/{topic_id}`).
- **`crawler_rerun.py`** – Provide lightweight reruns of stored jobs using manual overrides for sampling or targeted resume operations.
- **`seed_sessions.py`**, **`seeds.py`**, **`keywords.py`** – Manage the multi-step wizard used in the frontend. Sessions capture seeds, keywords, configuration state, and are stored via `SeedSessionService` (file- or database-backed depending on provider implementation).
- **`library.py`**, **`pdf_seeds.py`**, **`zotero_seeds.py`** – Handle ingestion of local PDF libraries or Zotero exports (`providers/zotero`). They normalize metadata and feed it into the seed session pipeline.
- **`papers.py`** – Expose paginated paper summaries, column metadata, and marking endpoints for curation workflows.
- **`author_topic_evolution.py`** – Serve time-series topic data for a selected author, reusing crawler vault outputs and `topics` services.
- **`configuration.py`**, **`settings.py`** – Save/retrieve session-scoped configuration (hyperparameters, ignored venues, text processing choices).
- **`staging.py`** – Provide filtered previews (search, sort, mark) of harvested seeds.

## Crawler Execution Pipeline

The heart of the backend lives under `app/services/crawler` & `app/services/crawler_execution_service.py`:

1. **Config building (`CrawlerConfigBuilder`)** – Takes `session_data` and resolves paths for experiments, vault folders, and `.env` data. It also translates session JSON into the config dataclasses consumed by the Python crawler (`CrawlerParameters`, `SamplingConfig`, etc.).
2. **Job runner (`CrawlerJobRunner`)** – Spawns the `ArticleCrawler` process inside the backend environment. It injects a `progress_callback` so we can update status each time the crawler finishes an iteration or subtask.
3. **Progress snapshots** – `CrawlerProgressSnapshot` (in `app/services/crawler`) converts crawler callbacks into API-friendly dictionaries (iterations completed, papers added, etc.).
4. **Job store (`app/core/stores/crawler_job_store.py`)** – Default is in-memory, but the interface allows Redis/database-backed implementations. Each job retains: config snapshot, session metadata, timestamps, iteration counters, error messages, and references to the vault folder.
5. **Background executor (`app/core/executors/background.py`)** – Wraps `concurrent.futures.ThreadPoolExecutor` to keep crawler runs asynchronous; API responses return immediately with `job_id`.
6. **Result assembly (`CrawlerResultAssembler`)** – After completion, ensures figures + markdown exist, and readies them for download endpoints.

Resuming jobs uses the same components but supplies `resume_payload` (checkpoint path + manual frontier) to `CrawlerJobRunner`. `crawler_execution.py` exposes this via `POST /jobs/{job_id}/resume`.

## Retraction & Validation

- The backend’s `retraction` services watch `retraction_cache/retraction_watch.csv`. `RetractionCacheLoader` hashes the CSV so updates can be detected (version recorded in `retraction_watch_version.txt`).
- When a new CSV is staged, call the service endpoint or CLI to rebuild the cache—affected papers are flagged in API responses and passed down to the crawler through `RetractionConfig` so they land in `df_forbidden_entries`.

## Staging, Seeds, and Libraries

- **Seed sessions** persist to disk (JSON) by default. Each session stores seeds (`SeedModel`), keywords, config wizard progress, and pointers to uploaded PDFs.
- **Staging service (`app/services/staging`)** indexes candidate seeds with flexible filters. `StagingQueryParser` (in `app/services/staging/query_parser.py`) interprets complex filter expressions (AND/OR, range queries) so the frontend can apply spreadsheet-like filtering.
- **Library & PDF ingestion** normalizes external inputs: `library_service` handles library imports, `pdf` service extracts metadata, and `providers/zotero` syncs with Zotero API keys stored in the `.env`.

## Settings & Providers

- `app/services/settings` merges `.env` values and defaults (ports, storage roots, ArticleCrawler path, feature flags).
- Provider modules under `app/services/providers` wrap third-party APIs (e.g., Zotero). They include test doubles for easier integration testing.

## Observability & Logging

- `logging.ini` the settings module configure the `ArticleCrawlerAPI` logger. Each router obtains a child logger for contextual info.
- Background jobs log to the same sink; `CrawlerExecutionService` uses `logging.LoggerAdapter` to append `job_id` to log records.
- Health endpoints (see `settings.py` router) allow Kubernetes/Docker to ensure the API is healthy and has loaded settings.

## Configuration & Environment

- `.env` at the backend root is generated by `install.py`. Key variables: `ARTICLECRAWLER_PATH`, `STORAGE_ROOT`, `OPENALEX_EMAIL`, `ZOTERO_*`, `GROBID_URL`.
- Docker Compose runs `python install.py --non-interactive --env-only`, so containers always boot with fresh `.env` files; volumes expose vault output directories back to the host.

## Testing & Local Development

- Activate the repo’s `.venv`, `cd article-crawler-backend`, then run `pytest` to execute service/router tests.
- Use `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` to run locally. Swagger UI at `/api/v1/docs` provides request samples for every router.


## Module Reference


### API Layer
- `app/main.py` – FastAPI factory; configures middleware, startup/shutdown hooks, router mounting.
- `app/api/__init__.py` & `router.py` – Compose versioned routers and include them in the app.
- `app/api/dependencies.py` – Dependency injection wiring. Provides singleton instances of services (crawler execution, seed sessions, settings, etc.) and enforces environment validation.
- `app/api/routes_helpers/` – Shared helpers for streaming responses, file attachments, and error normalization used across routers.
- `app/api/v1/*.py` – Each router file maps directly to a business capability:
  - `crawler_execution.py`, `crawler_rerun.py` – Job lifecycle endpoints.
  - `seed_sessions.py`, `seeds.py`, `keywords.py`, `settings.py`, `configuration.py` – Wizard orchestration.
  - `library.py`, `pdf_seeds.py`, `zotero_seeds.py` – Library ingestion/upload flows.
  - `papers.py`, `author_topic_evolution.py`, `topics.py`, `staging.py` – Read models for UI browsing.
  - `crawler_rerun.py`, `manual_metadata.py` – Administrative routes for re-running or patching metadata.

### Core Infrastructure
- `app/core/config.py` – Settings loader (reads `.env`, sets defaults, validates critical paths).
- `app/core/bootstrap.py` – Bootstraps dependency container; invoked at startup.
- `app/core/container.py` – Service registry used by `dependencies.py`.
- `app/core/exceptions.py` – Common exception types translated into HTTP errors.
- `app/core/executors/background.py` – `BackgroundJobExecutor` built on `ThreadPoolExecutor` for async crawler runs.
- `app/core/storage/` – Helpers for resolving storage roots, vault paths, and ensuring directories exist.
- `app/core/stores/` – Abstractions plus in-memory implementations for:
  - `crawler_job_store.py` – CRUD operations for job metadata.
  - `seed_session_store.py` – Session persistence (file-backed by default).
  - `pdf_upload_store.py` – Temporary metadata for uploaded PDFs until they become seeds.

### Models & Schemas
- `app/models/` – Internal models (Pydantic/BaseModel) for persistent entities (experiments, seed sessions, keywords).
- `app/schemas/` – API contract models (request/response validation). Includes `crawler_execution`, `seeds`, `keywords`, `library`, `topics`, etc.

### Repositories
- `experiment_repository.py` – Reads/writes experiment metadata (job folders, vault locations).
- `paper_catalog_repository.py` – Indexed paper summaries served via `papers.py`.
- `paper_annotation_repository.py` – Stores user annotations/marks applied through the UI.

### Services (Top-Level Files)
- `crawler_execution_service.py` – Orchestrates job lifecycle (start, resume, status, result assembly).
- `crawler_rerun_service.py` – Simplified rerun entrypoints.
- `configuration_service.py`, `settings/service.py` – Persist wizard configuration / global feature flags.
- `integration_settings_service.py` – Manage integration toggles (e.g., Zotero, GROBID).
- `paper_metadata_service.py` – Aggregates metadata for UI downloads.
- `source_file_service.py` / `source_files/` – File upload helpers.
- `manual_metadata/` – Tools for editing metadata manually when automated ingestion fails.

### Crawler Subservices (`app/services/crawler/`)
- `config_builder.py` – Builds `CrawlerRunInputs` from session data and resolves filesystem paths.
- `job_runner.py` – Wraps the Python crawler invocation; injects progress callbacks and resume payloads.
- `progress.py` – `CrawlerProgressSnapshot` plus helpers to map progress events into job store updates.
- `entity_papers_builder.py` – Constructs topic/entity-specific paper lists for analytics endpoints.

### Staging & Session Management (`app/services/staging/` + `.../seeds/`)
- `staging/service.py` – Entry point for staging queries (filtering, sorting, marking). Uses:
  - `repository.py` – On-disk storage of staging rows.
  - `query_parser.py`, `query_service.py`, `query_utils.py` – Parse spreadsheet-like filter syntax and execute it against staged data.
  - `match_service.py`, `matchers.py`, `identifier_utils.py` – Detect duplicates, map PDFs to OpenAlex IDs, and align library entries.
  - `retraction_updater.py` – Decorates rows with retraction info from the cache.
  - `row_manager.py` – Handles CRUD operations for staged rows.
  - `session_store.py` – Persists staging session metadata.
- `services/seeds/` – Manage seed entities, including `seed_service`, `seed_session_service`, and helpers for the wizard state machine.
- `services/keyword/`, `services/topics/`, `services/workflows/` – Domain-specific logic for keywords, topic outputs, and workflow metadata.

### Library, PDF, and Zotero Services
- `services/library/` – `LibraryService` for ingesting existing libraries, `LibraryWriter` for exporting new ones, `LibraryValidator` for rules enforcement.
- `services/pdf/` – PDF ingestion pipeline: extraction, deduplication, linking to sessions.
- `services/providers/` – External integrations (e.g., `providers/article_crawler.py` to talk to the Python package, `providers/zotero/` for Zotero API calls).
- `services/zotero/` – Higher-level logic for syncing Zotero collections into the crawler workflow.

### Retraction & Catalog Services
- `services/retraction/` – `RetractionCacheLoader`, version tracking, and update routines that sync `retraction_cache/retraction_watch.csv` into in-memory lookup tables.
- `services/catalog/` – Manage the consolidated paper catalog referenced by staging and analytics.
- `services/author_topic_evolution_service.py`, `services/topics/` – Build datasets for author/topic analytics pages (consuming crawler vaults).

### Utilities
- `app/utils/` – File helpers, response builders, environment detection. Includes utilities for zipped responses, checksum calculations, and markdown generation fallbacks.
