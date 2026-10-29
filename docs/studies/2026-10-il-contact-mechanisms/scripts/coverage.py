"""Which evidence papers are in each crawl's data? Usage: coverage.py <name>=<pkl> ..."""
import json, pickle, sys, logging, collections
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
logging.basicConfig(level=logging.WARNING)
import ArticleCrawler  # noqa: F401  (needed to unpickle)
ev = json.loads((Path(__file__).parent.parent / "data/evidence.json").read_text())
res = {}
for arg in sys.argv[1:]:
    name, pkl = arg.split("=", 1)
    c = pickle.load(open(pkl, "rb"))
    md = c.data_coordinator.frames.df_paper_metadata
    ids = set(md.paperId)
    yrs = collections.Counter(md.year.dropna().astype(int))
    print(f"\n== {name}: {len(ids)} papers in data; columns: {list(md.columns)[:25]}")
    res[name] = {"n_papers": len(ids), "hits": {}}
    for e in ev:
        vids = {v["id"] for v in e["versions"]}
        hit = sorted(vids & ids)
        res[name]["hits"][e["key"]] = hit
    print("in data:", [k for k, v in res[name]["hits"].items() if v])
(Path(__file__).parent.parent / "data/coverage.json").write_text(json.dumps(res, indent=1))
