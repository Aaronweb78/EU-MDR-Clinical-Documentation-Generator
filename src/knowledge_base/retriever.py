"""
High-level retrieval interface for RAG
"""
from typing import List, Dict, Optional
import logging
from .vector_store import VectorStore
from ..ingestion.embedder import TextEmbedder
from config import MAX_CHUNKS_FOR_CONTEXT

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieve relevant context for report generation"""

    def __init__(self, vector_store: VectorStore, embedder: TextEmbedder):
        """
        Initialize retriever

        Args:
            vector_store: VectorStore instance
            embedder: TextEmbedder instance
        """
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, project_id: str, query: str,
                n_results: int = MAX_CHUNKS_FOR_CONTEXT,
                categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Retrieve relevant chunks for a query

        Args:
            project_id: Project identifier
            query: Query text
            n_results: Number of results to return
            categories: Optional list of document categories to filter by

        Returns:
            List of relevant chunks with text and metadata
        """
        try:
            # Build filter if categories specified
            filter_dict = None
            if categories:
                filter_dict = {"category": {"$in": categories}}

            # Query vector store
            results = self.vector_store.query_by_text(
                project_id=project_id,
                query_text=query,
                embedder=self.embedder,
                n_results=n_results,
                filter_dict=filter_dict
            )

            return results

        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []

    def retrieve_by_file(self, project_id: str, file_id: str,
                        query: str, n_results: int = 5) -> List[Dict]:
        """
        Retrieve chunks from a specific file

        Args:
            project_id: Project identifier
            file_id: File identifier
            query: Query text
            n_results: Number of results

        Returns:
            List of relevant chunks from the file
        """
        try:
            filter_dict = {"file_id": file_id}

            results = self.vector_store.query_by_text(
                project_id=project_id,
                query_text=query,
                embedder=self.embedder,
                n_results=n_results,
                filter_dict=filter_dict
            )

            return results

        except Exception as e:
            logger.error(f"Error retrieving chunks by file: {e}")
            return []

    def retrieve_by_category(self, project_id: str, category: str,
                           query: str, n_results: int = MAX_CHUNKS_FOR_CONTEXT) -> List[Dict]:
        """
        Retrieve chunks from a specific document category

        Args:
            project_id: Project identifier
            category: Document category
            query: Query text
            n_results: Number of results

        Returns:
            List of relevant chunks from the category
        """
        return self.retrieve(project_id, query, n_results, categories=[category])

    def retrieve_multi_query(self, project_id: str, queries: List[str],
                           n_results_per_query: int = 5) -> List[Dict]:
        """
        Retrieve using multiple queries and merge results

        Args:
            project_id: Project identifier
            queries: List of query texts
            n_results_per_query: Results per query

        Returns:
            Merged list of unique chunks
        """
        all_results = []
        seen_ids = set()

        for query in queries:
            results = self.retrieve(project_id, query, n_results_per_query)

            for result in results:
                if result['id'] not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result['id'])

        # Sort by average distance (lower is better)
        return all_results

    def retrieve_with_reranking(self, project_id: str, query: str,
                               initial_k: int = 20,
                               final_k: int = MAX_CHUNKS_FOR_CONTEXT) -> List[Dict]:
        """
        Retrieve and rerank results for better relevance

        Args:
            project_id: Project identifier
            query: Query text
            initial_k: Initial number of results to retrieve
            final_k: Final number of results after reranking

        Returns:
            Reranked list of chunks
        """
        # Retrieve more results initially
        results = self.retrieve(project_id, query, n_results=initial_k)

        if len(results) <= final_k:
            return results

        # Simple reranking based on text similarity
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        # Score each result
        scored_results = []
        for result in results:
            text_lower = result['text'].lower()
            text_terms = set(text_lower.split())

            # Calculate term overlap
            overlap = len(query_terms.intersection(text_terms))
            overlap_score = overlap / len(query_terms) if query_terms else 0

            # Combine with distance (lower distance is better)
            distance = result.get('distance', 1.0)
            final_score = overlap_score * 0.3 + (1 - distance) * 0.7

            scored_results.append((result, final_score))

        # Sort by score (higher is better)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return [result for result, score in scored_results[:final_k]]

    def retrieve_for_section(self, project_id: str, section_name: str,
                           section_query: str,
                           preferred_categories: List[str] = None,
                           n_results: int = MAX_CHUNKS_FOR_CONTEXT) -> Dict:
        """
        Retrieve context optimized for a specific report section

        Args:
            project_id: Project identifier
            section_name: Name of the section
            section_query: Query for this section
            preferred_categories: Categories most relevant to this section
            n_results: Number of results

        Returns:
            Dictionary with chunks and metadata
        """
        # Retrieve with category preference
        results = self.retrieve(
            project_id=project_id,
            query=section_query,
            n_results=n_results,
            categories=preferred_categories
        )

        # Group by source file
        by_file = {}
        for result in results:
            file_id = result['metadata'].get('file_id', 'unknown')
            if file_id not in by_file:
                by_file[file_id] = []
            by_file[file_id].append(result)

        return {
            'section': section_name,
            'chunks': results,
            'by_file': by_file,
            'source_files': list(by_file.keys()),
            'total_chunks': len(results)
        }

    def build_context_string(self, chunks: List[Dict],
                           max_length: int = 5000,
                           include_metadata: bool = True) -> str:
        """
        Build context string from chunks for LLM prompt

        Args:
            chunks: List of chunk dictionaries
            max_length: Maximum length of context string
            include_metadata: Whether to include metadata headers

        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0

        for i, chunk in enumerate(chunks):
            # Build chunk text with optional metadata
            if include_metadata:
                metadata = chunk.get('metadata', {})
                filename = metadata.get('filename', 'Unknown')
                category = metadata.get('category', 'unknown')
                header = f"[Source {i+1}: {filename} ({category})]\n"
                chunk_text = header + chunk['text'] + "\n\n"
            else:
                chunk_text = chunk['text'] + "\n\n"

            # Check length
            if current_length + len(chunk_text) > max_length:
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)

        return "".join(context_parts)

    def get_retrieval_stats(self, project_id: str) -> Dict:
        """
        Get statistics about the vector store for a project

        Args:
            project_id: Project identifier

        Returns:
            Dictionary of statistics
        """
        try:
            count = self.vector_store.get_collection_count(project_id)

            return {
                'total_chunks': count,
                'collection_exists': count > 0
            }

        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {
                'total_chunks': 0,
                'collection_exists': False
            }

    def test_retrieval(self, project_id: str, test_query: str = "device") -> Dict:
        """
        Test retrieval functionality

        Args:
            project_id: Project identifier
            test_query: Query to test with

        Returns:
            Test results
        """
        try:
            results = self.retrieve(project_id, test_query, n_results=3)

            return {
                'success': True,
                'results_count': len(results),
                'sample_results': results[:2] if results else []
            }

        except Exception as e:
            logger.error(f"Error testing retrieval: {e}")
            return {
                'success': False,
                'error': str(e)
            }
