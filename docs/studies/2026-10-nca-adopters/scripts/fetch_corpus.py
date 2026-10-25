import os, json, requests, re
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
key=os.environ["OPENALEX_API_KEY"]
ids=set(w["id"].split("/")[-1] for w in json.load(open("citers.json")))|{r["id"] for r in json.load(open("nca_titled.json"))}
ids|={"W3006201994","W3130408838","W3199753215","W3180899834"}
ids=sorted(ids); docs=[]
for i in range(0,len(ids),50):
    r=requests.get("https://api.openalex.org/works",params={"filter":"openalex:"+"|".join(ids[i:i+50]),"per_page":50,"api_key":key,
      "select":"id,title,publication_year,abstract_inverted_index,primary_topic,cited_by_count,authorships,referenced_works_count"}).json()
    for w in r["results"]:
        inv=w.get("abstract_inverted_index") or {}
        pos=sorted((p,t) for t,ps in inv.items() for p in ps); ab=" ".join(t for _,t in pos)
        pt=w.get("primary_topic") or {}
        docs.append(dict(id=w["id"].split("/")[-1],title=w["title"] or "",year=w["publication_year"],abstract=ab,
          oa_topic=pt.get("display_name"),oa_field=(pt.get("field") or {}).get("display_name"),cites=w["cited_by_count"],
          inst=sorted({i["display_name"] for a in w["authorships"] for i in a.get("institutions",[])})[:3],
          authors=[a["author"]["display_name"] for a in w["authorships"][:3]]))
# dedupe by normalized title (preprint + published copies)
seen={}; 
for d in sorted(docs,key=lambda d:(-len(d["abstract"]),-d["cites"])):
    k=re.sub(r"[^a-z0-9]","",d["title"].lower())[:80]
    if k and k not in seen: seen[k]=d
out=list(seen.values())
print("fetched",len(docs),"deduped",len(out),"with abstract",sum(1 for d in out if len(d["abstract"])>200))
json.dump(out,open("corpus.json","w"))
