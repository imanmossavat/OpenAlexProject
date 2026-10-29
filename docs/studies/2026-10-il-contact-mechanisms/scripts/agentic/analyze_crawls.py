"""Analyses 1, 2 and 5 of docs/studies/agentic-analyses.md for this study.
Usage (from fakenewscitationnetwork/, repo venv): analyze_crawls.py <brief.pkl> <search.pkl>
Writes data/agentic/crawl_analysis.json and adds in-crawl flags to data/agentic/corpus.json."""
import json, pickle, sys, ast, collections, logging, re
from pathlib import Path
logging.basicConfig(level=logging.ERROR)
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
import ArticleCrawler  # noqa: F401
D = Path(__file__).resolve().parents[2] / "data/agentic"
fr = {k: pickle.load(open(p, "rb")).data_coordinator.frames for k, p in zip(("A", "B"), sys.argv[1:3])}
ids = {k: set(f.df_paper_metadata.paperId) for k, f in fr.items()}
seedsA = {l.strip() for l in open(D.parents[1] / "scripts/seeds_brief.txt") if l.strip()}
seedsB = {l.strip() for l in open(D.parents[1] / "scripts/seeds_search.txt") if l.strip()}

# --- 2. coverage by year on the field set
F = json.loads((D / "field_set.json").read_text())
cov = collections.defaultdict(collections.Counter)
for w in F:
    c = cov[w["year"]]; c["refs" if w["refs"] else "norefs"] += 1
    c["A"] += w["id"] in ids["A"]; c["B"] += w["id"] in ids["B"]
    c["dark"] += (not w["refs"] and not w["cites"])
years = sorted(y for y in cov if y)
coverage = [dict(year=y, **{k: cov[y][k] for k in ("refs", "norefs", "A", "B", "dark")}) for y in years]
tot = collections.Counter(); [tot.update(cov[y]) for y in years]
linked = [w for w in F if w["refs"] or w["cites"]]
print("field set", len(F), dict(tot), "| linked", len(linked), "reached A", sum(w["id"] in ids["A"] for w in linked), "B", sum(w["id"] in ids["B"] for w in linked))
print("field set reached by year:", coverage)

# --- 1. seed citers and field-set institutions
C = json.loads((D / "seed_citers.json").read_text())
def grp(f):
    if f == "Computer Science": return "cs"
    if f in ("Engineering",): return "eng"
    if f in ("Medicine", "Neuroscience", "Biochemistry, Genetics and Molecular Biology", "Health Professions"): return "life"
    if f in ("Physics and Astronomy", "Materials Science", "Mathematics", "Chemistry", "Environmental Science", "Earth and Planetary Sciences"): return "phys"
    return "other"
by = collections.defaultdict(collections.Counter)
for w in C: by[w["year"]][grp(w["field"])] += 1
cyears = list(range(2021, 2027))
citers_by_year = [dict(year=y, **{k: by[y][k] for k in ("cs", "eng", "phys", "life", "other")}) for y in cyears]
def inst_counts(ws, n=14):
    ic, cc, iseed = collections.Counter(), collections.Counter(), collections.defaultdict(set)
    for w in ws:
        s = {tuple(x) for x in w["inst"]}
        for name, cty in s: ic[name] += 1; iseed[name] |= set(w.get("seeds", []))
        for cty in {c for _, c in s}: cc[cty] += 1
    return [dict(name=i, n=k, seeds=len(iseed[i])) for i, k in ic.most_common(n)], cc.most_common(10)
inst_citers, cty_citers = inst_counts(C)
inst_field, cty_field = inst_counts(F)
auth = collections.defaultdict(lambda: [0, set()])
for w in C:
    for a in w["authors"]: auth[a][0] += 1; auth[a][1] |= set(w["seeds"])
multi = sorted(((a, n, sorted(s)) for a, (n, s) in auth.items() if len(s) >= 3), key=lambda x: -x[1])[:15]
seed_counts = collections.Counter(s for w in C for s in w["seeds"])
print("citers per seed", dict(seed_counts)); print("institutions (field set)", inst_field[:8]); print("countries (field)", cty_field[:6])
print("multi-seed authors", multi[:8])

# --- 5. crawl diff: B vs A
def first(x):
    if isinstance(x, str):
        try: x = ast.literal_eval(x)
        except Exception: return x
    if isinstance(x, (list, tuple)) and len(x):
        v = x[0]; return v.get("display_name") if isinstance(v, dict) else v
    return None
mB = fr["B"].df_paper_metadata.set_index("paperId"); mA = fr["A"].df_paper_metadata.set_index("paperId")
newB = mB.loc[~mB.index.isin(ids["A"])]; newA = mA.loc[~mA.index.isin(ids["B"])]
robot = re.compile(r"robot|manipulat|grasp|imitation|polic|demonstration|visuomotor|tactile|insertion|assembly|dexterous", re.I)
def describe(new, frames, meta):
    ns = set(new.index)
    vr = frames.df_paper_references[frames.df_paper_references.referencePaperId.isin(ns)]
    vc = frames.df_paper_citations[frames.df_paper_citations.citedPaperId.isin(ns)]
    src = collections.Counter(list(vr.paperId) + list(vc.paperId))
    return dict(n=len(new), robot_share=round(float(new.title.fillna("").str.contains(robot).mean()), 3),
        fields=collections.Counter(new["fields"].map(first)).most_common(6),
        top_sources=[(str(meta.title.get(p, ""))[:100], int(meta.year.get(p) or 0), n) for p, n in src.most_common(8)])
diff = dict(overlap=len(ids["A"] & ids["B"]), onlyB=describe(newB, fr["B"], mB), onlyA=describe(newA, fr["A"], mA),
            field_onlyB=[w["title"] for w in F if w["id"] in ids["B"] and w["id"] not in ids["A"]],
            field_onlyA=[w["title"] for w in F if w["id"] in ids["A"] and w["id"] not in ids["B"]])
print("overlap", diff["overlap"], "onlyB", diff["onlyB"]["n"], diff["onlyB"]["robot_share"], diff["onlyB"]["fields"][:3])
print("onlyA", diff["onlyA"]["n"], diff["onlyA"]["robot_share"]); print("field-set only in B:", len(diff["field_onlyB"]), "only in A:", len(diff["field_onlyA"]))
for t in diff["onlyB"]["top_sources"][:6]: print("   pulled in by:", t)

# flags for topic-model corpus
corpus = json.loads((D / "corpus.json").read_text())
for d in corpus: d["inA"] = d["id"] in ids["A"]; d["inB"] = d["id"] in ids["B"]
(D / "corpus.json").write_text(json.dumps(corpus))
print("corpus in A", sum(d["inA"] for d in corpus), "in B", sum(d["inB"] for d in corpus), "either", sum(d["inA"] or d["inB"] for d in corpus), "of", len(corpus))
json.dump(dict(coverage=coverage, field_total=dict(tot), field_n=len(F), field_linked=len(linked),
    field_linked_reached={k: sum(w["id"] in ids[k] for w in linked) for k in ids},
    citers_by_year=citers_by_year, citers_n=len(C), citers_per_seed=dict(seed_counts),
    inst_citers=inst_citers, inst_field=inst_field, cty_citers=cty_citers, cty_field=cty_field, multi_seed_authors=multi, diff=diff),
    open(D / "crawl_analysis.json", "w"), indent=1, default=str)
