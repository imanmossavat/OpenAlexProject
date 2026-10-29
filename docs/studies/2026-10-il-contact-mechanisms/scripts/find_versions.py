"""For each seed, list all OpenAlex works with the same title (other versions), with ref and citation counts."""
import json, re, sys, urllib.parse, urllib.request
from pathlib import Path

ENV = Path("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
KEY = next((l.split("=", 1)[1].strip().strip('"') for l in ENV.read_text().splitlines()
            if l.startswith("OPENALEX_API_KEY")), "")
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())

seeds = json.loads(Path("../data/seeds.json").read_text())
for s in seeds:
    t = s["title"]
    q = urllib.parse.quote(t.split(":")[0] if len(t.split(":")[0]) > 12 else t)
    url = f"https://api.openalex.org/works?filter=title.search:{q}&per-page=25&select=id,display_name,publication_year,referenced_works_count,cited_by_count,primary_location&api_key={KEY}"
    res = json.load(urllib.request.urlopen(url, timeout=30))["results"]
    same = [r for r in res if norm(r["display_name"])[:40] == norm(t)[:40]]
    s["versions"] = [{"id": r["id"].rsplit("/", 1)[1], "year": r["publication_year"],
                      "refs": r["referenced_works_count"], "cites": r["cited_by_count"],
                      "venue": ((r.get("primary_location") or {}).get("source") or {}).get("display_name")}
                     for r in same]
    print(s["name"])
    for v in s["versions"]:
        print(f'   {v["id"]} {v["year"]} refs={v["refs"]:<3} cites={v["cites"]:<5} {v["venue"]}')
Path("../data/seeds.json").write_text(json.dumps(seeds, indent=1))
