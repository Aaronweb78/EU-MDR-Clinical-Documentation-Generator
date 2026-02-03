"""
Text embedding using sentence-transformers
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging
from config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class TextEmbedder:
    """Generate embeddings for text chunks"""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize embedder

        Args:
            model_name: Name of sentence-transformers model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 32,
                   show_progress: bool = False) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")

        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def embed_chunks(self, chunks: List[dict], show_progress: bool = True) -> List[dict]:
        """
        Generate embeddings for chunks with metadata

        Args:
            chunks: List of chunk dictionaries with 'text' field
            show_progress: Whether to show progress bar

        Returns:
            Chunks with 'embedding' field added
        """
        if not chunks:
            return []

        # Extract texts
        texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings
        embeddings = self.embed_batch(texts, show_progress=show_progress)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding

        return chunks

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model

        Returns:
            Embedding dimension
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")

        return self.model.get_sentence_embedding_dimension()

    def compute_similarity(self, embedding1: Union[List[float], np.ndarray],
                          embedding2: Union[List[float], np.ndarray]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays if needed
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)

        # Compute cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_most_similar(self, query_embedding: List[float],
                         candidate_embeddings: List[List[float]],
                         top_k: int = 5) -> List[tuple]:
        """
        Find most similar embeddings to query

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = []

        for i, candidate in enumerate(candidate_embeddings):
            sim = self.compute_similarity(query_embedding, candidate)
            similarities.append((i, sim))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        (Alias for embed_text for clarity in search contexts)

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        return self.embed_text(query)

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate that embedding is valid

        Args:
            embedding: Embedding vector to validate

        Returns:
            True if valid, False otherwise
        """
        if not embedding:
            return False

        if not isinstance(embedding, (list, np.ndarray)):
            return False

        # Check dimension matches
        expected_dim = self.get_embedding_dimension()
        if len(embedding) != expected_dim:
            return False

        # Check for NaN or Inf values
        if isinstance(embedding, list):
            embedding = np.array(embedding)

        if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
            return False

        return True
