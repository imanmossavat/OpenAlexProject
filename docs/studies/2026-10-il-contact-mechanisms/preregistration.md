# Pre-registration: causal failure mechanisms in imitation-learned contact-rich policies

Written 2026-10-29, **before** any search, crawl or ChatGPT output for this study was seen.
Author: Claude (Opus 5.5), working in a Claude Code session; not an author of ArticleCrawler.
Purpose: fix the scoring rules and the checklist in advance, so ChatGPT deep research, Claude's
short web search and the ArticleCrawler runs are all judged against the same list. (The NCA
study built its checklist after seeing the results; this fixes that weakness.)

## 1. Question

For imitation-learned robot policies on contact-rich manipulation, which failure mechanisms
have been shown by intervention, not just correlation? For each: what was changed, on which
task, sim or real, effect size and trials, and whether it was replicated on a different policy
or task. Narrow fallback: what has been causally shown to make insertion/assembly fail, as
opposed to grasping?

## 2. What counts as evidence

| Grade | Definition |
|---|---|
| **A** | One factor changed with the rest fixed (ablation, toggle, controlled comparison); success measured with and without it; trials per condition reported. |
| **B** | Intervention present but confounded (several factors changed together, or trials not reported). |
| **C** | Correlational only: failure analysis, attention maps, probing, or a "method beats baselines" result with no single-factor ablation. Not a table row; listed separately. |

- Intervention categories: **cost** (loss terms, objectives), **training** (curriculum, noise
  injection, DAgger-style correction), **architecture**, **input** (modalities, history,
  preprocessing, camera), **data** (quantity, diversity, recovery demos, quality), and
  **action/control** (action representation, chunking, compliance/impedance, inference
  scheme). The last one is added because I expect many contact-rich mechanisms to live there.
- **Negative or null results count** as grade-A evidence against a mechanism.
- Ablation tables in method papers are primary sources.
- Excluded: leaderboards and benchmark papers with no intervention; pure RL, unless it is
  compared with an imitation policy under the same intervention.
- Window: 2023–2026, with weight on 2025–2026. Older anchors (e.g. robomimic 2021) may be
  cited as the original source of a mechanism, but they do not count as recent evidence.

## 3. Replication rules

- **Replicated:** the same mechanism is shown with grade A or B by a *different group* on a
  *different policy class or task*.
- **Weakly replicated:** the same group, or the same policy on a new task.
- **Contested:** a grade-A result points the other way (for example, a myth-busting paper).
- **Single:** one source only.
- A row also records sim vs real and trials per condition; a real-robot result with fewer
  than 20 trials per condition is flagged "low-n".

## 4. Grasp vs insertion

Each row records the phase where the failure occurs: **approach/grasp**, **insertion/assembly**,
**both**, or **not separated**. A paper "separates" the phases only if it reports success or
failure per phase, or intervenes on one phase alone.

## 5. Candidate checklist (fixed now)

These are the mechanism families I expect, written from prior knowledge. "Believed source"
means I expect it there; every entry still has to be verified. A source gets credit for a
family when it reports at least one verified grade-A/B row in it. A source can also earn
credit for families that are **not** on this list; those are counted separately as "found
beyond the checklist", so the list does not cap recall.

| # | Mechanism family | Believed sources to verify |
|---|---|---|
| M1 | Modality neglect: the policy ignores force or touch when vision suffices for most of the task | FACTR (force-attending curriculum, 2025); Reactive Diffusion Policy (tactile/force, 2025); modality-dropout ablations |
| M2 | Observation history: copycat or causal confusion, or history helping | robomimic (2021 anchor); Past-Token Prediction for long-context diffusion policies (2025) |
| M3 | Action chunking vs reactivity (chunk length, temporal ensembling, closed-loop decoding) | ACT (2023); Bidirectional Decoding (2024); Diffusion Policy ablations |
| M4 | Compounding error and covariate shift; noise injection; the true role of stochasticity in generative policies | "The Pitfalls of Imitation Learning when Actions are Continuous" (2025); the "noising" myth-busting paper (to be named by the user) |
| M5 | Action multimodality and averaging (generative vs regression heads) | Diffusion Policy (2023); contested by M4 sources |
| M6 | Action representation (absolute vs delta vs relative, position vs velocity) | Diffusion Policy; UMI (2024) |
| M7 | Compliance and impedance in the action or low-level controller | Adaptive Compliance Policy (2024); compliance-aware DAgger/residual work (2025) |
| M8 | Phase structure: phase gating, sub-task segmentation, mode switching around contact | User's example ("85% → 25% without phase gating"), source unknown |
| M9 | Data: recovery/correction demos, demo quality, diversity vs quantity | Data scaling laws in IL (2024); data-quality-in-IL work (2023); recovery/correction data (2025) |
| M10 | Shortcut learning on proprioception or dataset artefacts | Shortcut learning in generalist robot policies (2025); proprio-removal ablations |
| M11 | Visual input design: wrist camera, viewpoint, pretrained vs scratch encoder, augmentation | robomimic; "what matters" studies (2024–2025) |
| M12 | Inference-time effects: latency, asynchronous execution, number of denoising steps | Real-time chunking (2025); Diffusion Policy latency ablations |

Fallback-question checklist: at least one paper that reports per-phase failure on an
insertion or assembly task (approach/grasp vs insertion), with an intervention that affects
one phase more than the other.

## 6. Scoring per source

For ChatGPT deep research, Claude's web search, each crawl, and search + crawl combined:

1. **Families covered** (M1–M12) fully (grade A) or partly (grade B only), plus families found
   beyond the checklist.
2. **Row precision:** the share of a source's rows whose paper ID, number and trial count
   check out against the paper (via OpenAlex/arXiv). Each wrong ID, number or misattribution
   counts as one factual error.
3. **Replication column:** for each verified mechanism, did the source find the replicating or
   contesting paper that exists in the union of all sources?
4. **Newest work:** verified rows from 2026 (and 2025 H2).
5. **Grasp vs insertion:** did the source answer the fallback question with a verified citation?
6. **Cost:** wall-clock time, and the share of the free OpenAlex daily allowance used.

For a crawl, a mechanism counts as covered if its evidence paper is in the crawl's data, the
same rule as in the NCA study. Finding it there still takes analysis, and the report will say
which scripts did that.

## 7. Hypotheses (stated in advance)

- **H1.** The crawl beats both search modes on the replication column, because forward
  citations of an ablation paper are where replications appear.
- **H2.** Search beats the crawl on 2026 work (papers with no reference lists in OpenAlex).
- **H3.** Most verified mechanisms are "single" or "weakly replicated"; fewer than a third are
  "replicated".
- **H4.** Few papers (at most a handful) separate grasp failures from insertion failures
  causally.
- **H5.** Search-seeded crawling again gives the best coverage per paper fetched.

## 8. Crawl plan (draft; settings to be fixed before the first run)

- **Crawl A, brief-seeded:** seeds = the papers named in the question (FACTR, robomimic, the
  noising paper, Diffusion Policy, ACT), resolved to OpenAlex IDs.
- **Crawl B, search-seeded:** the seeds of crawl A plus the papers named by Claude's short web
  search, which runs *after* this file is saved.
- **Title keywords (draft):** imitation, behavior/behaviour cloning, diffusion policy,
  visuomotor, policy learning, contact-rich, insertion, assembly, peg, force, tactile,
  haptic, compliance, compliant. Kept on the narrow side; the NCA study showed that broad
  keywords drift (there, into metallurgy CA and land-use CA).
- **Other settings:** as in the NCA study unless the record says otherwise (off-keyword
  setting 0.3, year weight 0.3, centrality weight 1, NMF 12 topics, Retraction Watch on), at
  the code commit recorded at run time.
- **ChatGPT run:** prompt as agreed on 2026-10-29, deep research mode; mode, date, run time
  and any follow-ups recorded with the output.

## 9. Known biases

- This checklist comes from my own prior knowledge, which favours well-known, older papers.
  "Found beyond the checklist" exists to offset that.
- I wrote both this checklist and the ChatGPT prompt, and the prompt's examples (FACTR,
  robomimic, noising) overlap M1, M2 and M4. All sources get the same examples.
- The short web search is deliberately short, as in the NCA study.

## Amendment 1 (2026-10-29, before any results were seen)

Sections 1–9 above are unchanged. Their SHA-256 at 2026-10-29T07:57:09Z was
`1dbab7988ca277369737418f7dd83dc0b52e73b8dc8757e2641cc1980110db16`.

- **Noising paper named:** *Much Ado About Noising: Dispelling the Myths of Generative Robotic
  Control* (2025). It is a seed of crawl A and the anchor for M4/M5.
- **Second ChatGPT run (prompt sensitivity).** The agreed prompt was written by an AI. The user
  will also run deep research on a short, human-written gist of the question. Both outputs are
  scored with section 6, separately, and reported side by side as "ChatGPT (structured AI
  prompt)" and "ChatGPT (human gist prompt)".
  - Caveat: the user had already seen the structured prompt before writing the gist, so the
    two prompts are not independent.
  - To keep the runs comparable: same mode (deep research), same day, each in a fresh chat
    with ChatGPT memory off (or a temporary chat), no follow-ups. Record the run time for each.
  - Extra measures for this comparison: the overlap of verified rows between the two runs, and
    which run reports trial counts and replication without being asked.

## Amendment 2 (2026-10-29, before any crawl was run or any ChatGPT output seen)

Fixes the crawl settings that section 8 left as drafts. Code: ArticleCrawler at commit `5c90d09`
(branch `fix/crawl-state-flags`). Script: `scripts/run_crawl.py`.

- **Seed version rule.** OpenAlex often keeps the arXiv preprint and the venue version as separate
  works, and many records have no reference list. For every seed, every OpenAlex version with at
  least one reference or citation is a seed; if none has, the resolved record is kept anyway.
  Seeds are resolved in `data/seeds.json` (`scripts/resolve_seeds.py`, `scripts/find_versions.py`).
- **Observed before crawling:** 11 of the 18 seed papers have no reference list in OpenAlex;
  *Much Ado About Noising* and *Past-Token Prediction* have neither references nor citations
  there. This supports H2 in advance and threatens H1: the replication column depends on
  citation links that OpenAlex may lack for recent arXiv-only papers.
- **Crawl A (brief):** 7 OpenAlex works (`scripts/seeds_brief.txt`): FACTR, robomimic, Much Ado
  About Noising, Diffusion Policy (3 versions), ACT.
- **Crawl B (search):** crawl A's seeds plus the 13 papers named by Claude's web search,
  20 works in all (`scripts/seeds_search.txt`). Search log: `search_log.md`.
- **Keywords:** the 14 title expressions in `scripts/run_crawl.py`. Matching is a
  case-insensitive substring test, so every ambiguous term is paired with a robotics term
  (e.g. `force` needs `polic`/`manipulat` and excludes `reinforcement`). Vision-language-action
  terms are left out on purpose, to avoid drowning the crawl in general VLA work. Checked on 11
  test titles: all intended matches and non-matches.
- **Settings:** 6 rounds × 50 papers, keyword-bypass setting 0.3, year weight 0.3, centrality
  weight 1, NMF 12 topics, Retraction Watch on, numpy seed 20261029.

## Amendment 3 (2026-10-29, after the three external outputs arrived, before any scoring)

- **NotebookLM deep research added** as a fifth source (not planned). Scored with section 6 like the
  others. Its prompt and run time are not recorded yet.
- **ChatGPT gist run answered in Dutch** although the prompt was English. This points to account
  language or memory settings carrying over; it is reported, not scored.
- Raw outputs as received: `data/raw/`. Step 1 of verification (does each cited paper exist with the
  claimed title?) is in `data/verify_ids.json` (`scripts/verify_ids.py`). Step 2 (numbers, trial counts,
  sim/real, against the paper text) follows; until then no row counts as verified.
