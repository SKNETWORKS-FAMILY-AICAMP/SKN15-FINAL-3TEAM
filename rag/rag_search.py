# rag_search.py
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
import pandas as pd

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "index" / "faiss.index"
IDMAP_PATH = ROOT / "index" / "id_map.npy"
CSV_PATH   = ROOT / "data" / "claim_text.csv"
MODEL_NAME = "intfloat/multilingual-e5-base"

class RAGSearcher:
    def __init__(self):
        print("[RAG] Loading index and model...")
        self.index = faiss.read_index(str(INDEX_PATH))
        self.id_map = np.load(IDMAP_PATH, allow_pickle=True).astype(str).tolist()
        self.df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
        self.model = SentenceTransformer(MODEL_NAME)
        self.doc_map = {
            row["prior_art_number"].strip(): row["claim"].strip()
            for _, row in self.df.iterrows() if str(row["prior_art_number"]).strip()
        }
        print("[RAG] Ready!")

    def _normalize(self, x):
        n = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
        return x / n

    def search(self, query: str, top_k: int = 5):
        """query(문장) 입력하면 top_k개 선행문헌 리턴"""
        qtext = f"query: {query.strip()}"
        emb = self.model.encode([qtext], normalize_embeddings=False).astype("float32")
        emb = self._normalize(emb)
        sims, idxs = self.index.search(emb, top_k)
        results = []
        for rank, (i, score) in enumerate(zip(idxs[0], sims[0]), start=1):
            pid = self.id_map[i]
            text = self.doc_map.get(pid, "")
            results.append({
                "rank": rank,
                "prior_id": pid,
                "similarity": float(score),
                "snippet": text[:200] + ("..." if len(text) > 200 else "")
            })
        return results
