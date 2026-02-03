"""
Summary of Safety and Clinical Performance (SSCP) Generator
"""
from typing import Dict, List
from .section_generator import SectionGenerator


class SSCPGenerator:
    """Generate SSCP documents"""

    SECTIONS = [
        {'number': 1, 'title': 'Device Identification', 'prompt_file': 'section_01_device_identification.txt', 'categories': ['device_description', 'regulatory']},
        {'number': 2, 'title': 'Intended Purpose', 'prompt_file': 'section_02_intended_purpose.txt', 'categories': ['intended_use']},
        {'number': 3, 'title': 'Device Description', 'prompt_file': 'section_03_device_description.txt', 'categories': ['device_description']},
        {'number': 4, 'title': 'Residual Risks and Warnings', 'prompt_file': 'section_04_risks_and_warnings.txt', 'categories': ['risk_management']},
        {'number': 5, 'title': 'Summary of Clinical Evaluation', 'prompt_file': 'section_05_clinical_evaluation_summary.txt', 'categories': ['clinical_study', 'literature']},
    ]

    def __init__(self, section_generator: SectionGenerator):
        self.section_generator = section_generator

    def get_sections(self) -> List[Dict]:
        return self.SECTIONS.copy()

    def generate_section(self, project_id: str, section_config: Dict, device_info: Dict) -> Dict:
        return self.section_generator.generate_section(
            project_id=project_id,
            report_type='SSCP',
            section_number=section_config['number'],
            section_title=section_config['title'],
            section_prompt_file=section_config['prompt_file'],
            device_info=device_info,
            preferred_categories=section_config.get('categories'),
            max_chunks=10
        )

    def generate_all_sections(self, project_id: str, device_info: Dict, callback=None) -> List[Dict]:
        results = []
        total = len(self.SECTIONS)

        for i, section_config in enumerate(self.SECTIONS):
            if callback:
                callback(i + 1, total)
            result = self.generate_section(project_id, section_config, device_info)
            results.append(result)

        return results
