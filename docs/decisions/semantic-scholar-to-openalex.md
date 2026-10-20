# Why the project moved from Semantic Scholar to OpenAlex — and what changed next

**Status:** accepted · **Scope:** crawler core, backend API, installer, Docker image
**Decision owner:** Iman Mossavat

This note records *why* the codebase looks the way it does, so that anyone picking it up later
(including future-me) doesn't have to reverse-engineer it. It covers three phases:

| Phase | What happened | Data source |
|---|---|---|
| 1. Research tool | Iman Mossavat wrote a package to analyse the literature on misinformation / fake-news spread | Semantic Scholar |
| 2. OpenAlex pivot | Semantic Scholar became unusable for the project; an intern helped rebuild around OpenAlex and added an API + UI | OpenAlex (email-based access at the time) |
| 3. Cleanup (this change) | Finish the pivot: retire the leftovers of phase 1 and stop forcing heavy dependencies on everyone | OpenAlex only |

> Items marked **Author to confirm** are things the repository cannot tell us (dates, outcomes of
> the original analysis). Fill them in or delete them.

---

## Phase 1 — A research tool for studying misinformation papers (Semantic Scholar)

The package was written by Iman Mossavat to look into **papers that study misinformation spread**.
That is where the odd directory name `fakenewscitationnetwork/` comes from: it was originally a
*citation network of fake-news research*.

The working idea, which still defines the crawler core today:

1. start from a set of **seed papers**,
2. **expand the citation network** (references and citations) through an academic-graph API,
3. **sample / score** papers (keywords, centrality, sampling rules) so the crawl stays on-topic,
4. **topic-model** the resulting corpus to map the field.

In this phase the data source was **Semantic Scholar**, accessed through the PyS2 library
(`https://github.com/mirandrom/PyS2`).

> **Author to confirm:** time frame of this work, and the headline results of the fake-news
> literature analysis, if worth recording here.

Traces of this era are still visible in the code. The Semantic Scholar provider defaults to
`wait=150` seconds between `retries=2`, and tracks `failed_paper_ids` and
`inconsistent_api_response_paper_ids` (responses whose returned ID differed from the one
requested). Those defaults and bookkeeping are what you would add to a client that is fighting
rate limits and unreliable responses.

The **provider abstraction** (`BaseAPIProvider` + `create_api_provider`) was the important design
choice of this phase: the crawler talks to an interface, not to a specific service. That is what
made phase 2 feasible without rewriting the crawler.

## Phase 2 — Moving to OpenAlex

### Why

Semantic Scholar stopped being workable for this project:

- the API became **rate limited**, which makes large citation crawls impractically slow, and
- requests for an **account / API key** (the usual way to get higher limits) **went unanswered**.

With no realistic path to the throughput a citation crawl needs, the project switched to
**OpenAlex**, an open scholarly graph (CC0 data). At that time (September 2025) OpenAlex let you
identify yourself with a contact email to get its faster "polite pool" — that is what the
project's `OPENALEX_EMAIL` setting does — so no approved account was needed.

> **That access model has since changed.** See
> [OpenAlex changed its access model after the pivot](#openalex-changed-its-access-model-after-the-pivot).

### How

An intern was hired to carry this forward. The repository history starts here (the first commit is
*"Openalex initial exploration files"*, 2025‑09‑24); the Semantic Scholar–era history lives
outside this repository.

Thanks to the provider abstraction, the crawler core kept its shape while the intern:

- implemented the **OpenAlex provider** (with citation/reference enrichment),
- built the **FastAPI backend** (`article-crawler-backend/`) and the **React frontend**
  (`frontend/`),
- added library creation from **Zotero**, **PDFs** (via GROBID) and local folders, library
  editing, crawl reruns, and author topic-evolution views.

This is the part of the codebase Iman knows least well. Start with
[`docs/components/backend.md`](../components/backend.md),
[`docs/components/frontend.md`](../components/frontend.md) and
[`docs/handover/structure-map.md`](../handover/structure-map.md).

### What it left behind

The pivot was done by *adding* OpenAlex, not by *removing* Semantic Scholar. Semantic Scholar stayed
wired in as a selectable "legacy" provider, and an unfinished experiment of Iman's
(the recommender, below) stayed exported from the package. Nobody revisited either, and by this
point the app was OpenAlex-only in practice:

- the **frontend hardcodes `api_provider: 'openalex'`** in all 7 places it sets a provider, and
  never mentions Semantic Scholar;
- the **backend defaults to `openalex`** everywhere.

But the leftovers were not harmless — see phase 3.

## OpenAlex changed its access model after the pivot

This is the most important thing to know before relying on the system.

**What changed (per OpenAlex's own documentation, checked October 2026):**

- Before February 2026 OpenAlex offered the email-based *polite pool*. That system has been
  **replaced by API keys**: every user is expected to have one, and keys are free.
- Usage is now metered against a **daily budget in dollars**, which refills at midnight UTC. A free
  key gives about **$1/day**; using the API with no key gives only a small fraction of that (the
  docs state it as roughly 10× less, and different pages quote $0.10 and $0.01 per day — check the
  current figure). Exceeding the budget, or exceeding 100 requests/second, returns HTTP 429.
- Different request types cost different amounts, larger pages (`per_page=100`) stretch the budget
  further, higher limits are available on paid plans (and academics can ask for more), and the
  full **data snapshot** is free to download for bulk work.

Sources: <https://developers.openalex.org/api-reference/authentication> and
<https://developers.openalex.org/guides/deprecations>.

**Update:** `OPENALEX_API_KEY` support has since been added (crawler, CLI, installer, `.env` templates). The text below describes the state *before* that change. Still open: the backend's Settings screen only edits the email, so set the key in `.env`.

**What the project did before:** it authenticated *only* with an email — `OPENALEX_EMAIL` is
required, set as `pyalex.config.email` and sent as `mailto=` on the provider's direct HTTP calls.
There is **no API-key support anywhere** (the only `api_key` settings in the repo are for Zotero).
The installed `pyalex` (0.18) can send a key (`pyalex.config.api_key`), so adding support is
small, but it has not been done.

**Why it matters:** the project left Semantic Scholar because of rate limiting and unreachable
account approval. Running keyless against OpenAlex's new budget risks the *same* failure — a real
citation crawl making thousands of calls could hit HTTP 429 quickly, and the provider's built-in
2 requests/second limiter does nothing about a daily cost budget. I have **not** been able to test
this live, so treat it as a strong risk to check, not a confirmed bug.

**Recommended next step** (not part of this change): create a free key at
<https://openalex.org/settings/api>, add an `OPENALEX_API_KEY` setting, send it in both the
`pyalex` configuration and the provider's direct `requests` calls, make the email optional, and
surface the remaining budget (the `/rate-limit` endpoint) in the UI or logs. For very large crawls,
consider the free snapshot instead of the API.

## Phase 3 — Finishing the pivot (this change)

A first real test run of the never-tested repo surfaced the following. Each row is a decision.

| # | Finding | Decision | Why |
|---|---|---|---|
| 1 | `requirements.txt` pinned `s2==0.1.9`. That is **not PyS2**: the PyPI package named `s2` is an unrelated project with no `s2.api`. | **Remove `s2` from requirements.** Keep PyS2 as a documented, manual install for anyone who needs the legacy provider. | A fresh install silently got the wrong library. |
| 2 | With the wrong package, Semantic Scholar calls didn't crash — the provider's `except Exception` blocks logged and returned `None`, so **every lookup looked like "paper not found"**. | The provider now **raises a clear `ImportError`** (before the `try`) explaining how to install PyS2. Selecting it through the factory emits a `DeprecationWarning`. | Silent failure is worse than a loud one. |
| 3 | The backend API still accepted `api_provider="semantic_scholar"` (seeds, Zotero matching, PDF matching, staging) although no client ever sent it. | Request schemas are now `Literal["openalex"]`; the unused `_from_semantic_scholar` seed builder is deleted. The API rejects other values with a validation error (HTTP 422). | The API shouldn't advertise a provider that can't work. |
| 4 | `import ArticleCrawler` imported **`torch` and `sentence-transformers`** (multi-GB). Only the recommender and title-similarity modules use them, and **nothing** — backend, frontend, CLI — calls those modules. They have no tests. | **Make the ML stack optional**: new `ml` extra / `requirements-ml.txt`, imports are lazy, package exports resolve on first use. Installer flag `--with-ml`; Docker build arg `INSTALL_ML=true`. | During testing, a plain `pip install` pulled CUDA builds of torch and exhausted a sandbox's free disk. Everyone paid that cost for code nobody runs. |
| 5 | The CLI imported **`tkinter`** (a desktop GUI toolkit) at module level, and the backend imports the CLI package. A headless server without `python3-tk` **could not start the API**. | `tkinter` is imported inside the one method that opens the native file dialog. | Docker only worked because its image installs `python3-tk`. |
| 6 | `polars` was pinned to `1.35.2` in the crawler's `requirements.txt` and `0.20.21` in the backend's. The crawler never uses polars. | Removed from the crawler's requirements; the backend's pin is the only one. | Both install flows install the backend last, so `0.20.21` is what actually runs. The backend tests pass on both versions. |
| 7 | 4 metadata-extractor smoke tests read sample files (`testfilesDifferentfiletypes/`) that were never committed. | Tests now **generate their own samples** and assert real values (title, DOI, authors). | Self-contained tests; no binary fixtures to lose. |
| 8 | `ArticleCrawler/utils/` had no `__init__.py`. | Added an empty one. | A normal (non-editable) install would have omitted the package. |

### What this change deliberately does **not** do

- **It does not delete Semantic Scholar from the crawler core.** The term still appears in 19
  files (config, CLI wizard, validators, Zotero title-matching strategies, `markdown_writer`,
  `json_manager`, `url_builder`, …). Removing it is a refactor with its own risk; it is
  listed below as an open decision rather than bundled in.
- **It does not finish or delete the recommender.** It is only made optional (see below).
- **It does not exercise a real OpenAlex crawl.** The unit tests mock the network. See
  "Verification".

### About the recommender

`PaperRecommender` (in `usecases/recommender.py`) is Iman's later, unfinished experiment: a
**LinUCB contextual bandit over sentence embeddings** that learns from relevant / not-relevant
feedback and ranks the next papers to review. `TitleSimilarityEngine` is a related embedding-based
title search. They are the *only* reason the project needed `torch`.

They remain available — install the extra and use them as before:

```bash
pip install -e "fakenewscitationnetwork[ml]"     # or: pip install -r fakenewscitationnetwork/requirements-ml.txt
python install.py --with-ml                       # installer
docker compose build --build-arg INSTALL_ML=true  # Docker (or set INSTALL_ML=true in .env)
```

Known state of that code, so nobody is surprised later: no tests; not wired into the CLI, API or UI;
and `PaperRecommender.save()` references `self.fb` / `self.model`, which don't exist (they are
`self.feedback` / `self.embedding_model`), so saving a session would fail.

## Consequences

**Breaking changes**

- API clients sending `api_provider: "semantic_scholar"` now get a validation error. (The shipped
  frontend never did.)
- `from ArticleCrawler import *` no longer includes `TitleSimilarityEngine`, `PaperRecommender`,
  `RecommenderEmbeddingModel`. Accessing them by name (`ArticleCrawler.PaperRecommender`,
  `from ArticleCrawler import PaperRecommender`) still works and imports on demand.
- A default install no longer includes `torch`; using the recommender without `[ml]` raises an
  `ImportError` that says exactly what to install.
- `fakenewscitationnetwork/requirements.txt` no longer contains `s2`, `polars`, or the torch /
  transformers stack (the latter moved to `requirements-ml.txt`).

**Benefits**

- A default install is a small fraction of the previous size and works on machines without a GPU
  toolchain or desktop libraries.
- The backend starts on a headless host without `python3-tk`.
- The API's contract matches what the product actually supports.

## Verification

Run with Python 3.12, with **no stubbed modules** (no `torch`, no `tkinter` installed):

| Suite | Before | After |
|---|---|---|
| Crawler (`pytest`) | 613 passed, 9 failed (only runnable at all with `torch` / `tkinter` stubbed) | **626 passed, 5 skipped, 0 failed** |
| Backend (`pytest`) | 50 passed (with stubs; first run used `polars` 1.35, which users don't get) | **57 passed** (on `polars` 0.20.21, which both install flows use) |

The 5 skipped tests need the real PyS2 library and skip themselves if it isn't installed.
New regression tests keep `import ArticleCrawler` free of `torch` / `tkinter` and assert the API
rejects Semantic Scholar.

**Not verified:** a live crawl against OpenAlex (including whether it hits the new daily budget), the Playwright end-to-end tests, GROBID/PDF
ingestion, and the Docker build. These need network access and services the review environment
lacked. Before relying on the system, run the manual smoke test below.

### Manual smoke test (≈15 minutes)

0. Create a free OpenAlex API key (see above). Until key support is added, expect the budget to be tight.
1. `python install.py`, then `python run_tests.py`.
2. Start the backend and frontend (see the [Installation guide](../../Installation%20guide.md)).
3. Create a library from 3–5 known DOIs; confirm papers appear with titles and authors.
4. Run a small seed-based crawl (1–2 iterations); confirm the results page, topics and export work.
5. Optional: `cd frontend && npm run test:e2e`.

## Open decisions

1. **OpenAlex API key — done in the code, verify live.** Add `OPENALEX_API_KEY` to `.env`, run a real crawl, and watch for HTTP 429. Optionally add a key field to the backend Settings screen and surface the remaining budget.
2. **Strip Semantic Scholar from the crawler core?** Recommended once the OpenAlex smoke test
   passes: delete `semantic_scholar_api.py`, the factory branch, the Zotero
   `SemanticScholarTitleMatch` strategy and the config/CLI references. Keep it only if there is a
   realistic chance of regaining API access.
3. **Finish, park or delete the recommender?** If finished, add tests, fix `save()`, and wire it to
   the backend/UI; if parked, leave it behind the `ml` extra as now.
4. **Reconcile dependency pins.** `pyproject.toml` and `requirements.txt` disagree on a few
   packages (e.g. `python-docx` 1.1.2 vs 1.2.0, `beautifulsoup4` 4.12.3 vs 4.14.2, and the CLI
   extra's `pydantic` 2.12.3 vs the backend's 2.5.3). `requirements.txt` looks like a `pip freeze`
   dump and could be regenerated from the real direct dependencies.
5. **Supported Python version.** Docs and Docker say 3.11; the tests above ran on 3.12.
6. **Housekeeping.** The tests need `OPENALEX_EMAIL`, `ARTICLECRAWLER_PATH` and downloaded NLTK
   data, and fail with unhelpful messages when these are missing; an IDE folder
   (`.idea/`) is committed inside the package.
