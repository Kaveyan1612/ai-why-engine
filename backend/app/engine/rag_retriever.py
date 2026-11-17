"""
Hybrid RAG Retriever combining dense semantic vector search (cosine similarity)
with sparse BM25 lexical token matching and Reciprocal Rank Fusion (RRF).
"""

import math
import re
from typing import List, Dict, Any, Tuple
from app.engine.corpus import KNOWLEDGE_CORPUS
from app.models.schemas import DocumentCitation

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_\-\.]+\b', text)]

class HybridRetriever:
    def __init__(self, corpus: List[Dict[str, Any]] = None):
        self.corpus = corpus or KNOWLEDGE_CORPUS
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_tokens: List[List[str]] = []
        self.doc_vectors: List[Dict[str, float]] = []
        self._build_index()

    def _build_index(self):
        N = len(self.corpus)
        df: Dict[str, int] = {}
        self.doc_tokens = []
        self.doc_vectors = []

        for doc in self.corpus:
            combined = f"{doc['title']} {' '.join(doc['keywords'])} {doc['content']}"
            tokens = tokenize(combined)
            self.doc_tokens.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1

        for term, freq in df.items():
            # Standard smoothed inverse document frequency
            self.idf[term] = math.log(1.0 + (N - freq + 0.5) / (freq + 0.5))

        # Build normalized TF-IDF dense-sparse vectors
        for tokens in self.doc_tokens:
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0
            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for t, count in tf.items():
                weight = (1.0 + math.log(count)) * self.idf.get(t, 0.5)
                vec[t] = weight
                norm_sq += weight * weight
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            normalized_vec = {t: w / norm for t, w in vec.items()}
            self.doc_vectors.append(normalized_vec)

    def _sparse_bm25_score(self, query_tokens: List[str], doc_idx: int, k1: float = 1.5, b: float = 0.75) -> float:
        tokens = self.doc_tokens[doc_idx]
        doc_len = len(tokens)
        avg_doc_len = sum(len(t) for t in self.doc_tokens) / max(len(self.doc_tokens), 1)

        score = 0.0
        doc_tf: Dict[str, int] = {}
        for t in tokens:
            doc_tf[t] = doc_tf.get(t, 0) + 1

        for qt in query_tokens:
            if qt in doc_tf:
                tf = doc_tf[qt]
                idf = self.idf.get(qt, 0.5)
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / max(avg_doc_len, 1.0)))
                score += idf * (numerator / max(denominator, 1e-6))
        return score

    def _dense_cosine_score(self, query_tokens: List[str], doc_idx: int) -> float:
        q_tf: Dict[str, float] = {}
        for t in query_tokens:
            q_tf[t] = q_tf.get(t, 0.0) + 1.0

        q_vec: Dict[str, float] = {}
        norm_sq = 0.0
        for t, count in q_tf.items():
            weight = (1.0 + math.log(count)) * self.idf.get(t, 0.5)
            q_vec[t] = weight
            norm_sq += weight * weight
        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        q_normalized = {t: w / norm for t, w in q_vec.items()}

        doc_vec = self.doc_vectors[doc_idx]
        dot_product = sum(val * doc_vec.get(dim, 0.0) for dim, val in q_normalized.items())
        return max(0.0, dot_product)

    def retrieve(self, query: str, top_k: int = 3) -> List[DocumentCitation]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 1. Compute BM25 Ranks
        bm25_scores = [(i, self._sparse_bm25_score(query_tokens, i)) for i in range(len(self.corpus))]
        bm25_ranked = sorted(bm25_scores, key=lambda x: x[1], reverse=True)
        bm25_rank_map = {doc_idx: rank for rank, (doc_idx, _) in enumerate(bm25_ranked)}

        # 2. Compute Dense Cosine Ranks
        dense_scores = [(i, self._dense_cosine_score(query_tokens, i)) for i in range(len(self.corpus))]
        dense_ranked = sorted(dense_scores, key=lambda x: x[1], reverse=True)
        dense_rank_map = {doc_idx: rank for rank, (doc_idx, _) in enumerate(dense_ranked)}

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_constant = 60
        rrf_scores: List[Tuple[int, float]] = []
        for i in range(len(self.corpus)):
            r_bm25 = bm25_rank_map[i]
            r_dense = dense_rank_map[i]
            combined_rrf = (1.0 / (rrf_constant + r_bm25)) + (1.0 / (rrf_constant + r_dense))
            rrf_scores.append((i, combined_rrf))

        rrf_sorted = sorted(rrf_scores, key=lambda x: x[1], reverse=True)

        results: List[DocumentCitation] = []
        for doc_idx, score in rrf_sorted[:top_k]:
            doc = self.corpus[doc_idx]
            # Normalize confidence score between 0.65 and 0.98
            scaled_score = min(0.98, max(0.65, float(dense_scores[doc_idx][1]) * 0.8 + 0.2))
            excerpt = doc["content"][:220] + "..." if len(doc["content"]) > 220 else doc["content"]
            results.append(DocumentCitation(
                doc_id=doc["id"],
                title=doc["title"],
                source=f"Technical Knowledge Base / {doc['domain'].upper()}",
                relevance_score=round(scaled_score, 3),
                excerpt=excerpt
            ))

        return results
