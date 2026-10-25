# Study: does a citation crawler beat agentic search? (October 2026)

> **Authorship notice.** This study was carried out by **Claude (Opus 5.5), an AI agent from Anthropic**, working in Claude Code sessions on 25 October 2026. Claude is **not part of this repository** and is not one of its authors. It used ArticleCrawler as a tool. The report labels every figure as *Repo output*, *Agentic Analysis of Crawler data*, *Claude web search* or *ChatGPT deep research*.

Open [`index.html`](index.html) in a browser for the full report.

## Question

How well does ArticleCrawler gather a field's literature compared with agentic search, such as ChatGPT deep research or Claude's own web search? Put simply: if you add all this machinery, is it any better than asking Claude to search?

The test field is neural cellular automata (NCA): which fields, labs and companies use them. This was input for a Fontys ICT Interaction Design lectorate talk.

## Answer in brief

- **Coverage: the crawler wins.** The test used a checklist of 14 NCA application domains. Claude's 3-minute web search and ChatGPT deep research each covered 5 fully and 2 partly. Each crawl's data covered 10–11 fully and 2–3 partly. ChatGPT also made at least 4 factual errors, which the crawl data exposed.
- **Seeding the crawler from search works best.** One crawl started from the 4 brief seeds plus the 14 papers Claude's search had named. It reached 96 of the 210 NCA-titled OpenAlex works, against 87 and 92 for the crawls from the brief seeds alone, and it did so with half as many papers as the big crawl.
- **Recency: search wins.** 59% of NCA-titled works (72% of those from 2026) have no reference list in OpenAlex. A citation crawl reaches those only as seeds. Only search found the 2026 language-model paper.
- **Bigger is not better.** Doubling the crawl added 3,169 papers but only 5 NCA papers. Keywords can pull in fields that share a name, such as classic CA in metallurgy or neural-network CA for land-use simulation.

## The three crawls

| | Small | Big | Search-seeded |
|---|---|---|---|
| Seeds | 4 brief seeds (`scripts/seeds.txt`) | same | 18: brief seeds + 14 from Claude's web search (`scripts/seeds_agentic.txt`) |
| Keywords | cellular automata, morphogenesis, self-organizing, regeneration, reaction-diffusion | same | neural cellular automata/automaton, NCA |
| Rounds | 3 × 25 | 6 × 50 | 6 × 50 |
| Code | `5a44791` plus the change committed as `85d5779` (crawl code identical to `85d5779`) | same | `85d5779` |
| Time, share of free daily OpenAlex allowance | ~5 min, ~4% | ~18 min, ~9% | ~17 min, ≤ 9% |
| Papers | 2,997 | 5,688 | 2,760 |

All three crawls ran against the live OpenAlex API through the Python API, using a free API key, so nothing was paid. The whole study used 27% of the key's free daily allowance (10,000 credits). Retraction Watch flagged no retracted papers in the small crawl and one off-topic paper in each of the other two; OpenAlex also marks both as retracted. Institution names and abstracts for the crawlers' papers were looked up in OpenAlex.

## Reproducing

`scripts/` is a snapshot of what was run. The scripts use paths relative to their own folder, plus an absolute path to `fakenewscitationnetwork/.env` for `OPENALEX_API_KEY`; adjust that path for your machine. Run them in this order:

1. Crawls: `run_nca.py`, `run_nca_big.py`, `run_nca_agentic.py`.
2. Citers and checks: `analyze.py <pkl>`, `inst.py`, `verify_gpt.py`, `coverage.py`, `more.py`, `build_data.py`.
3. Topic model: `fetch_corpus.py`, `K=12 nlp.py` (needs `sentence-transformers` and `umap-learn`), `build_nlp.py`.
4. Crawl comparison: `bigdiff.py`, `agdiff.py`, `compare.py`, `build_compare.py`.
5. Report: `assemble.py <out.html>`. It joins `part_css.html`, `part_body.html` and `part_js.js`. It also needs `native_imgs.json`, which holds the small crawl's `top_words_NMF_fig_1.png` from `vault/figures/` as a data URI.

`zotero_export.py` puts the evidence papers in a Zotero collection with the repository's `ZoteroExportService`.

OpenAlex changes daily, so counts will drift. `data/` holds the exact numbers behind the figures. `first-pass-summary.md` is the agent's first short summary, written after the small crawl and before the comparison.
