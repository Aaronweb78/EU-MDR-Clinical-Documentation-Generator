"""
Main file processor that orchestrates extraction, chunking, and embedding
"""
from pathlib import Path
from typing import Optional, Dict, List
import logging

from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .xlsx_extractor import XLSXExtractor
from ..utils.file_utils import get_file_type, read_text_file
from ..utils.text_utils import clean_text

logger = logging.getLogger(__name__)


class FileProcessor:
    """Process files and extract text"""

    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.docx_extractor = DOCXExtractor()
        self.xlsx_extractor = XLSXExtractor()

    def process_file(self, file_path: Path) -> Optional[str]:
        """
        Process file and extract text based on file type

        Args:
            file_path: Path to file

        Returns:
            Extracted and cleaned text, or None if extraction fails
        """
        file_type = get_file_type(str(file_path))

        if not file_type:
            logger.warning(f"Unsupported file type: {file_path}")
            return None

        try:
            # Extract text based on file type
            if file_type == 'pdf':
                text = self.pdf_extractor.extract_text(file_path)
            elif file_type == 'docx':
                text = self.docx_extractor.extract_text(file_path)
            elif file_type == 'xlsx':
                text = self.xlsx_extractor.extract_text(file_path)
            elif file_type == 'txt':
                text = read_text_file(file_path)
            else:
                logger.warning(f"Unknown file type: {file_type}")
                return None

            if not text:
                logger.warning(f"No text extracted from {file_path}")
                return None

            # Clean the text
            cleaned_text = clean_text(text)

            return cleaned_text if cleaned_text else None

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None

    def get_metadata(self, file_path: Path) -> Dict:
        """
        Extract metadata from file

        Args:
            file_path: Path to file

        Returns:
            Dictionary of metadata
        """
        file_type = get_file_type(str(file_path))

        if not file_type:
            return {}

        try:
            if file_type == 'pdf':
                return self.pdf_extractor.extract_metadata(file_path)
            elif file_type == 'docx':
                return self.docx_extractor.extract_metadata(file_path)
            elif file_type == 'xlsx':
                return self.xlsx_extractor.extract_metadata(file_path)
            else:
                return {}

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {}

    def validate_file(self, file_path: Path) -> Dict[str, any]:
        """
        Validate that file can be processed

        Args:
            file_path: Path to file

        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'file_type': None,
            'error': None,
            'warnings': []
        }

        # Check file exists
        if not file_path.exists():
            result['error'] = "File does not exist"
            return result

        # Check file type
        file_type = get_file_type(str(file_path))
        if not file_type:
            result['error'] = "Unsupported file type"
            return result

        result['file_type'] = file_type

        # Try to extract text
        try:
            text = self.process_file(file_path)

            if not text:
                result['warnings'].append("No text could be extracted")
                result['valid'] = True  # File is valid but might be empty
            elif len(text) < 100:
                result['warnings'].append("Very little text extracted (< 100 characters)")
                result['valid'] = True
            else:
                result['valid'] = True

        except Exception as e:
            result['error'] = f"Error processing file: {str(e)}"
            return result

        return result

    def get_file_preview(self, file_path: Path, max_chars: int = 500) -> str:
        """
        Get a preview of file content

        Args:
            file_path: Path to file
            max_chars: Maximum characters to return

        Returns:
            Preview text
        """
        try:
            text = self.process_file(file_path)
            if not text:
                return ""

            if len(text) <= max_chars:
                return text

            return text[:max_chars] + "..."

        except Exception as e:
            logger.error(f"Error getting preview for {file_path}: {e}")
            return ""

    def batch_process(self, file_paths: List[Path],
                     callback=None) -> Dict[str, Optional[str]]:
        """
        Process multiple files

        Args:
            file_paths: List of file paths
            callback: Optional callback function(file_path, success, text)

        Returns:
            Dictionary mapping file paths to extracted text
        """
        results = {}

        for file_path in file_paths:
            try:
                text = self.process_file(file_path)
                results[str(file_path)] = text

                if callback:
                    callback(file_path, text is not None, text)

            except Exception as e:
                logger.error(f"Error in batch processing {file_path}: {e}")
                results[str(file_path)] = None

                if callback:
                    callback(file_path, False, None)

        return results

    def get_text_stats(self, file_path: Path) -> Dict:
        """
        Get statistics about extracted text

        Args:
            file_path: Path to file

        Returns:
            Dictionary of statistics
        """
        try:
            text = self.process_file(file_path)

            if not text:
                return {
                    'char_count': 0,
                    'word_count': 0,
                    'line_count': 0
                }

            return {
                'char_count': len(text),
                'word_count': len(text.split()),
                'line_count': len(text.split('\n'))
            }

        except Exception as e:
            logger.error(f"Error getting text stats for {file_path}: {e}")
            return {
                'char_count': 0,
                'word_count': 0,
                'line_count': 0
            }
