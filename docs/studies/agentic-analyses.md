# Agentic analyses on top of an ArticleCrawler crawl

This file describes the analyses Claude ran **on top of** ArticleCrawler's output in the NCA study
(`2026-10-nca-adopters/`, 25 October 2026). They are reused in the imitation-learning study
(`2026-10-il-contact-mechanisms/`, 29 October 2026). None of them is part of the crawler. Each one is a script
that reads the crawl's pickle and/or calls the OpenAlex API directly. In the reports they carry the label
**Agentic analysis**. What the crawler produces itself carries **Repo output**.

The crawler's own output is: the set of papers and citation links (in the pickle's
`data_coordinator.frames`), the Obsidian-style vault of markdown files, an NMF/LDA topic model on the abstracts
of processed papers, and the Retraction Watch flags. Everything below is extra.

Paths to scripts are relative to each study's `scripts/` folder. All scripts read `OPENALEX_API_KEY` from
`fakenewscitationnetwork/.env`.

---

## 1. Seed-citer analysis: who builds on the seed papers

**Question it answers.** Who works on this topic: which fields, institutions, countries, authors and venues?

**Input.** The seed papers' OpenAlex IDs.

**Method.**
1. For each seed, page through `GET /works?filter=cites:<seed>` (200 per page, cursor paging), selecting
   `id, title, publication_year, cited_by_count, authorships, primary_location, primary_topic, is_retracted`.
2. Merge citers across seeds and record which seeds each citer cites.
3. Count:
   - fields, from the OpenAlex primary topic's field;
   - venues;
   - institutions, once per paper, from `authorships[].institutions`;
   - countries;
   - authors, with the number of distinct seeds they cite (an author citing several seeds works across
     several strands of the topic).
4. List the most-cited citers.

**Output.** `citers.json`, plus printed tables. In the NCA report:
- "Who cites the seeds, by field": a stacked bar chart of citers per year, with fields grouped into computer
  science / engineering and physical sciences / life sciences / other.
- "Most active institutions": a bar chart of papers per institution, annotated with how many seeds the
  institution cites.
- The narrative table of groups (TU Darmstadt, Levin lab, ITU Copenhagen, …).

**NCA scripts.** `inst.py` (fetch and counts), `build_data.py` (chart data).

**Caveats.**
- OpenAlex under-indexes citations from arXiv-only and Distill papers, so treat counts as relative.
- OpenAlex institution matching sometimes drops affiliations.
- Citers of a very general seed (in the IL study: Diffusion Policy, ACT) describe the wider community, not
  the specific topic.

---

## 2. Coverage by year: the structural blind spot

**Question it answers.** How much of the field's literature can a citation crawl reach at all, and how much
did each crawl reach?

**Input.** A reference set of works defined independently of the crawl. In NCA: every OpenAlex work with
"neural cellular automata/automaton" in the title (210 works).

**Method.**
1. Fetch the reference set with `filter=title.search:...` and cursor paging, selecting `referenced_works`
   and `cited_by_count`.
2. For each work, record:
   - the number of references OpenAlex holds (0 means OpenAlex has no reference list);
   - whether it cites a seed;
   - whether it is in each crawl's `df_paper_metadata.paperId`.
3. Tabulate by year: works with references, works without, and the number reached by each crawl.

**The key point.** A crawl reaches a work only by following a link: the work cites a crawled paper (so it
needs references in OpenAlex) or a crawled paper cites it (so it needs citations). A work with neither is
reachable only as a seed. In NCA, 59% of the reference set had no reference list, and 72% for 2026.

**Output.** `nca_titled.json`. In the report: "Coverage by year", a stacked bar chart (with vs without
references) with dots for each crawl's reach, plus a table.

**NCA scripts.** `coverage.py`, `build_data.py`, `build_compare.py`.

---

## 3. Citation network of the seed citers

**Question it answers.** Does the community split into sub-communities, and which papers sit at the centre?

**Method.**
1. Fetch `referenced_works` for every citer (batches of 50 via `filter=openalex:id1|id2|…`).
2. Build an undirected graph with networkx:
   - nodes are the citers plus the seeds;
   - there is an edge when one node references another node in the set.
3. Lay it out with `nx.spring_layout(G, seed=7, k=0.09, iterations=300)` and normalise to [0, 1].
4. Draw it as SVG:
   - dot size from citation count;
   - colour from field group (later, topic cluster);
   - seeds ringed;
   - hover shows title, authors and institution.

**Output.** `citer_refs.json`, and the nodes and edges in `report_data.json`. In the NCA report: "Citation
network of the seed citers" (239 nodes). Visible regions there: games around Earle et al., biology and
robotics near Growing NCA, graphics near Textures.

**NCA scripts.** `more.py` (references), `build_data.py` (graph and layout).

**Caveats.** A spring layout is not unique; the fixed seed makes it reproducible, not canonical. Missing
OpenAlex references remove edges, so recent papers often show up as isolated dots.

---

## 4. Embedding topic model (topic map, topic table, topics over time)

**Question it answers.** What are the sub-topics, how big is each, how have they grown, and which ones did
the crawls miss?

**Corpus.** The seed citers plus the reference set, de-duplicated by normalised title (preprint and venue
copies collapse to the record with the longest abstract). NCA: 361 papers.

**Method.**
1. Fetch title and abstract (rebuilt from OpenAlex's `abstract_inverted_index`), year, OpenAlex topic,
   institutions and authors (`fetch_corpus.py`).
2. Embed `title [SEP] abstract` with **SPECTER** (`sentence-transformers/allenai-specter`), a model trained
   on scientific papers, with normalised embeddings.
3. Reduce with **UMAP** to 8 dimensions (`n_neighbors=15, min_dist=0.0, metric=cosine, random_state=42`).
4. Cluster with **k-means** for k = 6…14 (`n_init=20`) and score each k with the silhouette. Pick k: in NCA,
   k=12 had silhouette 0.468 against the best 0.470 at k=6, and gave more readable topics.
5. Make a separate 2D UMAP (`min_dist=0.15`) for the map only. Clusters come from the 8D space.
6. Extract keywords with **class-based TF-IDF** over each cluster's concatenated text. Use lemmatised
   unigrams and bigrams, English stop words plus a domain stop list (the topic's own name, generic research
   words), `min_df=2`:

   $$ \mathrm{ctfidf}_{c,w} = \frac{n_{c,w}}{\sum_{w'} n_{c,w'}} \cdot \log\!\Big(1 + \frac{\bar{N}}{\sum_{c'} n_{c',w} + 1}\Big), $$

   where $n_{c,w}$ is the count of word $w$ in cluster $c$ and $\bar N$ is the mean cluster size in words.
7. For each cluster, collect the five papers closest to the centroid (cosine), a year histogram, the top
   OpenAlex topics and the top institutions.
8. **Naming.** Claude names each cluster from its keywords and its centre papers. This is a judgement call
   and is labelled as such.
9. **Crawl coverage per topic.** A paper is drawn as a filled dot if it is in any crawl's data and hollow if
   it is not. The topic table gives "in crawler data" counts.

**Output.** `corpus.json`, `nlp_out.json`, `nlp_report.json`. In the NCA report:
- "Topic map": an interactive scatter where you pick a topic to highlight it.
- A topic table: name, size, number in crawl data, keywords, institutions, typical paper.
- "Topics over time": a heatmap of papers per topic per year.

**NCA scripts.** `fetch_corpus.py`, `nlp.py` (run as `K=12 python nlp.py`; needs `sentence-transformers` and
`umap-learn`), `build_nlp.py` (labels), `build_compare.py` (crawl flags).

**Environment note (29 Oct 2026).** No single local environment has both `sentence-transformers` and
`umap-learn`. The IL study therefore runs step 2 in the `REFLECT` conda env (sentence-transformers, torch) and
steps 3–7 in the `TTS` env (umap-learn, scikit-learn, nltk). Both read and write files in the study folder;
nothing is installed.

**Caveats.** A different k moves topic boundaries. Clusters near the centre of the map act as catch-alls.
Treat the model as a map for exploring, not as a classification.

---

## 5. Crawl-to-crawl comparison: what a bigger or differently seeded crawl adds

**Question it answers.** Does a bigger crawl, or one seeded from search, add relevant papers or just volume?

**Method.**
1. Load two pickles and take the papers in crawl X that are not in crawl Y.
2. For those new papers, count:
   - OpenAlex fields (first entry of `fields`);
   - year buckets;
   - titles that match the topic, and titles that match known false friends (in NCA: classic "cellular
     automata" in metallurgy, "land use" CA).
3. Find **who pulled them in**: count, per sampled paper, how many new papers entered through its
   references (`df_paper_references`) or its citers (`df_paper_citations`).
4. Compare reference-set coverage across crawls: union, overlap, papers unique to each crawl.

**Output.** `bigdiff.json`, `agdiff.json`, `compare.json`. In the NCA report: "More papers does not mean more
NCA". Doubling the crawl added 3,169 papers but 5 NCA papers, and the drift came from regeneration biology and
metallurgy CA.

**NCA scripts.** `bigdiff.py`, `agdiff.py`, `compare.py`.

---

## 6. Checking external claims against OpenAlex and the crawl

**Question it answers.** Are the papers a search tool cites real, and would the crawl have found them?

**Method.** Search OpenAlex for each claimed paper. Record year, venue, authors, institutions, number of
references, whether it cites a seed, and whether it is in the crawl.

**NCA script.** `verify_gpt.py` → `gpt_verify.json`.

**Changed in the IL study.** A paper missing from OpenAlex is not evidence that it does not exist, because
OpenAlex lags on recent work. Existence is checked on the web and on arXiv. Every number, trial count and
sim/real label is then checked against the paper's full text (`data/verification.md`). OpenAlex is used only
for crawl coverage and IDs.

---

## What this implies for the crawler

All six analyses were needed to turn a crawl into answers. Candidates for building into ArticleCrawler:

1. A seed-citer report: fields, institutions, authors, top citers.
2. A coverage report against a reference set, including the share of works with no links in OpenAlex.
3. Citation-network export with a layout.
4. An embedding topic model alongside NMF/LDA, with crawl-coverage flags.
5. A crawl diff: new papers, their fields and the papers that pulled them in.
6. A fallback reference source for works OpenAlex holds without links, and merging of preprint and venue
   versions.
