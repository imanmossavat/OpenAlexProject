import pickle, json, collections, ast
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
import ArticleCrawler
ld=lambda p: pickle.load(open(p,"rb")).data_coordinator.frames
s=ld("out/nca_crawl/pkl/perm/nca_crawl_20261025202158.pkl"); b=ld("out/nca_crawl_big/pkl/perm/nca_crawl_big_20261025211531.pkl")
a=ld("out/nca_crawl_agentic/pkl/perm/nca_crawl_agentic_20261025215446.pkl")
am=a.df_paper_metadata.set_index("paperId"); old=set(s.df_paper_metadata.paperId)|set(b.df_paper_metadata.paperId)
new=am.loc[~am.index.isin(old)]
def first(x):
    if isinstance(x,str):
        try: x=ast.literal_eval(x)
        except Exception: return x
    if isinstance(x,(list,tuple)) and len(x):
        v=x[0]; return v.get("display_name") if isinstance(v,dict) else v
    return None
fields=collections.Counter(new["fields"].map(first)).most_common(8)
ttl=new.title.fillna("")
nca=ttl.str.contains(r"neural cellular automat",case=False); ca=ttl.str.contains("cellular automat",case=False)
ncaacr=ttl.str.contains(r"\bNCAs?\b")
ref=a.df_paper_references; cit=a.df_paper_citations; ns=set(new.index)
vr=ref[ref.referencePaperId.isin(ns)]; vc=cit[cit.citedPaperId.isin(ns)]
src=collections.Counter(list(vr.paperId)+list(vc.paperId))
top=[(str(am.title.get(p,""))[:90],int(am.year.get(p) or 0),n) for p,n in src.most_common(10)]
land=ttl.str.contains("land use|urban",case=False)
print(len(new),"fields",fields,"\nNCA-titled",nca.sum(),"CA",ca.sum(),"NCA acronym",ncaacr.sum(),"land/urban",land.sum())
print("via ref",vr.referencePaperId.nunique(),"via cit",vc.citedPaperId.nunique())
for t in top: print(t)
print("acronym titles:",list(ttl[ncaacr & ~nca])[:12])
print("years", sorted(collections.Counter((new.year//5*5).fillna(0).astype(int)).items()))
json.dump(dict(n=len(new),fields=fields,nca=int(nca.sum()),ca=int(ca.sum()),acr=int((ncaacr&~nca).sum()),acr_titles=list(ttl[ncaacr&~nca])[:20],land=int(land.sum()),
  via_ref=int(vr.referencePaperId.nunique()),via_cit=int(vc.citedPaperId.nunique()),top=top),open("agdiff.json","w"),indent=1,default=str)
