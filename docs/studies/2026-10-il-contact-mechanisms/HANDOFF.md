# Session handoff: IL contact-mechanisms study

From a Claude Code session (Claude Opus 5.5) with Iman Mossavat, 29 October 2026, ending about 09:30 UTC.
The study is complete, committed and pushed (`db8da77` on `main`). Read this file, then `README.md`.

## What the study is

It is the second field test of ArticleCrawler, after the NCA study in `../2026-10-nca-adopters/`.

**Test question:** "For imitation-learned robot policies on contact-rich manipulation, which failure
mechanisms have been shown by intervention, not just correlation? Effect sizes, sim/real, replication?"

**Real question:** how well do two ArticleCrawler crawls, ChatGPT deep research (two prompts), NotebookLM
and a short Claude web search gather the evidence, and how accurate is what they report?

**Purpose:** a publication with accurate claims about the crawler.

## Deliverables (all in this folder unless noted)

| File | What |
|---|---|
| `index.html` | The report. Published privately as https://claude.ai/artifact/Pv1stVDZ1xTeFWQaCTcuUa (version 2). The user shares it via the Share menu |
| `survey.md` | Plain-language survey of the question: methodology with trial-count maths, mechanisms with verified numbers, grasp vs insertion, open experiments, and a chapter comparing the search methods |
| `external-outputs.md` | The ChatGPT (both prompts) and NotebookLM outputs, readable and translated, with a verdict on every claim. Cited from `index.html` and `survey.md` |
| `preregistration.md` | Rules, checklist M1–M12 and hypotheses, fixed before any results, plus amendments 1–3 (hashed) |
| `search_log.md` | Claude's six web searches |
| `data/verification.md` | Ledger: every claim checked against full text |
| `data/raw/` | External outputs exactly as received |
| `data/*.json` | Seeds, evidence set (36 papers), crawl coverage, citers |
| `data/agentic/`, `scripts/agentic/` | NCA-style analyses: seed citers, field-set coverage, SPECTER topic model, citation network, crawl diff |
| `../agentic-analyses.md` | Reference description of all analyses run on top of a crawl (both studies) |
| `README.md` | Overview and how to reproduce |

## Results to keep consistent everywhere

**Accuracy of the search outputs** (checked against the paper text):
- ChatGPT, structured prompt: 3 errors in 9 rows; 3 of the 9 rows are outside the contact-rich scope.
- ChatGPT, short prompt: 3 errors in 5 rows (2 citations not found, 1 wrong robot); answered in Dutch.
- NotebookLM: 4 errors and 5 partly-wrong claims. It inverts *Much Ado About Noising*.
- Claude search: 0 errors in 5 checked claims.

**Overlap:** the four search outputs cite almost disjoint papers. Only RDP and *Much Ado* appear in more
than one.

**Evidence set (36 papers):**
- 17 have no links in OpenAlex, 16 of them from 2025–26.
- The crawls hold 16 (A) and 21 (B).
- Among linked non-seeds, the crawls reached 11/15 (A) and 7/10 (B).
- Crawl B holds 16 of the 19 linked evidence papers.

**Field set (217 contact-rich IL works since 2023):**
- 95 (44%) are dark; in 2026, 66 of 103.
- The crawls reached 83 (A) and 87 (B) of the 122 linked works.

**Citation network:** 246 nodes, 139 edges; 65% of nodes isolated.

**Topic model:** k=11 (silhouette 0.363; best was k=6 at 0.389). Most mechanism evidence sits in a general
"IL theory, data and interventions" cluster that holds only 4 field-set works.

**Replication evidence:** the crawl holds nearly every indexed citer of the evidence papers. FoAR (found
only by the crawl) is the cross-group result on naive force fusion.

**Hypotheses:** H1 partly; H2, H3 and H4 supported; H5 partly.

**Cost:** crawls of 17 and 19 minutes, 0 errors. The whole study used 25% of the free daily OpenAlex
allowance.

**Corrections already made** (do not reintroduce):
- MiTaS vision-only is 35.5%.
- FACTR is a real-robot study.
- RDP and FoAR are the same group (Cewu Lu).
- Crawl B holds 16 of 19 linked evidence papers.

## Open items for the user

1. Run times of both ChatGPT runs and of NotebookLM, and the NotebookLM prompt. Not recorded; the report
   says so. Add them to `external-outputs.md` and the report's setup table.
2. Whether ChatGPT memory was off in the short-prompt run.
3. **Branch `fix/crawl-state-flags` is not pushed.** The crawls ran on its commit `5c90d09`, which the study
   cites. Until that branch is pushed or merged, readers of `main` can't see that commit. Ask before pushing.
4. Sharing the artifact (private by default).

## How to continue

- **Re-run or extend:** see `README.md`, "Reproducing". Embeddings run in the `REFLECT` conda env and
  UMAP/k-means in `TTS`. Do not install packages into the user's environments. Crawl pickles live in
  `scripts/out/` (git-ignored, local only). `data/agentic/embeddings.npy` is git-ignored; `embed.py`
  rebuilds it.
- **Change the report:** edit `scripts/agentic/part_sections.html` / `part_js.js`, run
  `python3 scripts/agentic/assemble.py` (idempotent), and republish to the same URL. From a new session,
  pass `url` to the Artifact tool and read it first.
- **Verification rule** (user's correction, also in memory): check cited papers on the web or arXiv, not only
  in OpenAlex. Every number comes from the paper's full text. Full texts were read from
  `https://arxiv.org/html/<id>`; the session scratchpad copies are gone, so re-download if needed.
- **Keywords** are substring matches on titles: pair ambiguous words with a robotics term.

## Natural next steps

- Run one of the open experiments listed in `survey.md` §2.10, for example history × policy class × action
  space on one insertion task, or force-fusion choices across ACT, DP and a flow policy.
- Build the crawler features listed at the end of `../agentic-analyses.md`. The highest value is a fallback
  reference source for papers with no links in OpenAlex, then merging preprint and venue versions.
