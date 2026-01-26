# Mega Prompts for Debugging
Paste the relevant block into an LLM, fill in the “Problem” description, and the assistant will know the architecture, key classes, and diagnostics to reference.

---

## General Prompt (Full Stack)

```
You are assisting with the OpenAlex ArticleCrawler stack. Components:
1. Python crawler in `fakenewscitationnetwork/ArticleCrawler/` (service-oriented architecture with API providers, DataCoordinator, FrameManager/DataFrameStore, GraphManager + GraphProcessing, Sampler, TextAnalysisManager, RetractionWatchManager, DataStorage/markdown writers, CLI entrypoints). Config classes map legacy options to dataclasses: CrawlerParameters, SamplingConfig, TextProcessingConfig, GraphConfig, StorageAndLoggingConfig (see folders_all map), RetractionConfig, StoppingConfig.
2. FastAPI backend in `article-crawler-backend/app/` (routers under `app/api/v1`, dependency injection in `app/api/dependencies.py`, services in `app/services` covering crawler execution/rerun, staging, seeds, keywords, configuration/settings, library, pdf ingestion, manual metadata, retraction, topics, workflows, zotero). Infrastructure lives under `app/core` (config loader, DI container, BackgroundJobExecutor, crawler job store, seed session store, pdf upload store). Retraction cache resides in `retraction_cache/` (CSV + `retraction_watch_version.txt`).
3. React + Vite frontend in `frontend/src/` (workflows defined in `shared/workflows/*.js` for crawler creation, rerun, library creation/edit, author topics; API client in `shared/api/client.js`; session helpers in `shared/lib/session.js`; reusable components in `components/` such as Layout/Header/Footer/Stepper/PaperDetailModal; pages grouped under `pages/workflow`, `pages/create`, `pages/author`, `pages/help`, `pages/about`).

Documentation references: `docs/system-overview.md`, `docs/components/*.md`, `docs/handover/structure-map.md`, `Installation guide.md`.

Vault outputs: every crawl writes to `fakenewscitationnetwork/experiments/.../vault/`. Each vault contains markdown summaries (`*_table_*`, `summary/top_authors.md`, etc.), topic markdown (`topics/`), PNG figures under `figures/<timestamp>/`, abstracts/papers folders, plus `run.md` + `README.md`. Folders are defined by `storage_config.folders_all` (experiment/pkl/log/vault/abstracts/figures/metadata/summary/xlsx/recommendation directories).

Constraints:
- Never expose `.env` contents or personal data (Sreedevi-specific info).
- `.venv` lives at repo root (created by `install.py`). Backend `.env` must point `ARTICLECRAWLER_PATH` at the crawler directory.
- Logs: crawler logs go to `StorageAndLoggingConfig.log_folder`; backend logs stream via Uvicorn/`ArticleCrawlerAPI`; frontend logs surface in the browser console or Vite dev server. Vault `run.md` captures crawler parameters/errors.

Problem summary: <describe cross-cutting symptom>

Request: Provide a step-by-step debugging plan referencing relevant modules (crawler configs/services, backend routers/services, frontend workflows/components), commands (`python -m pytest`, `uvicorn app.main:app --reload`, `npm run dev`, `docker compose up`), vault/log files to inspect, and integrity checks (df_forbidden_entries, retraction cache version, session JSON).
```

---

## Crawler Prompt

```
Context: Python crawler (`fakenewscitationnetwork/ArticleCrawler/`) orchestrates:
- API provider layer (`api/`) fetching OpenAlex data.
- DataCoordinator + FrameManager/DataFrameStore managing pandas frames (see below).
- GraphManager/GraphProcessing maintaining a NetworkX graph (centrality metrics inserted into df_derived_features).
- Sampler weighting papers based on centrality/year/keywords and avoiding df_forbidden_entries.
- TextAnalysisManager (preprocessing, vectorization, topic modeling, visualization) producing markdown + PNGs.
- RetractionWatchManager pulling the backend CSV and flagging retracted DOIs.
- DataStorage/markdown writers persisting vaults and checkpoints (`checkpoint/ResumeState`).

Key configs: `CrawlerParameters` (seed IDs/keywords), `SamplingConfig` (num_papers, `hyper_params`, `ignored_venues`, `no_keyword_lambda`), `TextProcessingConfig` (language, `abstract_min_length`, `num_topics`, `topic_model`, `save_figures`, `random_state`), `GraphConfig`, `StorageAndLoggingConfig` (defines `folders_all`), `RetractionConfig`, `StoppingConfig` (iteration/df size caps).

Storage folders (from `StorageAndLoggingConfig.folders_all`):
```
{
  'experiment_folder': <root>/experiments/<job>,
  'pkl_folder': .../pkl,
  'log_folder': .../log,
  'vault_folder': .../vault,
  'abstracts_folder': .../vault/abstracts,
  'figure_folder': .../vault/figures,
  'metadata_folder': .../vault/metadata,
  'summary_folder': .../vault/summary,
  'xlsx_folder': .../vault/xlsx,
  'recommendation_folder': .../vault/recommendations
}
```

Frame schemas to keep in mind:
```
df_paper_metadata columns = ['paperId','doi','venue','year','title','processed','isSeed','isKeyAuthor','selected','retracted']
df_paper_author = ['paperId','authorId']
df_author = ['authorName','authorId']
df_paper_citations = ['paperId','citedPaperId']
df_paper_references = ['paperId','referencePaperId']
df_citations = ['paperId','referencePaperId']
df_abstract = ['paperId','abstract']
df_derived_features = ['nodeId','centrality (in)','centrality (out)','attribute','nodeType']
df_forbidden_entries = ['paperId','reason','sampler','textProcessing','doi']
```

Artifacts/logs/tests:
- Logs: `CrawlerLogger` writes to `log_folder`.
- Vault: inspect `vault/run.md`, `vault/README.md`, `topics/`, `figures/`, `summary/`.
- Checkpoints: see `checkpoint/` payloads when resuming jobs.
- Tests: run `python -m pytest` from `fakenewscitationnetwork/` (unit + integration suites).

Problem: <crawler-specific issue — e.g., keyword parser regression, missing papers, topic modeling failure, resume bug>

Request: Identify which module might be malfunctioning (API provider, MetadataParser, DataCoordinator, GraphProcessing, Sampler, TextProcessing, RetractionWatchManager, StorageAndLoggingOptions). Suggest diagnostics (inspect DataFrame contents, rerun CLI commands under `ArticleCrawler/cli`, verify `storage_config.folders_all`, check `df_forbidden_entries`, review logs/figures). Provide commands and file paths to inspect while avoiding personal Sreedevi data and keeping outputs frontend-compatible.
```

---

## Backend Prompt

```
Context: FastAPI backend (`article-crawler-backend/app/`). Structure:
- Routers (`app/api/v1/*.py`): crawler execution/resume, crawler rerun, seed sessions, seeds, keywords, configuration, settings, staging, library, pdf seeds, zotero seeds, papers, topics, author topic evolution, manual metadata.
- Dependencies (`app/api/dependencies.py`): DI wiring for services, stores, settings.
- Services (`app/services/`):
  * `crawler/` (config_builder, job_runner, progress, result_assembler, entity_papers_builder).
  * `crawler_execution_service.py`, `crawler_rerun_service.py` orchestrate jobs.
  * `staging/` (repository, query_parser, match_service, retraction_updater, row_manager, session_store).
  * `seeds/`, `keyword/`, `configuration_service.py`, `settings`, `integration_settings_service.py` manage wizard data.
  * `library/`, `pdf/`, `manual_metadata/`, `providers/`, `zotero/` handle external data ingestion.
  * `retraction/` loads `retraction_cache/retraction_watch.csv` and tracks versions.
  * `topics/`, `author_topic_evolution_service.py` read vaults for analytics.
- Core infrastructure (`app/core/`): config loader, bootstrap/container, exceptions, `executors/background.py`, stores (`crawler_job_store.py`, `seed_session_store.py`, `pdf_upload_store.py`), storage helpers.
- Repositories: `experiment_repository.py`, `paper_catalog_repository.py`, `paper_annotation_repository.py`.
- `.env` (generated by `install.py` or Docker) supplies `ARTICLECRAWLER_PATH`, `STORAGE_ROOT`, `OPENALEX_EMAIL`, `ZOTERO_*`, `GROBID_URL`.

Artifacts/logs/tests:
- API docs: `http://localhost:8000/api/v1/docs`.
- Logs: Uvicorn + `ArticleCrawlerAPI` logger (watch crawler job logs for status transitions).
- Job metadata: inspect `app/core/stores/crawler_job_store.py` (default in-memory) for iteration counts, status, error messages, config snapshots.
- Uploaded artifacts: `article-crawler-backend/uploaded_dumps/` and experiment folders referenced in job snapshots.
- Tests: `cd article-crawler-backend && python -m pytest`.

Problem: <backend-specific issue — e.g., job stuck at “saving”, rerun fails with manual frontier, staging filters broken, retraction cache mismatch, library upload errors>

Request: Point to relevant routers/services/modules (e.g., `crawler_execution.py`, `services/crawler/job_runner.py`, `services/staging/query_parser.py`, `services/retraction/cache_loader.py`, `services/library/service.py`, `services/zotero`). Recommend diagnostics (curl/HTTPie commands, inspect job store state, verify `.env` paths, check `retraction_cache/retraction_watch_version.txt`, review staging repository files). Suggest pytest targets when possible. Ensure advice keeps vault outputs intact and avoids leaking secrets.
```

---

## Frontend Prompt

```
Context: React + Vite frontend (`frontend/`). Structure:
- Entry: `main.jsx` + `App.jsx` with router from `src/app/router.jsx`.
- Workflows: `src/shared/workflows/*.js` defines steps for crawler creation, crawler rerun, library creation/edit, author topic analytics. Each workflow lists API endpoints, progress states, and wizard labels.
- Shared helpers: `shared/api/client.js` (fetch wrapper, auto-restart library sessions), `shared/api/endpoints.js`, `shared/config/env.js`, `shared/lib/session.js`, `shared/lib/time.js`, `shared/lib/utils.js`, `hooks/use-toast.js`.
- Components: Layout, Header, Footer, Stepper, PaperDetailModal, column filter widgets, other UI pieces in `src/components/`.
- Pages: `pages/workflow/WorkflowPage.jsx` (main wizard + rerun UI), `pages/create/*` (library/PDF onboarding + edit flows), `pages/author/*` (topic selection/results/evolution with markmap styles under `src/styles/markmap.css`), `pages/help/GrobidSetupPage.jsx`, `pages/about/AboutPage.jsx`, plus supporting pages for other workflows.
- Assets: `src/assets/` currently holds logos/icons; future Sreedevi presentation images or video thumbnails go here.
- Environment: `frontend/.env` sets `VITE_API_URL` (defaults to `http://localhost:8000`).

Artifacts/logs/tests:
- Dev server logs via `npm run dev`.
- Browser console/network tab for API responses.
- Build verification via `npm run build`.

Problem: <frontend-specific issue — e.g., workflow step doesn’t advance, rerun prompts wrong API, author topic chart blank, library edit state resets>

Request: Identify likely sources (workflow definitions, API client/endpoints, session storage, specific page/component). Suggest debugging steps: inspect `shared/workflows/*.js`, log API responses in `shared/api/client.js`, check localStorage for session IDs, verify `VITE_API_URL`. Recommend `npm run lint`/`npm run build` to catch compile errors. Ensure instructions mention where to add instrumentation (e.g., Stepper, PaperDetailModal) and respect asset/privacy constraints.
```

---
