"""
ChromaDB vector store for document chunks
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from pathlib import Path
from config import CHROMA_DB_DIR

logger = logging.getLogger(__name__)


class VectorStore:
    """Manage vector storage with ChromaDB"""

    def __init__(self, persist_directory: Path = CHROMA_DB_DIR):
        """
        Initialize vector store

        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collections = {}
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client"""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise

    def get_or_create_collection(self, project_id: str):
        """
        Get or create a collection for a project

        Args:
            project_id: Project identifier

        Returns:
            ChromaDB collection
        """
        if project_id in self.collections:
            return self.collections[project_id]

        try:
            collection = self.client.get_or_create_collection(
                name=f"project_{project_id}",
                metadata={"project_id": project_id}
            )
            self.collections[project_id] = collection
            logger.info(f"Collection created/retrieved for project {project_id}")
            return collection

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def add_chunks(self, project_id: str, chunks: List[Dict]):
        """
        Add document chunks to vector store

        Args:
            project_id: Project identifier
            chunks: List of chunk dictionaries with text, embedding, and metadata
        """
        if not chunks:
            logger.warning("No chunks to add")
            return

        collection = self.get_or_create_collection(project_id)

        try:
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                # Generate unique ID
                chunk_id = chunk.get('id', f"{chunk.get('file_id', 'unknown')}_{i}")
                ids.append(chunk_id)

                # Get embedding
                embeddings.append(chunk['embedding'])

                # Get document text
                documents.append(chunk['text'])

                # Prepare metadata (ChromaDB only supports simple types)
                metadata = chunk.get('metadata', {})
                # Ensure all metadata values are strings, numbers, or booleans
                clean_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = str(value)

                metadatas.append(clean_metadata)

            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"Added {len(chunks)} chunks to collection {project_id}")

        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise

    def query(self, project_id: str, query_embedding: List[float],
             n_results: int = 10, filter_dict: Optional[Dict] = None) -> Dict:
        """
        Query vector store for similar chunks

        Args:
            project_id: Project identifier
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            Query results with ids, documents, metadatas, and distances
        """
        collection = self.get_or_create_collection(project_id)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict if filter_dict else None
            )

            return results

        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return {
                'ids': [[]],
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }

    def query_by_text(self, project_id: str, query_text: str,
                     embedder, n_results: int = 10,
                     filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Query using text (will generate embedding)

        Args:
            project_id: Project identifier
            query_text: Query text
            embedder: Text embedder instance
            n_results: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            List of result dictionaries
        """
        # Generate embedding for query
        query_embedding = embedder.embed_text(query_text)

        # Query vector store
        results = self.query(project_id, query_embedding, n_results, filter_dict)

        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })

        return formatted_results

    def delete_collection(self, project_id: str):
        """
        Delete a project's collection

        Args:
            project_id: Project identifier
        """
        try:
            self.client.delete_collection(f"project_{project_id}")
            if project_id in self.collections:
                del self.collections[project_id]
            logger.info(f"Deleted collection for project {project_id}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")

    def get_collection_count(self, project_id: str) -> int:
        """
        Get number of chunks in collection

        Args:
            project_id: Project identifier

        Returns:
            Number of chunks
        """
        try:
            collection = self.get_or_create_collection(project_id)
            return collection.count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0

    def update_chunk(self, project_id: str, chunk_id: str,
                    text: str = None, embedding: List[float] = None,
                    metadata: Dict = None):
        """
        Update a chunk in the vector store

        Args:
            project_id: Project identifier
            chunk_id: Chunk identifier
            text: New text (optional)
            embedding: New embedding (optional)
            metadata: New metadata (optional)
        """
        collection = self.get_or_create_collection(project_id)

        try:
            update_data = {'ids': [chunk_id]}

            if text is not None:
                update_data['documents'] = [text]
            if embedding is not None:
                update_data['embeddings'] = [embedding]
            if metadata is not None:
                update_data['metadatas'] = [metadata]

            collection.update(**update_data)
            logger.info(f"Updated chunk {chunk_id} in project {project_id}")

        except Exception as e:
            logger.error(f"Error updating chunk: {e}")
            raise

    def delete_chunks(self, project_id: str, chunk_ids: List[str]):
        """
        Delete specific chunks

        Args:
            project_id: Project identifier
            chunk_ids: List of chunk IDs to delete
        """
        collection = self.get_or_create_collection(project_id)

        try:
            collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks from project {project_id}")
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")

    def get_chunk(self, project_id: str, chunk_id: str) -> Optional[Dict]:
        """
        Get a specific chunk by ID

        Args:
            project_id: Project identifier
            chunk_id: Chunk identifier

        Returns:
            Chunk data or None
        """
        collection = self.get_or_create_collection(project_id)

        try:
            result = collection.get(ids=[chunk_id])

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0],
                    'embedding': result['embeddings'][0] if result.get('embeddings') else None
                }
            return None

        except Exception as e:
            logger.error(f"Error getting chunk: {e}")
            return None

    def list_collections(self) -> List[str]:
        """
        List all collections

        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    def reset(self):
        """Reset the entire database (use with caution!)"""
        try:
            self.client.reset()
            self.collections = {}
            logger.warning("ChromaDB has been reset")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
