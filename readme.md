# OpenAlex Project Repository

Full-stack workspace for the ArticleCrawler system (crawler core + FastAPI backend + React frontend).

## Project Overview – What You Can Do

The ArticleCrawler stack helps researchers and analysts explore scientific domains end-to-end: launch citation crawls, ingest personal PDF libraries, explore authors/topics, and creates structured vaults for further analysis.

- **Library creation from many ingestion sources:** Import Zotero exports, local folders (PDF, HTML, DOCX, etc.), or remote libraries via simple staging screens to generate clean, normalized vaults you can reuse elsewhere.
- **Library editing:** Reopen any existing library to restage, filter, and clean it.
- **Crawling with vault creation:** Start a seed-based crawl, let the system iteratively expand the citation network and score papers by keywords, centrality, and sampling rules, then get vaults packed with ranked tables, topic-model summaries, author/venue highlights, and manual k+1 continuation screens that help you steer the next frontier.
- **Author topic exploration:** Run dedicated author workflows to fetch an author’s corpus, model topics over time, and visualize how their focus evolves.
- **Crawl reruns & experimentation:** Rerun previous crawls to test new parameters.

## Repository Structure

- `fakenewscitationnetwork/` – Python crawler package, CLI scripts, experiment data, and vault outputs.
- `article-crawler-backend/` – FastAPI service that exposes crawler functionality and manages retraction cache data.
- `frontend/` – Vite + React UI for operating the crawler and browsing vaults.
- `docker/`, `docker-compose.yml` – Container workflow (includes optional GROBID PDF parsing).
- `install.py` – Automated installer that provisions `.venv`, dependencies, and `.env` files.
- `docs/` – New documentation hub described below.

## Documentation Map

- [Installation guide](Installation guide.md) – Full stack install/runbook.
- [`docs/README.md`](docs/README.md) – Start here for the complete documentation hub; it links to every guide described below.
  - [`docs/system-overview.md`](docs/system-overview.md) – Combined architecture + workflow description.
  - [`docs/components/crawler.md`](docs/components/crawler.md) – Details about `fakenewscitationnetwork/`.
  - [`docs/components/backend.md`](docs/components/backend.md) – FastAPI backend notes.
  - [`docs/components/frontend.md`](docs/components/frontend.md) – Frontend notes, asset guidance.
  - [`docs/handover/structure-map.md`](docs/handover/structure-map.md) – Config + code ownership guide.
  - [`docs/handover/mega-prompts.md`](docs/handover/mega-prompts.md) – Debugging prompts (general + per component).


## Getting Started

Follow the [Installation guide](Installation guide.md) for step-by-step instructions on cloning the repo, running the installer, configuring `.env` files, and launching either the local or Docker-based workflow. It also covers optional components such as GROBID and Zotero integrations.

## Running Tests

Use the helper script in the repo root to execute all crawler and backend tests from one command:

```bash
python run_tests.py
```

## Media & Supporting Assets

- **Crawler interview decks:**
  - [`docs/assets/FertelizerPrediction Presentation part 1.pptx`](docs/assets/FertelizerPrediction%20Presentation%20part%201.pptx) – Findings/validation deck showing how the crawler answered the researcher’s questions about venues, experts, openness, subfields, and trustworthiness across ~7k fertilizer prediction papers.
  - [`docs/assets/FertelizerPrediction Presentation part 2.pptx`](docs/assets/FertelizerPrediction%20Presentation%20part%202.pptx) – Technical workflow deck explaining inputs, OpenAlex enrichment, crawling, filtering/ranking, structuring, and Obsidian export so stakeholders see how results are produced.
- **Researcher survey:** [`docs/assets/Survey Finalized.md`](docs/assets/Survey%20Finalized.md) – sanitized questionnaire used in interviews to capture researcher workflows and evaluation criteria.
- **Ideas-for-next vault:** `docs/assets/Vaultwithideasfornext/` – Obsidian-style vault containing worked-out feature ideas from the mentor (overview + per-idea markdown notes, including rationale and feasibility constraints).

See `docs/assets/README.md` for more details about each asset and guidance for adding new ones.
