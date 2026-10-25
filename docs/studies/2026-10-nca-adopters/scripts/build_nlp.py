import json, collections
N=json.load(open("nlp_out.json"))
L={0:"Soft & modular robotics",1:"Vision, hardware & reasoning",2:"Games & procedural content",3:"Textures & graphics",
   4:"Artificial life & open-ended evolution",5:"NCA dynamics & theory",6:"Image & microscopy classification",
   7:"Physical & spatio-temporal simulation",8:"Medical image segmentation",9:"NCA meets deep learning & language",
   10:"Morphogenesis & developmental biology",11:"Quality-diversity methods"}
years=["≤2019"]+[str(y) for y in range(2020,2027)]
cl=[]
for c in N["clusters"]:
    row=collections.Counter()
    for y,n in c["years"].items():
        y=int(y) if y not in (None,"None") else 0
        row["≤2019" if y<=2019 else str(y)]+=n
    cl.append(dict(c=c["c"],label=L[c["c"]],n=c["n"],kw=c["kw"][:6],rep=c["rep"][:3],inst=[i for i,_ in c["inst"]],years=[row[y] for y in years]))
order=sorted(cl,key=lambda c:-c["n"])
pts=[dict(x=round(p["x"],3),y=round(p["y"],3),c=p["c"],t=p["t"],yr=p["yr"],a=p["a"]) for p in N["points"]]
json.dump(dict(years=years,clusters=order,points=pts,silhouette=N["silhouette"],oa_topics=N["oa_topics"]),open("nlp_report.json","w"),separators=(",",":"))
print(len(pts), [ (c["label"],c["n"]) for c in order])
