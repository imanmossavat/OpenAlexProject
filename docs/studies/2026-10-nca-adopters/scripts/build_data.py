import json, collections, networkx as nx
C=json.load(open("citers.json")); R=json.load(open("citer_refs.json")); T=json.load(open("nca_titled.json"))
seeds={"W3006201994":"Growing NCA (2020)","W3130408838":"Self-Organising Textures (2021)","W3199753215":"Earle et al. level generation (2022)","W3180899834":"Reaction-diffusion (2021)"}
def grp(w):
    f=((w.get("primary_topic") or {}).get("field") or {}).get("display_name")
    if f=="Computer Science": return "cs"
    if f in ("Biochemistry, Genetics and Molecular Biology","Medicine","Neuroscience"): return "life"
    if f in ("Engineering","Physics and Astronomy","Materials Science","Environmental Science","Chemistry"): return "eng"
    return "other"
# per-year stacked by field
yr=collections.defaultdict(lambda: collections.Counter())
for w in C: yr[w["publication_year"]][grp(w)]+=1
years=list(range(2020,2027))
citers_by_year=[{"year":y,**{k:yr[y][k] for k in ("cs","life","eng","other")}} for y in years]
# coverage
cov=collections.defaultdict(lambda: collections.Counter())
for r in T:
    if r["year"] and r["year"]>=2020:
        c=cov[r["year"]]; c["refs" if r["nrefs"] else "norefs"]+=1; c["crawl"]+=r["in_crawl"]
coverage=[{"year":y,"refs":cov[y]["refs"],"norefs":cov[y]["norefs"],"crawl":cov[y]["crawl"]} for y in years]
# institutions
inst=collections.Counter(); iseeds=collections.defaultdict(set)
for w in C:
    s={i["display_name"] for a in w["authorships"] for i in a.get("institutions",[])}
    for i in s: inst[i]+=1; iseeds[i]|=set(w["seeds"])
institutions=[{"name":i,"n":n,"seeds":len(iseeds[i])} for i,n in inst.most_common(12)]
# network
G=nx.Graph(); ids={w["id"].split("/")[-1]:w for w in C}
for s in seeds: G.add_node(s)
for wid,w in ids.items():
    G.add_node(wid)
    for r in R.get(wid,[]):
        if r in seeds or (r in ids and r!=wid): G.add_edge(wid,r)
pos=nx.spring_layout(G,seed=7,k=0.09,iterations=300)
xs=[p[0] for p in pos.values()]; ys=[p[1] for p in pos.values()]
nx_=lambda v:(v-min(xs))/(max(xs)-min(xs)); ny_=lambda v:(v-min(ys))/(max(ys)-min(ys))
nodes=[]
for n in G.nodes:
    x,y=pos[n]
    if n in seeds: nodes.append(dict(id=n,x=round(nx_(x),4),y=round(ny_(y),4),seed=1,t=seeds[n],g="seed",c=0,deg=G.degree(n)))
    else:
        w=ids[n]; inst_=sorted({i["display_name"] for a in w["authorships"] for i in a.get("institutions",[])})
        nodes.append(dict(id=n,x=round(nx_(x),4),y=round(ny_(y),4),seed=0,t=w["title"],y_=w["publication_year"],g=grp(w),c=w["cited_by_count"],
          a=", ".join(a["author"]["display_name"] for a in w["authorships"][:3])+(" et al." if len(w["authorships"])>3 else ""),i="; ".join(inst_[:2]),deg=G.degree(n)))
edges=[[u,v] for u,v in G.edges]
print("nodes",len(nodes),"edges",len(edges),"isolated",sum(1 for n in G.nodes if G.degree(n)==0))
json.dump(dict(citers_by_year=citers_by_year,coverage=coverage,institutions=institutions,nodes=nodes,edges=edges),open("report_data.json","w"),separators=(",",":"))
print(citers_by_year); print(coverage); print(institutions)
