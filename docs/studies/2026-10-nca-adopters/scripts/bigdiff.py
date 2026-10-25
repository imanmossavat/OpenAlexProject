import pickle, json, collections, re, ast
from dotenv import load_dotenv
load_dotenv("/Users/imanm/OpenAlexProject/fakenewscitationnetwork/.env")
import ArticleCrawler
ld=lambda p: pickle.load(open(p,"rb")).data_coordinator.frames
s=ld("out/nca_crawl/pkl/perm/nca_crawl_20261025202158.pkl"); b=ld("out/nca_crawl_big/pkl/perm/nca_crawl_big_20261025211531.pkl")
sm=s.df_paper_metadata.set_index("paperId"); bm=b.df_paper_metadata.set_index("paperId")
new=bm.loc[~bm.index.isin(sm.index)]
print("new papers",len(new))
def first(x):
    if isinstance(x,str):
        try: x=ast.literal_eval(x)
        except Exception: return x
    if isinstance(x,(list,tuple)) and x: 
        v=x[0]; return v.get("display_name") if isinstance(v,dict) else v
    return None
for col in ["fields","subfields","topics"]:
    print(col, collections.Counter(new[col].map(first)).most_common(10))
print("years", sorted(collections.Counter((new.year//5*5).fillna(0).astype(int)).items()))
ca=new.title.fillna("").str.contains(r"cellular automat",case=False)
nca=new.title.fillna("").str.contains(r"neural cellular automat|\bNCA\b",case=False)
print("title has 'cellular automat':",ca.sum()," NCA:",nca.sum())
print("NEW NCA titles:", list(new.title[nca])[:10])
# how reached: edges from selected papers
sel_b=set(bm.index[bm.selected==True]) if "selected" in bm else set()
E=collections.Counter()
ref=b.df_paper_references; cit=b.df_paper_citations
newset=set(new.index)
via_ref=ref[ref.referencePaperId.isin(newset)]; via_cit=cit[cit.citedPaperId.isin(newset)]
print("new papers reached as references:",via_ref.referencePaperId.nunique()," as citers:",via_cit.citedPaperId.nunique())
src=collections.Counter(list(via_ref.paperId)+list(via_cit.paperId))
print("\nTOP SAMPLED PAPERS THAT PULLED IN NEW PAPERS:")
for pid,n in src.most_common(15):
    t=bm.title.get(pid,""); print(f"  {n:4d}  {bm.year.get(pid)}  {str(t)[:95]}")
# sampled papers in big not in small
sampled_b=set(via_ref.paperId)|set(via_cit.paperId)
print("\nsources",len(sampled_b))
print("venues", collections.Counter(new.venue).most_common(10))
json.dump(dict(n=len(new),ca=int(ca.sum()),nca=int(nca.sum()),nca_titles=list(new.title[nca]),
  fields=collections.Counter(new["fields"].map(first)).most_common(8),
  top_sources=[(bm.title.get(p,""),int(bm.year.get(p) or 0),n) for p,n in src.most_common(15)],
  via_ref=int(via_ref.referencePaperId.nunique()),via_cit=int(via_cit.citedPaperId.nunique())),open("bigdiff.json","w"),default=str)
