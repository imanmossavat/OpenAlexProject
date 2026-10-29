"""For key evidence papers: list OpenAlex citers, and whether each is in a crawl. Usage: citers.py <name>=<pkl> ..."""
import json, pickle, sys, logging, urllib.request
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
import os; KEY = os.environ["OPENALEX_API_KEY"]
logging.basicConfig(level=logging.WARNING)
import ArticleCrawler  # noqa: F401
D = Path(__file__).parent.parent / "data"
ev = {e["key"]: e for e in json.loads((D / "evidence.json").read_text())}
crawls = {a.split("=")[0]: set(pickle.load(open(a.split("=")[1], "rb")).data_coordinator.frames.df_paper_metadata.paperId) for a in sys.argv[1:]}
KEYS = ["FACTR", "RDP", "ACP", "MatchLight", "DexForce", "robomimic", "MILE", "IntervenGen", "MTIL", "RTC", "EquiDiff", "Kim-M2R"]
out = {}
for k in KEYS:
    rows = []
    for v in ev[k]["versions"]:
        if not v["cites"]: continue
        cur = "*"
        while cur:
            r = json.load(urllib.request.urlopen(f"https://api.openalex.org/works?filter=cites:{v['id']}&per-page=200&cursor={cur}&select=id,display_name,publication_year&api_key={KEY}", timeout=60))
            rows += [dict(id=w["id"].rsplit("/",1)[1], title=w["display_name"], year=w["publication_year"]) for w in r["results"]]
            cur = r["meta"].get("next_cursor") if r["results"] else None
    seen = {}
    for r in rows: seen[r["id"]] = r
    rows = list(seen.values())
    for r in rows: r["in"] = [n for n, ids in crawls.items() if r["id"] in ids]
    out[k] = rows
    print(f"{k:12} citers={len(rows):4} " + " ".join(f"in_{n}={sum(n in r['in'] for r in rows)}" for n in crawls))
(D / "citers.json").write_text(json.dumps(out, indent=1))
