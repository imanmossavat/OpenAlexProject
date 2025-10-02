import os
import logging
import pickle
import time
import numpy as np
import torch

from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class TitleSimilarityEngine:
    def __init__(self, model_name = 'all-MiniLM-L6-v2', device = None, crawler= None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = SentenceTransformer(model_name, device=self.device)
        
        if crawler:
            self.titles = crawler.data_manager.frames.df_paper_metadata['title'].tolist()
            self.source_pickle_path= crawler.storage_and_logging_options.folders_all['pkl_folder'] / 'perm'
        else:
            self.embeddings = None
            self.titles = None
            self.source_pickle_path = None

    def load_crawler(self, file_path: str):
        with open(file_path, "rb") as f:
            crawler = pickle.load(f)
        self.titles = crawler.data_manager.frames.df_paper_metadata['title'].tolist()
        self.source_pickle_path = file_path
        logging.info(f"Crawler loaded with {len(self.titles)} titles from: {file_path}")

    def compute_embeddings(self):
        if not self.titles:
            raise ValueError("Titles are not loaded.")
        start_time = time.time()
        self.embeddings = self.model.encode(self.titles, show_progress_bar=True, convert_to_numpy=True)
        elapsed = time.time() - start_time
        logging.info(f"Embeddings computed in {elapsed:.2f} seconds")

    def find_similar_titles(self, query: str, top_k: int = 5):
        if self.embeddings is None or self.titles is None:
            raise ValueError("Embeddings or titles not available. Run `compute_embeddings()` first.")

        query_embedding = self.model.encode(query, convert_to_numpy=True)
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        print(f"\n🔍 Query: {query}\n")
        print("📚 Top most similar titles:")
        for idx in top_indices:
            print(f"- ({similarities[idx]:.4f}) {self.titles[idx]}")

    def save(self, save_path: str):
        if self.embeddings is None or self.titles is None:
            raise ValueError("Nothing to save. Ensure embeddings and titles are set.")

        data = {
            'embeddings': self.embeddings,
            'titles': self.titles,
            'source_pickle_path': self.source_pickle_path
        }
        with open(save_path, 'wb') as f:
            pickle.dump(data, f)
        logging.info(f"Embedding data saved to: {save_path}")

    def load(self, load_path: str):
        with open(load_path, 'rb') as f:
            data = pickle.load(f)
        self.embeddings = data['embeddings']
        self.titles = data['titles']
        self.source_pickle_path = data['source_pickle_path']
        logging.info(f"Embedding data loaded from: {load_path}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # === CONFIGURATION ===
    pickle_path = r'C:\Users\imanm\OneDrive - Office 365 Fontys\Documenten\myCode\fakenews\refactor\Experiments\data\crawler_experiments\chess_post_rw\pkl\perm\chess_post_rw_20250416221521.pkl'
    query = "evolution of behavioral tendencies"
    save_path = os.path.join(os.path.dirname(pickle_path), 'title_embeddings_bundle.pkl')

    # === EXECUTION ===
    engine = TitleSimilarityEngine() # alternatively, if you have a crawler object, you can feed it into this class. 
    engine.load_crawler(pickle_path) # 
    engine.compute_embeddings()
    engine.find_similar_titles(query)
    engine.save(save_path)
