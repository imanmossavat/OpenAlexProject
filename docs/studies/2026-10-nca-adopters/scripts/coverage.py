import os, json, requests, pickle, collections
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
key=os.environ["OPENALEX_API_KEY"]
import ArticleCrawler
c=pickle.load(open("out/nca_crawl/pkl/perm/nca_crawl_20261025202158.pkl","rb"))
crawl=set(c.data_coordinator.frames.df_paper_metadata.paperId)
citers={w["id"].split("/")[-1] for w in json.load(open("citers.json"))}
seeds={"W3006201994","W3130408838","W3199753215","W3180899834"}
works=[]; cursor="*"
while cursor:
    r=requests.get("https://api.openalex.org/works",params={"filter":'title.search:"neural cellular automata"|"neural cellular automaton"',"per_page":200,"cursor":cursor,"api_key":key,
      "select":"id,title,publication_year,referenced_works,primary_location,type"}).json()
    works+=r["results"]; cursor=r["meta"].get("next_cursor") if r["results"] else None
rows=[]
for w in works:
    wid=w["id"].split("/")[-1]; refs={x.split("/")[-1] for x in w["referenced_works"]}
    rows.append(dict(id=wid,year=w["publication_year"],title=w["title"],nrefs=len(refs),cites_seed=bool(refs&seeds),in_crawl=wid in crawl,is_citer=wid in citers,
      venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name")))
json.dump(rows,open("nca_titled.json","w"))
by=collections.defaultdict(lambda: collections.Counter())
for r in rows:
    y=r["year"]; b=by[y]; b["total"]+=1; b["norefs"]+=r["nrefs"]==0; b["cites_seed"]+=r["cites_seed"]; b["in_crawl"]+=r["in_crawl"]
print("total NCA-titled:",len(rows))
for y in sorted(by): print(y, dict(by[y]))
t=collections.Counter()
for r in rows: t["norefs"]+=r["nrefs"]==0; t["cites_seed"]+=r["cites_seed"]; t["in_crawl"]+=r["in_crawl"]; t["citer"]+=r["is_citer"]
print(t)
