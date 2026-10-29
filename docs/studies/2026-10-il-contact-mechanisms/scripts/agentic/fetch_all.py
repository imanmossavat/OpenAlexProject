"""Fetch the analysis populations from OpenAlex (see docs/studies/agentic-analyses.md, analyses 1, 2 and 4).

- seed citers: works citing any brief seed (crawl A's 7 seed records)
- field set: title query for contact-rich imitation learning, 2023 onward (the reference set for coverage)
- evidence: the 36 evidence papers (all versions)
Writes data/agentic/{seed_citers,field_set,corpus}.json
"""
import json, re, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = ROOT / "data/agentic"
ENV = Path("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
KEY = next(l.split("=", 1)[1].strip().strip('"') for l in ENV.read_text().splitlines() if l.startswith("OPENALEX_API_KEY"))
SEL = "id,title,publication_year,cited_by_count,authorships,primary_location,primary_topic,referenced_works,abstract_inverted_index,is_retracted"
FIELD_Q = ('(imitation OR "diffusion policy" OR "diffusion policies" OR "behavior cloning" OR "behaviour cloning" OR visuomotor '
           'OR "learning from demonstration" OR "learning from demonstrations" OR "action chunking" OR "policy learning" '
           'OR "manipulation policy" OR "manipulation policies") AND ("contact-rich" OR insertion OR assembly OR force OR tactile '
           'OR visuotactile OR compliance OR compliant OR peg OR impedance OR wiping)')

def get(params):
    params = {**params, "api_key": KEY}
    for i in range(4):
        try: return json.load(urllib.request.urlopen("https://api.openalex.org/works?" + urllib.parse.urlencode(params), timeout=60))
        except Exception as e: time.sleep(2 * (i + 1)); err = e
    raise err

def page(flt):
    cur, out = "*", []
    while cur:
        r = get({"filter": flt, "per-page": 200, "cursor": cur, "select": SEL})
        out += r["results"]; cur = r["meta"].get("next_cursor") if r["results"] else None
    return out

def slim(w):
    inv = w.get("abstract_inverted_index") or {}
    ab = " ".join(t for _, t in sorted((p, t) for t, ps in inv.items() for p in ps))
    pt = w.get("primary_topic") or {}
    return dict(id=w["id"].rsplit("/", 1)[1], title=w["title"] or "", year=w["publication_year"], cites=w["cited_by_count"],
                refs=[x.rsplit("/", 1)[1] for x in w.get("referenced_works") or []], abstract=ab,
                field=(pt.get("field") or {}).get("display_name"), topic=pt.get("display_name"),
                venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                authors=[a["author"]["display_name"] for a in w["authorships"]],
                inst=[[i["display_name"], i.get("country_code")] for a in w["authorships"] for i in a.get("institutions", [])],
                retracted=w.get("is_retracted"))

seeds = [l.strip() for l in open(ROOT / "scripts/seeds_brief.txt") if l.strip()]
names = {s["id"]: s["name"] for s in json.loads((ROOT / "data/seeds.json").read_text())}
for s in json.loads((ROOT / "data/seeds.json").read_text()):
    for v in s.get("versions", []): names[v["id"]] = s["name"]
citers = {}
for s in seeds:
    for w in page(f"cites:{s}"):
        d = citers.setdefault(w["id"], dict(slim(w), seeds=set())); d["seeds"].add(names.get(s, s))
for d in citers.values(): d["seeds"] = sorted(d["seeds"])
print("seed citers", len(citers))
field = [slim(w) for w in page(f"title.search:{FIELD_Q},from_publication_date:2023-01-01")]
print("field set", len(field))
ev = json.loads((ROOT / "data/evidence.json").read_text())
ev_ids = [v["id"] for e in ev for v in e["versions"]]
evw = []
for i in range(0, len(ev_ids), 50):
    evw += get({"filter": "openalex:" + "|".join(ev_ids[i:i+50]), "per-page": 50, "select": SEL})["results"]
evw = [slim(w) for w in evw]
key_of = {v["id"]: e["key"] for e in ev for v in e["versions"]}
for d in evw: d["evidence"] = key_of.get(d["id"])
print("evidence records", len(evw))
(OUT / "seed_citers.json").write_text(json.dumps(list(citers.values())))
(OUT / "field_set.json").write_text(json.dumps(field))
# topic-model corpus: union, de-duplicated by normalised title (keep the record with the longest abstract)
pool = [dict(d, src="citer") for d in citers.values()] + [dict(d, src="field") for d in field] + [dict(d, src="evidence") for d in evw]
srcs = {}
for d in pool:
    k = re.sub(r"[^a-z0-9]", "", d["title"].lower())[:80]
    srcs.setdefault(k, set()).add(d["src"])
best = {}
for d in sorted(pool, key=lambda d: (-len(d["abstract"]), -d["cites"])):
    k = re.sub(r"[^a-z0-9]", "", d["title"].lower())[:80]
    if k and k not in best: best[k] = dict(d, srcs=sorted(srcs[k]))
corpus = list(best.values())
print("corpus", len(corpus), "with abstract", sum(len(d["abstract"]) > 200 for d in corpus))
(OUT / "corpus.json").write_text(json.dumps(corpus))
