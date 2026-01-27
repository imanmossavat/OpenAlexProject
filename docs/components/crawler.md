# Crawler Component (`fakenewscitationnetwork/ArticleCrawler`)

The crawler is a full Python application that manages OpenAlex ingestion, iteratively expands citation networks, runs topic modeling, and writes everything to the "vault" directory structure consumed by the backend and frontend.

## Architectural Highlights

1. **Crawler orchestrator (`crawler.py`)** – Manages configuration objects, runs iterations, emits progress snapshots, and persists state using checkpoint helpers. Dependency injection lets the backend and CLI pass their own API providers, configs, or callbacks.
2. **API abstraction (`ArticleCrawler/api`)** – `create_api_provider` selects OpenAlex (default) or alternate providers; retry logic, batching, and pagination live here.
3. **Data services (`ArticleCrawler/data/…`)**
   - `PaperRetrievalService` fetches metadata, references, citations, and abstracts via the API layer.
   - `DataCoordinator` + `FrameManager` own the in-memory pandas frames.
   - `DataValidationService`/`paper_validator.py` enforce sanity (dedupe, ensure seeds exist, flag missing abstracts).
4. **Sampling (`ArticleCrawler/sampling/sampler.py`)** – Chooses the next frontier using keyword matches, graph centrality, author prominence, and forbidden lists.
5. **Graph & analytics**
   - `GraphManager` + `GraphProcessing` (`ArticleCrawler/graph`) maintain a NetworkX `DiGraph`, update centrality scores, and push node attributes back into the frames.
   - `TextAnalysisManager` (`ArticleCrawler/text_processing`) coordinates preprocessing, transformations, and topic modeling (NMF/LDA) before markdown/figure export.
6. **Retraction safety** – `papervalidation/retraction_watch_manager.py` reads `article-crawler-backend/retraction_cache` CSVs via the backend or local copy, updates `df_forbidden_entries`, and keeps retracted content out of sampling/text processing.
7. **Storage & Vault** – `StorageAndLoggingConfig` defines all folders (`experiment/`, `vault/`, `abstracts/`, `figures/`, etc.) and gets passed to helpers like `DataStorage`, `CrawlerLogger`, and `md_generator`.

## Key Classes & Configurations

| Component | Location | Notes |
| --------- | -------- | ----- |
| `Crawler` | `ArticleCrawler/crawler.py` | Accepts old `SamplingOptions`, etc., but now maps them into typed config classes (`APIConfig`, `SamplingConfig`, `GraphConfig`, `TextProcessingConfig`, `StorageAndLoggingConfig`, `RetractionConfig`, `StoppingConfig`). Handles dependency wiring and emits `progress_callback` updates.
| `CrawlerParameters` + options | `ArticleCrawler/config` | Encapsulate seeds, keyword expressions, sampling hyper-params, stopping criteria, graph toggles, logging folders.
| `PaperRetrievalService` | `ArticleCrawler/data/retrieval_service.py` | Batches OpenAlex calls, writes to `FrameManager` through `MetadataParser`.
| `FrameManager` / `DataFrameStore` | `ArticleCrawler/data/frame_manager.py`, `data_frame_store.py` | Provide typed properties for every DataFrame (with schema initialization) so tests can assert column availability.
| `Sampler` | `ArticleCrawler/sampling/sampler.py` | Centrality-aware weighted sampler that respects `df_forbidden_entries`, keyword filters, and manual frontier overrides.
| `TextAnalysisManager` | `ArticleCrawler/text_processing/__init__.py` | Wraps `text_pre_processing`, `text_transformation`, `text_topic_modeling`, and figure generation utilities.
| `GraphManager` | `ArticleCrawler/graph/graph_manager.py` | Maintains `DG`, recalculates eigenvector/katz centrality, syncs with metadata store after each iteration.
| `RetractionWatchManager` | `ArticleCrawler/papervalidation/retraction_watch_manager.py` | Pulls the latest Retraction Watch CSV, caches hashes, and flags retracted DOIs/IDs.
| `ResumeState` / checkpoints | `ArticleCrawler/checkpoint` | Serialize frames + sampler flags to disk so backend jobs can pause/resume.

## Data Frames & Store Layout

`FrameManager` initializes empty pandas DataFrames so downstream modules can rely on consistent schemas. The most used tables:

| Frame | Key Columns | Purpose |
| ----- | ----------- | ------- |
| `df_paper_metadata` | `paperId`, `doi`, `title`, `venue`, `year`, `isSeed`, `processed`, `selected`, `retracted` | Master list of everything the crawl touched. Updated after every iteration (`crawler.py::_run_iteration`).
| `df_paper_author` | `paperId`, `authorId` | Edge list for author relations.
| `df_author` | `authorId`, `authorName`, `isKeyAuthor` | Metadata for unique authors.
| `df_paper_citations` / `df_paper_references` | `paperId`, `citedPaperId` / `referencePaperId` | Citation network edges before dedupes.
| `df_abstract` | `paperId`, `abstract` | Raw abstract text assembled from OpenAlex inverted indexes.
| `df_derived_features` | `nodeId`, `attribute`, `centrality (in/out)` | Calculated by `GraphProcessing` for ranking.
| `df_forbidden_entries` | `paperId`, `reason`, `sampler`, `textProcessing`, `retracted` flag | Aggregates manual bans, retractions, or text-processing exclusions.

All frames live within `DataCoordinator.frames` and are persisted as parquet/pickle files through `DataStorage` according to the folders defined in `StorageAndLoggingConfig`.

## Iterative Crawl Flow

1. **Initialize configs** – `Crawler` maps legacy options (`SamplingOptions`, `GraphOptions`, etc.) into new config dataclasses (see `_resolve_configurations` in `crawler.py`).
2. **Seed frames** – `crawl_initial_condition` validates keywords/seeds and primes `DataCoordinator` with `FrameManager` instances.
3. **Retrieve data** – `PaperRetrievalService` pulls from OpenAlex and populates metadata/citation tables via `MetadataParser`.
4. **Graph sync** – `GraphManager.update_graph_with_new_nodes` creates/updates nodes for papers, venues, and authors; `GraphProcessing` recalculates eigenvector centrality, which then feeds sampling weights.
5. **Sampling** – `Sampler.select_papers` weighs keywords, venues, year proximity, manual overrides, and forbidden lists. Manual frontier arrays can be injected when resuming a job (see `_manual_frontier_ids`).
6. **Text processing** – `TextAnalysisManager` pipelines `text_pre_processing` (tokenization, stopword removal, stemming), `text_transformation` (vectorization), and `text_topic_modeling` (NMF/LDA). Figures are saved under `vault/figures/<timestamp>/` and Markdown under `vault/topics/` + `summary/`.
7. **Vault generation** – The `md_generator` (defaults provided by backend) consumes frames and figures to write `*_seed_*.md`, `*_table_*.md`, `top_authors.md`, etc. `DataStorage` keeps zipped dumps ready for frontend download.
8. **Progress + checkpoints** – `_emit_progress` produces `CrawlerProgressSnapshot` objects consumed by backend job stores. `ResumeState` serializes frames/flags and is restored inside `_initialize_resume_state` when resuming via the API.
9. **Stopping criteria** – `StoppingConfig.max_iter` and `max_df_size` bound the run; hitting either triggers `Crawler._finalize` to close logs and push final summaries.

## How the Backend Uses the Crawler

- `article-crawler-backend/app/services/crawler_execution_service.py` calls `CrawlerConfigBuilder.build` to produce `CrawlerRunInputs` that include all configs, seed data, and output folders under the backend-controlled experiment directory.
- The backend passes a `progress_callback` into `CrawlerJobRunner.run` so API endpoints can stream iteration counts (`/api/v1/crawler_execution/...`).


## Testing Strategy

- `tests/unit` and `tests/integration` cover samplers, frame managers, metadata parsing, graph sync, and resume handling. Run them with `python -m pytest` from `fakenewscitationnetwork/`.
- Sample frames live inside fixtures in `tests/unit/conftest.py`, mirroring the schemas documented above.


## Module Reference


### API, Config, and CLI
- `api/` – Provider factory plus individual provider classes (OpenAlex default, Semantic Scholar legacy) that encapsulate authentication, retries, batching, and pagination logic.
- `config/` – All typed configuration dataclasses (`CrawlerParameters`, `SamplingConfig`, `TextProcessingConfig`, `GraphConfig`, `StorageAndLoggingConfig`, `RetractionConfig`, `StoppingConfig`). They convert CLI/front-end JSON into strongly typed objects consumed by `Crawler`.
- `cli/` – Full Typer/Rich command suite (`commands/`, `input_collectors/`, `validators/`, `formatters/`, `ui/`, `zotero/`). Lets operators launch crawls, inspect jobs, or sync Zotero libraries directly from a terminal.

### Data Management & Storage
- `data/data_coordinator.py` – `DataCoordinator` glues together the retrieval service, frame manager, and graph manager so iterations can update pandas frames and graphs consistently.
- `data/frame_manager.py` & `data/data_frame_store.py` – Initialize every DataFrame with the required schema and expose them as typed properties for downstream modules/tests.
- `data/metadata_parser.py` – Converts API payloads into normalized rows, reconstructs abstracts from OpenAlex inverted indexes, and populates `FrameManager`.
- `data/retrieval_service.py` – `PaperRetrievalService` batches OpenAlex requests, applies throttling, and delegates parsing to `MetadataParser`.
- `data/paper_validator.py` & `data/validation_service.py` – Validate incoming rows (duplicate detection, missing fields, DOI sanity) before they influence sampling or text processing.
- `DataManagement/data_storage.py` – `DataStorage` controls parquet/pickle checkpointing, and experiment folder layout (mirrors `StorageAndLoggingConfig.folders_all`).
- `DataManagement/json_manager.py` & `markdown_writer.py` – Helpers for persisting JSON manifests and generating markdown tables when running standalone (backend supplies its own markdown generator).

### Graph, Sampling, and Feature Computation
- `graph/graph_manager.py` – Maintains the NetworkX `DiGraph`, exposes methods to add papers/authors/venues, and syncs node attributes back into pandas frames.
- `graph/graph_processing.py` – `GraphProcessing` calculates eigenvector/Katz centrality plus other derived metrics used by `Sampler` and text analysis.
- `sampling/sampler.py` – Implements the weighted sampler (keyword scores, year proximity, centrality, manual frontier). Respects entries in `df_forbidden_entries`.
- `DataProcessing/data_frame_filter.py` & `feature_computer.py` – Filtering utilities and feature computation (e.g., venue dominance, author influence) that augment `df_derived_features`.

### Text Processing & Topic Modeling
- `text_processing/preprocessing.py` – `TextPreProcessing` handles language detection, tokenization, stemming, and forbidden-paper filtering.
- `text_processing/vectorization.py` – `TextTransformation` builds TF-IDF and count vectorizers, storing both representations for downstream strategies.
- `text_processing/topic_modeling.py` – `TopicModeling` runs LDA/NMF and injects topic assignments back into the abstract DataFrame.
- `text_processing/refined_method_b_strategy.py`, `topic_strategies.py`, `topic_labeler.py`, `topic_labeling_strategy.py` – Strategy classes that encapsulate alternative modeling approaches and how topics are labeled/explained.
- `text_processing/topic_companion_writer.py` – Writes job-specific topic markdown/JSON (the frontend reads these from `vault/topics/`).
- `text_processing/text_analyzer.py` – `TextAnalysisManager` orchestrates the full pipeline (preprocess → vectorize → topic modeling → visualization/reporting) and interacts with `GraphProcessing` for centrality-aware summaries.
- `text_processing/visualization.py` & `visualization/topic_evolution_visualizer.py` – Render PNG charts (temporal evolution, word clouds) stored under `vault/figures/<timestamp>/`.

### Retraction, Validation, and Normalization
- `papervalidation/retraction_watch_manager.py` – Pulls the latest Retraction Watch CSV, hashes versions, and flags DOIs/paper IDs so `df_forbidden_entries` excludes them from sampling/text processing.
- `normalization/venue_*` modules – `VenueNormalizer`, alias tables, and fuzzy-matching helpers that unify venue names across OpenAlex records.
- `metadata_extraction/` – Dispatcher, factory, extractor classes, and models that parse metadata from PDFs/Zotero exports before the crawler ingests them.
- `pdf_processing/` – `grobid_client` (HTTP wrapper), `docker_manager` (controls the GROBID container), `metadata_extractor`, `pdf_processor`, and `api_matcher` to connect extracted references back to OpenAlex IDs.

### Libraries, Use Cases, and Utilities
- `library/` – `LibraryManager`, `AuthorSearchService`, `TopicOverviewWriter`, etc., powering the frontend’s “Create/Edit library” features and standalone analyses.
- `usecases/` – Purpose-built scripts (`author_investigation`, `paper_investigation`, `library_creation/editing`, `title_similarity_usecase`, `topic_modeling_usecase`, `recommender`, `author_topic_evolution_usecase`) that leverage the crawler core for specialized workflows.
- `utils/` – `PaperURLBuilder`, `LibraryTempManager`, `TimePeriodCalculator`, and other helpers shared across modules.
- `LogManager/crawler_logger.py` – Configures log formatting/rotation for every crawler run using paths from `StorageAndLoggingConfig`.
- `visualization/visualization_config.py` – Centralizes plotting parameters for topic evolution charts outside the main text analysis pipeline.

### Checkpointing & Resume
- `checkpoint/` – Models and helpers (`ResumeState`, `CheckpointManager`) that serialize DataFrame snapshots, sampler flags, and file paths so backend jobs can pause/resume safely.

