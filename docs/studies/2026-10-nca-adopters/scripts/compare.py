import pickle, json, collections
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
import ArticleCrawler
T=json.load(open("nca_titled.json")); nca={r["id"]:r for r in T}
corpus={d["id"] for d in json.load(open("corpus.json"))}
C={w["id"].split("/")[-1] for w in json.load(open("citers.json"))}
DOM=[("Surveys and reviews",["W4416818787","W7157701221","W7214021387"]),
 ("Medical imaging",["W4379660320"]),("Microscopy / blood cells",["W4403071100"]),("Developmental biology",["W4416818787"]),
 ("Robotics",["W3151337059"]),("Graphics and textures",["W4400820364"]),("Games",["W3199753215"]),("Photonic hardware",["W4403229727"]),
 ("Gold nanoparticles / materials",["W4396553883","W4383032390"]),("Edge vision",["W7164000886"]),
 ("Physical simulation",["W7220892747","W4408224315","W2809252620"]),("Reasoning",["W4417124902","W7214964112"]),
 ("Language models",["W7135075179"]),("DNA computing",["W4413946390"])]
EVID=sorted({i for _,ids in DOM for i in ids})
runs={"small":"out/nca_crawl/pkl/perm/nca_crawl_20261025202158.pkl","big":"out/nca_crawl_big/pkl/perm/nca_crawl_big_20261025211531.pkl",
      "agentic":"out/nca_crawl_agentic/pkl/perm/nca_crawl_agentic_20261025215446.pkl"}
out={}; sets={}
for k,p in runs.items():
    f=pickle.load(open(p,"rb")).data_coordinator.frames; ids=set(f.df_paper_metadata.paperId); sets[k]=ids
    m=f.df_paper_metadata
    sel=set(m.paperId[m.selected==True]) if "selected" in m else set()
    out[k]=dict(papers=len(ids),abstracts=len(f.df_abstract),authors=len(f.df_author),nca=len(ids&set(nca)),
      nca_refs=len({i for i in ids&set(nca) if nca[i]["nrefs"]}),nca_norefs=len({i for i in ids&set(nca) if not nca[i]["nrefs"]}),
      citers=len(ids&C),corpus=len(ids&corpus),evid=len(ids&set(EVID)),
      nca2026=len({i for i in ids&set(nca) if nca[i]["year"]==2026}),
      domains={d:[i for i in e if i in ids] for d,e in DOM})
    print(k,{x:y for x,y in out[k].items() if x!="domains"})
tot=dict(nca=len(nca),nca_refs=sum(1 for r in T if r["nrefs"]),nca_norefs=sum(1 for r in T if not r["nrefs"]),corpus=len(corpus),evid=len(EVID))
a,b,s=sets["agentic"],sets["big"],sets["small"]
N=set(nca)
only_ag=sorted(a&N-b-s); only_bs=sorted((b|s)&N-a)
print("NCA only in agentic:",len(only_ag),[nca[i]["title"][:60] for i in only_ag])
print("NCA in brief-seeded but not agentic:",len(only_bs),[nca[i]["title"][:60] for i in only_bs])
print("union all crawls NCA:",len((a|b|s)&N))
print("2026 NCA:",{k:len({i for i in v&N if nca[i]["year"]==2026}) for k,v in sets.items()}, "of",sum(1 for r in T if r["year"]==2026))
ag_seeds=[l.strip() for l in open("seeds_agentic.txt") if l.strip()]
print("agentic seeds with no refs:",[(x,nca.get(x,{}).get("nrefs")) for x in ag_seeds])
print("overlap agentic & big:",len(a&b),"agentic-only papers:",len(a-b-s))
for k in out:
    print(k,"missing domains:",[d for d,v in out[k]["domains"].items() if not v])
json.dump(dict(runs=out,totals=tot,dom=DOM,only_ag=[(i,nca[i]["title"],nca[i]["year"]) for i in only_ag],
  only_bs=[(i,nca[i]["title"],nca[i]["year"]) for i in only_bs],union=len((a|b|s)&N),overlap_ab=len(a&b)),open("compare.json","w"),indent=1)
json.dump({k:sorted(v&corpus) for k,v in sets.items()},open("corpus_in_crawl.json","w"))
