import os, json, requests, pickle
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
key=os.environ["OPENALEX_API_KEY"]
seeds={"W3006201994","W3130408838","W3199753215","W3180899834"}
citers={w["id"].split("/")[-1] for w in json.load(open("citers.json"))}
import ArticleCrawler
c=pickle.load(open("out/nca_crawl/pkl/perm/nca_crawl_20261025202158.pkl","rb"))
crawl_ids=set(c.data_coordinator.frames.df_paper_metadata.paperId)
queries={
 "Sudhakaran 3D artefacts":"Growing 3D Artefacts and Functional Machines with Neural Cellular Automata",
 "Cells2Pixels":"cells2pixels neural cellular automata",
 "Etcheverry reasoning NCA":"neural cellular automata sudoku ARC reasoning",
 "Lee NCA LM pretraining":"neural cellular automata language model pre-training",
 "Celikyilmaz hierarchical NCA":"evolving hierarchical neural cellular automata",
 "Xu Miikkulainen ARC":"neural cellular automata ARC-AGI",
 "Med-NCA":"Med-NCA robust lightweight segmentation neural cellular automata",
}
out={}
for k,q in queries.items():
    r=requests.get("https://api.openalex.org/works",params={"search":q,"per_page":4,"api_key":key,
      "select":"id,title,publication_year,authorships,primary_location,referenced_works,cited_by_count"}).json()
    out[k]=[]
    for w in r.get("results",[]):
        wid=w["id"].split("/")[-1]
        refs={x.split("/")[-1] for x in w.get("referenced_works",[])}
        inst=sorted({i["display_name"] for a in w["authorships"] for i in a.get("institutions",[])})
        rec=dict(id=wid,year=w["publication_year"],title=w["title"],venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                 authors=[a["author"]["display_name"] for a in w["authorships"]][:6],inst=inst[:6],n_refs=len(refs),
                 cites_seed=bool(refs&seeds),in_citers=wid in citers,in_crawl=wid in crawl_ids,cited_by=w["cited_by_count"])
        out[k].append(rec)
        print(f"[{k}] {wid} {rec['year']} {rec['title'][:80]} | {rec['venue']} | refs={rec['n_refs']} citesSeed={rec['cites_seed']} inCrawl={rec['in_crawl']} | {rec['authors'][:4]} | {rec['inst'][:4]}")
json.dump(out,open("gpt_verify.json","w"),indent=1)
