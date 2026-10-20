# ArticleCrawler — build a reproducible corpus of a research field

**Turn a handful of seed papers into a curated, local dataset of a whole research area — with topic models, author/venue rankings, retraction checks and a markdown vault you can hand to Obsidian, NotebookLM or an LLM.**

Built on [OpenAlex](https://openalex.org). Full stack: Python crawler core + FastAPI backend + React UI.

## Why use it

Tools like ResearchRabbit, Connected Papers, Litmaps and Inciteful are excellent for *looking at* the literature around a paper, and bibliometrix / VOSviewer are excellent for analysing a dataset you already have. ArticleCrawler sits between them: it **builds the dataset**, under your control.

- **A corpus you own, not a map you view.** Starting from seeds (DOIs, a Zotero library, PDFs, keywords), it expands the citation network over several iterations, scoring papers by keywords, centrality and sampling rules, and lets you steer each next step. The result is a folder of files, not a tab in someone else's app.
- **Reproducible by design.** Every run writes its parameters, errors and environment to a manifest, and previous crawls can be re-run with new settings — useful when the crawl is part of a study.
- **Understands the field, not just the papers.** Topic models (LDA / NMF) over time, top authors and venues, and per-author topic evolution.
- **Integrity-aware.** Papers can be checked against Retraction Watch data.
- **Ready for LLM-assisted review.** The vault is plain markdown (one note per paper plus summaries), designed to import cleanly into Obsidian or NotebookLM.
- **Local and open.** Runs on your machine or in Docker; your Zotero library and PDFs (parsed with GROBID) never need to leave it.

**Good fit:** scoping a field you are new to, bibliometric / scientometric studies, preparing a corpus for a systematic or LLM-assisted review, tracking how a topic or an author's focus evolves. **Not a fit:** quick "what's related to this one paper?" lookups — use the tools above.

**Worked example:** a crawl of roughly 7,000 fertilizer-prediction papers answered a researcher's questions about venues, experts, openness, subfields and trustworthiness (see [Media & Supporting Assets](#media--supporting-assets)).

## How it works

1. **Seed** – import DOIs / OpenAlex IDs, a Zotero export, PDFs or a local folder; review and clean them in the staging screens.
2. **Crawl** – iteratively expand references and citations, score and filter, optionally add papers by hand for the next frontier.
3. **Analyse** – topic models, rankings, author and venue views, retraction flags.
4. **Export** – a vault of ranked tables, per-paper notes and figures; Zotero export; reruns with different parameters.

## Project status (October 2026)

| Area | State |
|---|---|
| Crawler core, backend API | Unit-tested: crawler 630 passed / 5 skipped, backend 57 passed (Python 3.12; 3.11 is the documented target) |
| Data source | **OpenAlex only.** Semantic Scholar (the original source) is retired — see the [decision record](docs/decisions/semantic-scholar-to-openalex.md) |
| OpenAlex access | **Needs a free API key** (`OPENALEX_API_KEY`, from <https://openalex.org/settings/api>). OpenAlex now meters usage by key; email-only access is very limited. Support was added recently and is **not yet verified against the live API** |
| Frontend, Docker build, GROBID/PDF ingestion, Playwright e2e | Present, but **not re-verified end to end** recently — run the smoke test in the decision record before relying on them |
| Recommender / title similarity | Experimental and unfinished; optional install (`--with-ml`), not used by the API or UI |
| Backend Settings screen | Edits the OpenAlex email and Zotero settings only; set the API key in `.env` |

If you are picking this project up, read the [decision record](docs/decisions/semantic-scholar-to-openalex.md) first: it explains the history, what changed, and the open decisions.

## Quick start

```bash
python install.py            # creates .venv, installs dependencies, writes .env files
# add your key to .env:  OPENALEX_API_KEY=...
python run_tests.py          # optional sanity check
```

Docker: `cp .env.docker.example .env`, fill in `OPENALEX_EMAIL` / `OPENALEX_API_KEY`, then `docker compose up --build`. The heavy ML packages (torch, sentence-transformers) are **not** installed by default; add `--with-ml` (or `INSTALL_ML=true` for Docker) only if you want the experimental recommender. Full details: [Installation guide](Installation%20guide.md).

## Where the name comes from

The project started as a tool for mapping research on misinformation and fake news spread (hence the `fakenewscitationnetwork/` directory) and has since become a general-purpose crawler for any research field.

## Repository Structure

- `fakenewscitationnetwork/` – Python crawler package, CLI scripts, experiment data, and vault outputs.
- `article-crawler-backend/` – FastAPI service that exposes crawler functionality and manages retraction cache data.
- `frontend/` – Vite + React UI for operating the crawler and browsing vaults.
- `docker/`, `docker-compose.yml` – Container workflow (includes optional GROBID PDF parsing).
- `install.py` – Automated installer that provisions `.venv`, dependencies, and `.env` files.
- `docs/` – New documentation hub described below.

## Documentation Map

- [Installation guide](Installation%20guide.md) – Full stack install/runbook.
- [`docs/README.md`](docs/README.md) – Start here for the complete documentation hub; it links to every guide described below.
  - [`docs/decisions/semantic-scholar-to-openalex.md`](docs/decisions/semantic-scholar-to-openalex.md) – Why the project moved from Semantic Scholar to OpenAlex, what changed since, and what is still open.
  - [`docs/system-overview.md`](docs/system-overview.md) – Combined architecture + workflow description.
  - [`docs/components/crawler.md`](docs/components/crawler.md) – Details about `fakenewscitationnetwork/`.
  - [`docs/components/backend.md`](docs/components/backend.md) – FastAPI backend notes.
  - [`docs/components/frontend.md`](docs/components/frontend.md) – Frontend notes, asset guidance.
  - [`docs/handover/structure-map.md`](docs/handover/structure-map.md) – Config + code ownership guide.
  - [`docs/handover/mega-prompts.md`](docs/handover/mega-prompts.md) – Debugging prompts (general + per component).


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
