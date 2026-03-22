"""
Hybrid retriever combining BM25 and vector search
"""
from rank_bm25 import BM25Okapi
from typing import Optional
import numpy as np
from dataclasses import dataclass

from .embeddings import EmbeddingModel


@dataclass
class Document:
    """Document with content and metadata"""
    id: str
    content: str
    url: str
    title: str
    score: float = 0.0


class HybridRetriever:
    """
    Hybrid retriever that combines:
    1. BM25 for lexical/keyword matching
    2. Vector similarity for semantic matching
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
    ):
        """
        Initialize hybrid retriever.

        Args:
            embedding_model: Model for generating embeddings
            bm25_weight: Weight for BM25 scores (0-1)
            vector_weight: Weight for vector similarity (0-1)
        """
        self.embedding_model = embedding_model or EmbeddingModel()
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

        # Document storage
        self.documents: list[Document] = []
        self.tokenized_docs: list[list[str]] = []
        self.doc_embeddings: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Okapi] = None

    def add_documents(self, documents: list[Document]):
        """
        Add documents to the retriever index.

        Args:
            documents: List of Document objects to index
        """
        self.documents.extend(documents)

        # Tokenize for BM25
        new_tokenized = [doc.content.lower().split() for doc in documents]
        self.tokenized_docs.extend(new_tokenized)
        self.bm25 = BM25Okapi(self.tokenized_docs)

        # Generate embeddings
        new_embeddings = self.embedding_model.embed_documents(
            [doc.content for doc in documents]
        )
        if self.doc_embeddings is None:
            self.doc_embeddings = new_embeddings
        else:
            self.doc_embeddings = np.vstack([self.doc_embeddings, new_embeddings])

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """
        Search for relevant documents using hybrid retrieval.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of Documents sorted by relevance
        """
        if not self.documents:
            return []

        # BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores = np.array(self.bm25.get_scores(tokenized_query))
        bm25_scores = self._normalize_scores(bm25_scores)

        # Vector similarity scores
        query_embedding = self.embedding_model.embed_query(query)
        vector_scores = np.dot(self.doc_embeddings, query_embedding)
        vector_scores = self._normalize_scores(vector_scores)

        # Combine scores
        combined_scores = (
            self.bm25_weight * bm25_scores + self.vector_weight * vector_scores
        )

        # Get top-k indices
        top_indices = np.argsort(combined_scores)[::-1][:top_k]

        # Return documents with scores
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            doc.score = float(combined_scores[idx])
            results.append(doc)

        return results

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to 0-1 range"""
        if scores.max() == scores.min():
            return np.zeros_like(scores)
        return (scores - scores.min()) / (scores.max() - scores.min())
