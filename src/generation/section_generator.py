"""
Section generator for reports
Generates individual sections using RAG and LLM
"""
from pathlib import Path
from typing import Dict, List, Optional
import logging
from config import PROMPTS_DIR

logger = logging.getLogger(__name__)


class SectionGenerator:
    """Generate report sections using RAG and LLM"""

    def __init__(self, llm_client, retriever):
        """
        Initialize section generator

        Args:
            llm_client: OllamaClient instance
            retriever: Retriever instance for RAG
        """
        self.llm_client = llm_client
        self.retriever = retriever

    def generate_section(
        self,
        project_id: str,
        report_type: str,
        section_number: int,
        section_title: str,
        section_prompt_file: str,
        device_info: Dict,
        preferred_categories: Optional[List[str]] = None,
        max_chunks: int = 10
    ) -> Dict:
        """
        Generate a single report section

        Args:
            project_id: Project identifier
            report_type: Report type (CEP, CER, SSCP, LSR)
            section_number: Section number
            section_title: Section title
            section_prompt_file: Prompt template filename
            device_info: Device information dictionary
            preferred_categories: Preferred document categories for retrieval
            max_chunks: Maximum chunks to retrieve

        Returns:
            Dictionary with generated content and metadata
        """
        try:
            # Load prompt template
            prompt_template = self._load_prompt_template(report_type, section_prompt_file)

            # Build query for retrieval
            query = f"{section_title} {device_info.get('device_name', '')} {device_info.get('intended_purpose', '')}"

            # Retrieve relevant context
            chunks = self.retriever.retrieve(
                project_id=project_id,
                query=query,
                n_results=max_chunks,
                categories=preferred_categories
            )

            # Build context string
            context = self.retriever.build_context_string(chunks, max_length=5000)

            # Format device info
            device_info_str = self._format_device_info(device_info)

            # Build final prompt
            final_prompt = prompt_template.format(
                device_info=device_info_str,
                context=context
            )

            # Generate with LLM
            logger.info(f"Generating {report_type} section {section_number}: {section_title}")

            content = self.llm_client.generate(
                prompt=final_prompt,
                temperature=0.3,
                max_tokens=2000
            )

            # Extract source file IDs
            source_files = list(set(chunk['metadata'].get('file_id') for chunk in chunks))

            return {
                'success': True,
                'content': content,
                'section_number': section_number,
                'section_title': section_title,
                'sources': source_files,
                'chunks_used': len(chunks)
            }

        except Exception as e:
            logger.error(f"Error generating section {section_title}: {e}")
            return {
                'success': False,
                'error': str(e),
                'section_number': section_number,
                'section_title': section_title
            }

    def generate_section_stream(
        self,
        project_id: str,
        report_type: str,
        section_number: int,
        section_title: str,
        section_prompt_file: str,
        device_info: Dict,
        preferred_categories: Optional[List[str]] = None,
        max_chunks: int = 10
    ):
        """
        Generate section with streaming (for real-time UI updates)

        Yields:
            Text chunks as they are generated
        """
        try:
            # Load prompt and retrieve context (same as above)
            prompt_template = self._load_prompt_template(report_type, section_prompt_file)
            query = f"{section_title} {device_info.get('device_name', '')} {device_info.get('intended_purpose', '')}"
            chunks = self.retriever.retrieve(project_id, query, max_chunks, preferred_categories)
            context = self.retriever.build_context_string(chunks, max_length=5000)
            device_info_str = self._format_device_info(device_info)

            final_prompt = prompt_template.format(
                device_info=device_info_str,
                context=context
            )

            # Stream generation
            for chunk in self.llm_client.generate_stream(final_prompt, temperature=0.3, max_tokens=2000):
                yield chunk

        except Exception as e:
            logger.error(f"Error streaming section {section_title}: {e}")
            yield f"\n\n[Error generating section: {str(e)}]\n\n"

    def _load_prompt_template(self, report_type: str, filename: str) -> str:
        """Load prompt template from file"""
        prompt_file = PROMPTS_DIR / report_type.lower() / filename

        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}")
            return self._get_default_prompt(report_type)

        with open(prompt_file, 'r') as f:
            return f.read()

    def _get_default_prompt(self, report_type: str) -> str:
        """Get default prompt if file not found"""
        return f"""You are a medical device regulatory writer creating a {report_type} per EU MDR 2017/745.

Device Information:
{{device_info}}

Relevant Context from Source Documents:
{{context}}

Write this section based on the information provided. Use formal regulatory language.
Be thorough, accurate, and compliant with EU MDR requirements.
Output only the section content, no headers or titles."""

    def _format_device_info(self, device_info: Dict) -> str:
        """Format device information for prompt"""
        lines = []
        for key, value in device_info.items():
            if value:
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")

        return "\n".join(lines) if lines else "Device information not available"

    def validate_generated_content(self, content: str) -> Dict:
        """
        Validate generated content quality

        Args:
            content: Generated text

        Returns:
            Validation results
        """
        validation = {
            'valid': True,
            'warnings': [],
            'word_count': len(content.split()),
            'char_count': len(content)
        }

        # Check minimum length
        if len(content) < 100:
            validation['valid'] = False
            validation['warnings'].append("Content too short (< 100 characters)")

        # Check for error messages
        if '[Error' in content or 'ERROR' in content.upper():
            validation['warnings'].append("Content may contain error messages")

        # Check for placeholder text
        placeholders = ['TODO', 'TBD', 'XXX', 'PLACEHOLDER']
        for placeholder in placeholders:
            if placeholder in content.upper():
                validation['warnings'].append(f"Content contains placeholder: {placeholder}")

        return validation
