import json, re, collections, numpy as np, warnings
warnings.filterwarnings("ignore")
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
import umap, nltk
from nltk.stem import WordNetLemmatizer
try: nltk.data.find("corpora/wordnet")
except LookupError: nltk.download("wordnet", quiet=True)
lem=WordNetLemmatizer()
docs=json.load(open("corpus.json"))
texts=[(d["title"]+". "+d["abstract"]).strip() for d in docs]
model=SentenceTransformer("sentence-transformers/allenai-specter")
E=model.encode([d["title"]+"[SEP]"+d["abstract"] for d in docs],batch_size=32,normalize_embeddings=True,show_progress_bar=False)
U=umap.UMAP(n_components=8,n_neighbors=15,min_dist=0.0,metric="cosine",random_state=42).fit_transform(E)
scores={}
for k in range(6,15):
    lab=KMeans(k,n_init=20,random_state=42).fit_predict(U); scores[k]=round(float(silhouette_score(U,lab)),3)
print("silhouette",scores)
import os; k=int(os.environ.get("K")) if os.environ.get("K") else max(scores,key=scores.get)
lab=KMeans(k,n_init=20,random_state=42).fit_predict(U)
XY=umap.UMAP(n_components=2,n_neighbors=15,min_dist=0.15,metric="cosine",random_state=42).fit_transform(E)
domain={"neural","cellular","automaton","automata","nca","ncas","model","models","paper","propose","proposed","approach","method","result","show","use","using","based","new","study","work","learning","learn","network","networks","task","different","present","demonstrate","rule","ca","cell","cells","also","however","system","systems","can","one","two","provide","well"}
def tok(t):
    w=re.findall(r"[a-z][a-z\-]{2,}",t.lower()); w=[lem.lemmatize(x) for x in w]
    return [x for x in w if x not in ENGLISH_STOP_WORDS and x not in domain]
cv=CountVectorizer(tokenizer=tok,lowercase=False,ngram_range=(1,2),min_df=2,token_pattern=None)
X=cv.fit_transform(texts); vocab=np.array(cv.get_feature_names_out())
C=np.vstack([np.asarray(X[lab==c].sum(0)).ravel() for c in range(k)])
tf=C/C.sum(1,keepdims=True); idf=np.log(1+C.sum(1).mean()/(C.sum(0)+1)); ctf=tf*idf
clusters=[]
for c in range(k):
    m=np.where(lab==c)[0]; cen=E[m].mean(0)
    rep=m[np.argsort(-(E[m]@cen))][:5]
    yrs=collections.Counter(docs[i]["year"] for i in m)
    oat=collections.Counter(docs[i]["oa_topic"] for i in m).most_common(2)
    inst=collections.Counter(x for i in m for x in docs[i]["inst"]).most_common(3)
    clusters.append(dict(c=c,n=len(m),kw=list(vocab[np.argsort(-ctf[c])[:10]]),rep=[docs[i]["title"] for i in rep],years=dict(yrs),oa_topics=oat,inst=inst))
    print(f"\n#{c} n={len(m)} kw={clusters[-1]['kw']}\n  OA topics={oat}\n  inst={inst}\n  "+"\n  ".join(t[:110] for t in clusters[-1]['rep']))
pts=[dict(id=d["id"],x=float(XY[i,0]),y=float(XY[i,1]),c=int(lab[i]),t=d["title"],yr=d["year"],a=", ".join(d["authors"]),cites=d["cites"],abs=len(d["abstract"])>200) for i,d in enumerate(docs)]
oa_all=collections.Counter(d["oa_topic"] for d in docs).most_common(8)
print("\nOpenAlex topics overall:",oa_all)
json.dump(dict(k=k,silhouette=scores,clusters=clusters,points=pts,oa_topics=oa_all),open("nlp_out.json","w"))
