"""
Embedding model for vector search
"""
from sentence_transformers import SentenceTransformer
from typing import Union
import numpy as np


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model"""

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model name for embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, text: Union[str, list[str]]) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            text: Single string or list of strings

        Returns:
            Numpy array of embeddings
        """
        if isinstance(text, str):
            text = [text]
        return self.model.encode(text, normalize_embeddings=True)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string"""
        return self.embed(query)[0]

    def embed_documents(self, documents: list[str]) -> np.ndarray:
        """Embed multiple documents"""
        return self.embed(documents)
