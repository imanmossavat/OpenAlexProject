"""Analysis 4, steps 3-7: UMAP 8D, k-means (silhouette over k=6..14), 2D map, c-TF-IDF keywords.
Run with the TTS conda env (umap-learn). K=<k> to fix k."""
import json, os, re, collections, warnings, numpy as np
warnings.filterwarnings("ignore")
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
import umap, nltk
from nltk.stem import WordNetLemmatizer
try: nltk.data.find("corpora/wordnet")
except LookupError: nltk.download("wordnet", quiet=True)
lem = WordNetLemmatizer()
D = Path(__file__).resolve().parents[2] / "data/agentic"
docs = json.loads((D / "corpus.json").read_text()); E = np.load(D / "embeddings.npy")
U = umap.UMAP(n_components=8, n_neighbors=15, min_dist=0.0, metric="cosine", random_state=42).fit_transform(E)
scores = {k: round(float(silhouette_score(U, KMeans(k, n_init=20, random_state=42).fit_predict(U))), 3) for k in range(6, 15)}
print("silhouette", scores)
k = int(os.environ["K"]) if os.environ.get("K") else max(scores, key=scores.get)
lab = KMeans(k, n_init=20, random_state=42).fit_predict(U)
XY = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.15, metric="cosine", random_state=42).fit_transform(E)
domain = {"robot", "robotic", "robotics", "learning", "learn", "policy", "policies", "imitation", "manipulation", "task", "tasks",
          "method", "methods", "approach", "model", "models", "paper", "propose", "proposed", "result", "results", "show", "use", "using",
          "based", "new", "study", "work", "demonstrate", "performance", "framework", "also", "however", "system", "systems", "can",
          "one", "two", "provide", "well", "achieve", "enable", "existing", "real", "world", "real-world", "experiment", "experiments"}
def tok(t):
    w = [lem.lemmatize(x) for x in re.findall(r"[a-z][a-z\-]{2,}", t.lower())]
    return [x for x in w if x not in ENGLISH_STOP_WORDS and x not in domain]
texts = [(d["title"] + ". " + d["abstract"]).strip() for d in docs]
cv = CountVectorizer(tokenizer=tok, lowercase=False, ngram_range=(1, 2), min_df=2, token_pattern=None)
X = cv.fit_transform(texts); vocab = np.array(cv.get_feature_names_out())
C = np.vstack([np.asarray(X[lab == c].sum(0)).ravel() for c in range(k)])
ctf = (C / C.sum(1, keepdims=True)) * np.log(1 + C.sum(1).mean() / (C.sum(0) + 1))
clusters = []
for c in range(k):
    m = np.where(lab == c)[0]; cen = E[m].mean(0); rep = m[np.argsort(-(E[m] @ cen))][:5]
    inst = collections.Counter(x[0] for i in m for x in {tuple(y) for y in docs[i]["inst"]}).most_common(3)
    clusters.append(dict(c=c, n=len(m), kw=list(vocab[np.argsort(-ctf[c])[:10]]), rep=[docs[i]["title"] for i in rep],
        years=dict(collections.Counter(docs[i]["year"] for i in m)), inst=inst,
        field=sum("field" in docs[i]["srcs"] for i in m), evidence=[docs[i].get("evidence") for i in m if docs[i].get("evidence")],
        incrawl=sum(docs[i]["inA"] or docs[i]["inB"] for i in m)))
    print(f"\n#{c} n={len(m)} field={clusters[-1]['field']} crawl={clusters[-1]['incrawl']} ev={clusters[-1]['evidence']}\n  kw={clusters[-1]['kw']}\n  inst={inst}\n  " + "\n  ".join(t[:105] for t in clusters[-1]["rep"][:4]))
pts = [dict(id=d["id"], x=round(float(XY[i, 0]), 3), y=round(float(XY[i, 1]), 3), c=int(lab[i]), t=d["title"], yr=d["year"],
            a=", ".join(d["authors"][:3]), cr=int(d["inA"] or d["inB"]), fs=int("field" in d["srcs"]), ev=d.get("evidence")) for i, d in enumerate(docs)]
json.dump(dict(k=k, silhouette=scores, clusters=clusters, points=pts), open(D / "topics.json", "w"))
