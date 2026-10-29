"""Analysis 4, step 2: SPECTER embeddings of title [SEP] abstract. Run with the REFLECT conda env (sentence-transformers)."""
import json, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
D = Path(__file__).resolve().parents[2] / "data/agentic"
docs = json.loads((D / "corpus.json").read_text())
m = SentenceTransformer("sentence-transformers/allenai-specter")
E = m.encode([d["title"] + "[SEP]" + d["abstract"] for d in docs], batch_size=32, normalize_embeddings=True, show_progress_bar=False)
np.save(D / "embeddings.npy", E); print(E.shape)
