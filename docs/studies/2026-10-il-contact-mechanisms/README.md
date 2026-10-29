# Study: crawler vs search on a mechanism question (October 2026)

> **Authorship notice.** This study was carried out by **Claude (Opus 5.5), an AI agent from Anthropic**, in a Claude Code session on 29 October 2026, for Iman Mossavat. Claude is not an author of this repository; it used ArticleCrawler as a tool.

- `index.html`: the report (crawler vs ChatGPT deep research ×2, NotebookLM, Claude web search).
- `survey.md`: a working survey of the question itself: methodology, mechanisms with verified numbers, and a chapter comparing the search methods.
- `preregistration.md`: rules, checklist and hypotheses fixed before any results, plus three dated amendments.
- `external-outputs.md`: what ChatGPT (two prompts) and NotebookLM returned, translated and readable, with a verdict on every claim.
- `data/agentic/`, `scripts/agentic/`: the NCA-style analyses (seed citers, field-set coverage, embedding topic model, citation network, crawl diff). Method: `../agentic-analyses.md`.

## Question

For imitation-learned robot policies on contact-rich manipulation, which failure mechanisms have been shown by intervention, not just correlation; how large are the effects; and have they been replicated?

## Answer in brief (about the tools)

- The four search outputs cite almost disjoint sets of papers; only two papers appear in more than one.
- Every search output had factual errors when checked against the paper text (`data/verification.md`), except Claude's short search on the claims checked.
- 17 of 36 evidence papers have no references and no citations in OpenAlex, so a citation crawl reaches them only as seeds.
- Among linked papers, the crawls reached 70–73% of the non-seeds and held nearly every indexed citer of the key evidence. That is how FoAR, which no search tool named, was found.
- Seeding the crawl from search worked best, again.

## Reproducing

Scripts are in `scripts/`. They read `OPENALEX_API_KEY` from `fakenewscitationnetwork/.env` (absolute path; adjust for your machine). Run with the repository's virtualenv from `fakenewscitationnetwork/` for anything that loads crawl pickles.

1. Seeds: `resolve_seeds.py`, then `find_versions.py` → `data/seeds.json`, `scripts/seeds_*.txt`.
2. Crawls: `run_crawl.py brief` and `run_crawl.py search` (output in `scripts/out/`, git-ignored).
3. Verification: `verify_ids.py` (existence), then reading of full texts (`data/verification.md`, `data/verify_web.md`).
4. Coverage: `resolve_evidence.py` → `data/evidence.json`; `coverage.py brief=<pkl> search=<pkl>`; `citers.py brief=<pkl> search=<pkl>`.

5. Agentic analyses (see `../agentic-analyses.md`): `agentic/fetch_all.py` (system python); `agentic/analyze_crawls.py <brief.pkl> <search.pkl>` (repo venv, from `fakenewscitationnetwork/`); `agentic/embed.py` (conda env `REFLECT`); `K=11 agentic/topics.py` (conda env `TTS`); `agentic/build_report_data.py` (repo venv); `agentic/assemble.py` splices the sections into `index.html`. `data/agentic/embeddings.npy` is git-ignored; `embed.py` rebuilds it.

OpenAlex changes daily, so counts will drift. The external outputs are stored as received in `data/raw/`.
