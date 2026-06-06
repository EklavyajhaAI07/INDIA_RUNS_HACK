"""
Hybrid Retrieval — BM25 + Embedding-based candidate search.

This module combines two retrieval strategies:
1. BM25: Fast keyword matching for exact skill/term matches
2. Sentence-Transformers: Semantic search for conceptual similarity

Think of it as: "Find the 1000 most relevant candidates from 100,000."

Compute constraints:
- Pre-computed embeddings (allowed as pre_computation)
- BM25 index built at load time
- FAISS for fast vector search
"""

import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import pickle
import json


class HybridRetriever:
    """
    Combines BM25 and semantic search for candidate retrieval.

    Usage:
        retriever = HybridRetriever()
        retriever.build_index(candidates)
        results = retriever.retrieve(jd_text, top_k=1000)
    """

    def __init__(self):
        self.candidates = []
        self.bm25 = None
        self.faiss_index = None
        self.embeddings = None
        self.model = None
        self.candidate_texts = []
        self.candidate_ids = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        import re
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        tokens = text.split()
        # Remove very short tokens
        tokens = [t for t in tokens if len(t) > 1]
        return tokens

    def build_bm25_index(self, candidates):
        """Build BM25 index from candidate search texts."""
        from rank_bm25 import BM25Okapi

        print("Building BM25 index...")
        self.candidates = candidates
        self.candidate_ids = [c.candidate_id for c in candidates]
        self.candidate_texts = [c.search_text for c in candidates]

        # Tokenize all texts
        tokenized = [self._tokenize(text) for text in self.candidate_texts]

        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized)
        print(f"BM25 index built with {len(candidates)} documents")

    def build_embedding_index(self, candidates, model_name: str = "all-MiniLM-L6-v2"):
        """
        Build FAISS index from candidate embeddings.

        This is the pre-computation step (allowed by competition rules).
        """
        import faiss
        from sentence_transformers import SentenceTransformer

        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        print("Encoding candidate texts (this may take a while for 100K candidates)...")
        texts = [c.search_text for c in candidates]

        # Encode in batches to manage memory
        batch_size = 1000
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
            if (i // batch_size) % 10 == 0:
                print(f"  Encoded {min(i + batch_size, len(texts))}/{len(texts)} candidates")

        self.embeddings = np.vstack(all_embeddings).astype('float32')

        # Build FAISS index
        dimension = self.embeddings.shape[1]
        print(f"Building FAISS index (dimension={dimension})...")

        # Use IVF index for faster search on large datasets
        if len(candidates) > 10000:
            nlist = min(100, len(candidates) // 10)
            quantizer = faiss.IndexFlatL2(dimension)
            self.faiss_index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            self.faiss_index.train(self.embeddings)
            self.faiss_index.add(self.embeddings)
        else:
            self.faiss_index = faiss.IndexFlatL2(dimension)
            self.faiss_index.add(self.embeddings)

        print(f"FAISS index built with {len(candidates)} vectors")

    def bm25_search(self, query: str, top_k: int = 1000) -> List[Tuple[str, float]]:
        """Search using BM25 and return (candidate_id, score) pairs."""
        if self.bm25 is None:
            raise ValueError("BM25 index not built. Call build_bm25_index first.")

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.candidate_ids[idx], float(scores[idx])))

        return results

    def semantic_search(self, query: str, top_k: int = 1000) -> List[Tuple[str, float]]:
        """Search using embeddings and return (candidate_id, score) pairs."""
        if self.faiss_index is None or self.model is None:
            raise ValueError("Embedding index not built. Call build_embedding_index first.")

        # Encode query
        query_embedding = self.model.encode([query]).astype('float32')

        # Search FAISS
        distances, indices = self.faiss_index.search(query_embedding, min(top_k, len(self.candidates)))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:  # Valid index
                # Convert distance to similarity score (higher is better)
                score = 1.0 / (1.0 + dist)
                results.append((self.candidate_ids[idx], float(score)))

        return results

    def hybrid_search(self, query: str, top_k: int = 1000,
                      bm25_weight: float = 0.4, semantic_weight: float = 0.6) -> List[Tuple[str, float, dict]]:
        """
        Combine BM25 and semantic search results.

        Returns list of (candidate_id, combined_score, evidence_dict)
        """
        # Get results from both methods
        bm25_results = self.bm25_search(query, top_k=top_k * 2)
        semantic_results = self.semantic_search(query, top_k=top_k * 2)

        # Normalize scores
        bm25_scores = {cid: score for cid, score in bm25_results}
        semantic_scores = {cid: score for cid, score in semantic_results}

        # Normalize each to [0, 1]
        if bm25_scores:
            max_bm25 = max(bm25_scores.values())
            if max_bm25 > 0:
                bm25_scores = {k: v / max_bm25 for k, v in bm25_scores.items()}

        if semantic_scores:
            max_sem = max(semantic_scores.values())
            if max_sem > 0:
                semantic_scores = {k: v / max_sem for k, v in semantic_scores.items()}

        # Combine scores
        all_candidates = set(bm25_scores.keys()) | set(semantic_scores.keys())
        combined = {}

        for cid in all_candidates:
            bm25_score = bm25_scores.get(cid, 0.0)
            sem_score = semantic_scores.get(cid, 0.0)
            combined_score = (bm25_weight * bm25_score) + (semantic_weight * sem_score)

            combined[cid] = {
                "combined_score": combined_score,
                "bm25_score": bm25_score,
                "semantic_score": sem_score,
                "in_bm25": cid in bm25_scores,
                "in_semantic": cid in semantic_scores,
            }

        # Sort by combined score
        sorted_candidates = sorted(
            combined.items(),
            key=lambda x: x[1]["combined_score"],
            reverse=True
        )[:top_k]

        return [(cid, data["combined_score"], data) for cid, data in sorted_candidates]

    def retrieve(self, jd_text: str, top_k: int = 1000) -> List[Tuple[str, float, dict]]:
        """
        Main entry point: Retrieve top candidates for a job description.

        Args:
            jd_text: The job description text (or combined search query)
            top_k: Number of candidates to retrieve

        Returns:
            List of (candidate_id, score, evidence_dict)
        """
        return self.hybrid_search(jd_text, top_k=top_k)

    def save_index(self, path: str):
        """Save the built indexes to disk."""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save BM25 data
        with open(save_path / "bm25_data.pkl", "wb") as f:
            pickle.dump({
                "candidates": self.candidates,
                "candidate_ids": self.candidate_ids,
                "candidate_texts": self.candidate_texts,
            }, f)

        # Save FAISS index
        if self.faiss_index is not None:
            import faiss
            faiss.write_index(self.faiss_index, str(save_path / "faiss.index"))

        # Save embeddings
        if self.embeddings is not None:
            np.save(str(save_path / "embeddings.npy"), self.embeddings)

        print(f"Index saved to {save_path}")

    def load_index(self, path: str):
        """Load pre-built indexes from disk."""
        load_path = Path(path)

        # Load BM25 data
        with open(load_path / "bm25_data.pkl", "rb") as f:
            data = pickle.load(f)
            self.candidates = data["candidates"]
            self.candidate_ids = data["candidate_ids"]
            self.candidate_texts = data["candidate_texts"]

        # Rebuild BM25 index
        from rank_bm25 import BM25Okapi
        tokenized = [self._tokenize(text) for text in self.candidate_texts]
        self.bm25 = BM25Okapi(tokenized)

        # Load FAISS index
        if (load_path / "faiss.index").exists():
            import faiss
            self.faiss_index = faiss.read_index(str(load_path / "faiss.index"))

        # Load embeddings
        if (load_path / "embeddings.npy").exists():
            self.embeddings = np.load(str(load_path / "embeddings.npy"))

        print(f"Index loaded from {load_path}")
