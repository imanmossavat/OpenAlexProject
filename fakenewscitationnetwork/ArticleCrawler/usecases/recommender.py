# Linear contextual bandit + LinUCB
# Embeds paper text + future metadata
# Loads papers from crawler and caches embeddings
# Stores feedback and maintains A matrix with efficient Cholesky updates
# Scores papers using cosine similarity + UCB
# Interactive CLI for feedback collection
# Orchestrates modules and runs recommendation loop

import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.linalg import cho_factor, cho_solve
import os
from datetime import datetime
import pickle


class PaperRecommender:
    def __init__(self, crawler, lambda_reg=1.0, ucb_weight=0.1, UseSeed= True):
        df = crawler.data_manager.frames.df_paper_metadata[['title', 'paperId', 'isSeed']]
        self.embedding_model = RecommenderEmbeddingModel()
        self.db = PaperDatabase(df, self.embedding_model)
        self.feedback = FeedbackStore(dim=self.embedding_model.dim, lambda_reg=lambda_reg)

        if UseSeed:        # Add seed feedback here
            df_seed = df[df['isSeed']==True]
            for _, row in df_seed.iterrows():
                idx = self.db.df.index.get_loc(row.name)
                emb = self.db.embeddings[idx]
                self.feedback.add_feedback(emb, label=1)

        self.scorer = PaperScorer(self.feedback, ucb_weight=ucb_weight)
        self.cli = RecommenderCLI(self.db, self.scorer, self.feedback)

    def run(self, topk=5):
        self.cli.loop(topk=topk)
    
    def save(self, path=None):
        os.makedirs(os.path.dirname(path or "."), exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = path or f"recommender_session_{timestamp}.pkl"

        save_data = {
            'A': self.fb.A,
            'b': self.fb.b,
            'feedback_count': self.fb._feedback_count,
            'model_dim': self.model.dim,
        }

        with open(save_path, 'wb') as f:
            pickle.dump(save_data, f)

        print(f"Saved recommender state to: {save_path}")


# === RecommenderEmbeddingModel ===
class RecommenderEmbeddingModel:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True)

    def encode_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, normalize_embeddings=True)

    def encode_paper(self, title: str, **kwargs) -> np.ndarray:
        return self.encode_text(title)  # Easily extend later with venue, year, etc.


# === PaperDatabase ===
class PaperDatabase:
    def __init__(self, df, embedding_model):
        self.df = df
        self.embedding_model = embedding_model
        self.papers = []
        self.embeddings = []
        self._prepare()

    def _prepare(self):
        titles = self.df['title'].tolist()
        self.papers = [{'paperId': pid, 'title': title} for pid, title in zip(self.df['paperId'], titles)]
        self.embeddings = self.embedding_model.encode_batch(titles)


    def get_all(self):
        return self.papers, self.embeddings


# === FeedbackStore ===
class FeedbackStore:
    def __init__(self, dim, lambda_reg=1.0, update_every=10):
        self.dim = dim
        self.lambda_reg = lambda_reg
        self.A = lambda_reg * np.eye(dim)
        self.b = np.zeros(dim)
        self._feedback_count = 0
        self._cho = None
        self._dirty = True
        self._update_every = update_every
        self.explored = set()  # <-- add this to track explored embeddings


    def add_feedback(self, x: np.ndarray, label: int):
        self.A += np.outer(x, x)
        self.b += label * x
        self._feedback_count += 1
        if self._feedback_count % self._update_every == 0:
            self._dirty = True

        self.explored.add(tuple(x))


    def _update_cholesky(self):
        if self._dirty or self._cho is None:
            self._cho = cho_factor(self.A, lower=True)
            self._dirty = False

    def get_query(self) -> np.ndarray:
        self._update_cholesky()
        return cho_solve(self._cho, self.b)

    def mahalanobis(self, x: np.ndarray) -> float:
        self._update_cholesky()
        z = cho_solve(self._cho, x)
        return np.dot(x, z)


# === PaperScorer ===
class PaperScorer:
    def __init__(self, feedback_store, ucb_weight=0.1):
        self.fb = feedback_store
        self.alpha = ucb_weight

    def score_batch(self, X: np.ndarray) -> np.ndarray:
        w = self.fb.get_query()
        if np.linalg.norm(w) == 0:
            return np.zeros(len(X))  # no feedback yet

        sims = X @ w
        if self.alpha > 0:
            exploration = np.array([self.fb.mahalanobis(x) for x in X])
            scores = sims + self.alpha * np.sqrt(exploration)
        else:
            scores = sims
        
        # === Mask explored items ===
        explored_mask = np.array([tuple(x) in self.fb.explored for x in X])
        scores[explored_mask] = -np.inf
        return scores


# === RecommenderCLI ===
class RecommenderCLI:
    def __init__(self, db, scorer, fb):
        self.db = db
        self.scorer = scorer
        self.fb = fb

    def loop(self, topk=5):
        print("Welcome to the paper recommender!")
        print("For each paper shown, please type:\n"
            "  y - if relevant\n"
            "  n - if not relevant\n"
            "  skip - to skip\n"
            "  q - to quit\n")

        while True:
            papers, X = self.db.get_all()
            scores = self.scorer.score_batch(X)
            top_idx = scores.argsort()[::-1][:topk]

            for idx in top_idx:
                paper = papers[idx]
                print(f"\nTitle: {paper['title']}")
                ans = input("Relevant? (y/n/q, anything else = skip): ").strip().lower()
                if ans == 'y':
                    self.fb.add_feedback(X[idx], label=1)
                elif ans == 'n':
                    self.fb.add_feedback(X[idx], label=-1)
                elif ans == 'q':
                    print("Exiting...")
                    return
                else:
                    self.fb.add_feedback(X[idx], label=0)  # if you want zero feedback

                # skip just continues the loop silently
            print("\n--- Next batch ---")
