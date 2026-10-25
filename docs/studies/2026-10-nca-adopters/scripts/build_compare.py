import json, collections
I={k:set(v) for k,v in json.load(open("corpus_in_crawl.json")).items()}
anyc=set().union(*I.values())
T=json.load(open("nca_titled.json")); R=json.load(open("report_data.json"))
cov=collections.defaultdict(collections.Counter)
for r in T:
    if r["year"] and r["year"]>=2020:
        cov[r["year"]]["ag"]+=r["id"] in I["agentic"]; cov[r["year"]]["big"]+=r["id"] in I["big"]
for row in R["coverage"]: row["ag"]=cov[row["year"]]["ag"]; row["big"]=cov[row["year"]]["big"]
json.dump(R,open("report_data.json","w"),separators=(",",":"))
N={p["id"]:p for p in json.load(open("nlp_out.json"))["points"]}
rep=json.load(open("nlp_report.json"))
ids=list(N)  # nlp_report points keep nlp_out order
for p,i in zip(rep["points"],ids): assert p["t"]==N[i]["t"]; p["cr"]=int(i in anyc)
inc=collections.Counter(p["c"] for p in rep["points"] if p["cr"])
for c in rep["clusters"]: c["inc"]=inc[c["c"]]
json.dump(rep,open("nlp_report.json","w"),separators=(",",":"))
print(R["coverage"]); print([(c["label"],c["n"],c["inc"]) for c in rep["clusters"]])
