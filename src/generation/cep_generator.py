"""
Clinical Evaluation Plan (CEP) Generator
"""
from typing import Dict, List
from .section_generator import SectionGenerator


class CEPGenerator:
    """Generate Clinical Evaluation Plan documents"""

    # Define all CEP sections
    SECTIONS = [
        {
            'number': 1,
            'title': 'Scope and Objectives',
            'prompt_file': 'section_01_scope_and_objectives.txt',
            'categories': ['regulatory', 'intended_use']
        },
        {
            'number': 2,
            'title': 'Device Description',
            'prompt_file': 'section_02_device_description.txt',
            'categories': ['device_description', 'intended_use']
        },
        {
            'number': 3,
            'title': 'Intended Purpose and Indications',
            'prompt_file': 'section_03_intended_purpose.txt',
            'categories': ['intended_use', 'labeling']
        },
        {
            'number': 4,
            'title': 'Clinical Background and Current Knowledge',
            'prompt_file': 'section_04_clinical_background.txt',
            'categories': ['literature', 'clinical_study']
        },
    ]

    def __init__(self, section_generator: SectionGenerator):
        """
        Initialize CEP generator

        Args:
            section_generator: SectionGenerator instance
        """
        self.section_generator = section_generator

    def get_sections(self) -> List[Dict]:
        """Get list of all CEP sections"""
        return self.SECTIONS.copy()

    def generate_section(
        self,
        project_id: str,
        section_config: Dict,
        device_info: Dict
    ) -> Dict:
        """
        Generate a single CEP section

        Args:
            project_id: Project identifier
            section_config: Section configuration dictionary
            device_info: Device information

        Returns:
            Generated section result
        """
        return self.section_generator.generate_section(
            project_id=project_id,
            report_type='CEP',
            section_number=section_config['number'],
            section_title=section_config['title'],
            section_prompt_file=section_config['prompt_file'],
            device_info=device_info,
            preferred_categories=section_config.get('categories'),
            max_chunks=10
        )

    def generate_all_sections(
        self,
        project_id: str,
        device_info: Dict,
        callback=None
    ) -> List[Dict]:
        """
        Generate all CEP sections

        Args:
            project_id: Project identifier
            device_info: Device information
            callback: Optional callback function(section_number, total_sections)

        Returns:
            List of generated sections
        """
        results = []
        total = len(self.SECTIONS)

        for i, section_config in enumerate(self.SECTIONS):
            if callback:
                callback(i + 1, total)

            result = self.generate_section(project_id, section_config, device_info)
            results.append(result)

        return results
