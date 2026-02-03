"""
Text chunking for vector embeddings
"""
from typing import List, Dict
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from config import CHUNK_SIZE, CHUNK_OVERLAP


class TextChunker:
    """Split text into chunks for embedding"""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize chunker

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,  # Rough char to token conversion
            chunk_overlap=chunk_overlap * 4,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks with metadata

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text:
            return []

        # Split text
        text_chunks = self.splitter.split_text(text)

        # Create chunk objects with metadata
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = {
                'text': chunk_text,
                'chunk_index': i,
                'char_count': len(chunk_text),
                'word_count': len(chunk_text.split())
            }

            # Add custom metadata
            if metadata:
                chunk['metadata'] = metadata.copy()
                chunk['metadata']['chunk_index'] = i

            chunks.append(chunk)

        return chunks

    def chunk_by_sentences(self, text: str, max_sentences: int = 10) -> List[str]:
        """
        Chunk text by sentences

        Args:
            text: Text to chunk
            max_sentences: Maximum sentences per chunk

        Returns:
            List of text chunks
        """
        import re

        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []

        for sentence in sentences:
            current_chunk.append(sentence)

            if len(current_chunk) >= max_sentences:
                chunks.append(' '.join(current_chunk))
                current_chunk = []

        # Add remaining sentences
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def chunk_by_paragraphs(self, text: str, max_paragraphs: int = 5) -> List[str]:
        """
        Chunk text by paragraphs

        Args:
            text: Text to chunk
            max_paragraphs: Maximum paragraphs per chunk

        Returns:
            List of text chunks
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []

        for para in paragraphs:
            if not para.strip():
                continue

            current_chunk.append(para)

            if len(current_chunk) >= max_paragraphs:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []

        # Add remaining paragraphs
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def chunk_with_context(self, text: str, file_id: str,
                          filename: str, category: str = None) -> List[Dict]:
        """
        Chunk text with rich metadata context

        Args:
            text: Text to chunk
            file_id: File identifier
            filename: Original filename
            category: Document category

        Returns:
            List of chunks with metadata
        """
        metadata = {
            'file_id': file_id,
            'filename': filename,
            'category': category
        }

        return self.chunk_text(text, metadata)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except:
            # Fallback: rough estimate
            return int(len(text.split()) * 1.3)

    def get_optimal_chunk_count(self, text: str) -> int:
        """
        Calculate optimal number of chunks for text

        Args:
            text: Text to analyze

        Returns:
            Estimated number of chunks
        """
        token_count = self.count_tokens(text)
        return max(1, (token_count // self.chunk_size) + 1)

    def validate_chunks(self, chunks: List[Dict]) -> Dict:
        """
        Validate chunk quality

        Args:
            chunks: List of chunks to validate

        Returns:
            Validation statistics
        """
        if not chunks:
            return {
                'valid': False,
                'error': 'No chunks provided'
            }

        total_tokens = 0
        oversized_chunks = 0
        undersized_chunks = 0

        for chunk in chunks:
            token_count = self.count_tokens(chunk['text'])
            total_tokens += token_count

            if token_count > self.chunk_size * 1.5:
                oversized_chunks += 1
            elif token_count < self.chunk_size * 0.3:
                undersized_chunks += 1

        return {
            'valid': True,
            'chunk_count': len(chunks),
            'total_tokens': total_tokens,
            'avg_tokens_per_chunk': total_tokens / len(chunks),
            'oversized_chunks': oversized_chunks,
            'undersized_chunks': undersized_chunks
        }

    def merge_small_chunks(self, chunks: List[str], min_size: int = 100) -> List[str]:
        """
        Merge chunks that are too small

        Args:
            chunks: List of text chunks
            min_size: Minimum chunk size in characters

        Returns:
            List of merged chunks
        """
        if not chunks:
            return []

        merged = []
        current = ""

        for chunk in chunks:
            if len(current) < min_size:
                current += " " + chunk if current else chunk
            else:
                merged.append(current)
                current = chunk

        if current:
            merged.append(current)

        return merged
