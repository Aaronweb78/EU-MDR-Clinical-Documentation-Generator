"""
PDF text extraction using PyMuPDF
"""
import pymupdf as fitz
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files"""

    @staticmethod
    def extract_text(file_path: Path) -> Optional[str]:
        """
        Extract all text from PDF file

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            doc = fitz.open(str(file_path))
            text_content = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")

            doc.close()

            full_text = "\n\n".join(text_content)
            return full_text if full_text.strip() else None

        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return None

    @staticmethod
    def extract_metadata(file_path: Path) -> Dict:
        """
        Extract PDF metadata

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary of metadata
        """
        try:
            doc = fitz.open(str(file_path))
            metadata = doc.metadata
            page_count = len(doc)
            doc.close()

            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'page_count': page_count
            }

        except Exception as e:
            logger.error(f"Error extracting PDF metadata {file_path}: {e}")
            return {}

    @staticmethod
    def extract_by_page(file_path: Path) -> List[Dict]:
        """
        Extract text page by page

        Args:
            file_path: Path to PDF file

        Returns:
            List of dictionaries with page number and text
        """
        try:
            doc = fitz.open(str(file_path))
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                pages.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'char_count': len(text)
                })

            doc.close()
            return pages

        except Exception as e:
            logger.error(f"Error extracting PDF pages {file_path}: {e}")
            return []

    @staticmethod
    def has_text(file_path: Path) -> bool:
        """
        Check if PDF has extractable text

        Args:
            file_path: Path to PDF file

        Returns:
            True if PDF has text, False otherwise
        """
        try:
            doc = fitz.open(str(file_path))
            has_text_content = False

            # Check first 3 pages
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                text = page.get_text().strip()
                if text:
                    has_text_content = True
                    break

            doc.close()
            return has_text_content

        except Exception as e:
            logger.error(f"Error checking PDF text {file_path}: {e}")
            return False

    @staticmethod
    def get_page_count(file_path: Path) -> int:
        """
        Get number of pages in PDF

        Args:
            file_path: Path to PDF file

        Returns:
            Number of pages
        """
        try:
            doc = fitz.open(str(file_path))
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Error getting PDF page count {file_path}: {e}")
            return 0
