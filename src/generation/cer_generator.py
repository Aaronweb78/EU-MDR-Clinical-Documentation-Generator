"""
Clinical Evaluation Report (CER) Generator
"""
from typing import Dict, List
from .section_generator import SectionGenerator


class CERGenerator:
    """Generate Clinical Evaluation Report documents"""

    SECTIONS = [
        {'number': 1, 'title': 'Executive Summary', 'prompt_file': 'section_01_executive_summary.txt', 'categories': ['clinical_study', 'literature']},
        {'number': 2, 'title': 'Scope', 'prompt_file': 'section_02_scope.txt', 'categories': ['regulatory']},
        {'number': 3, 'title': 'Device Description', 'prompt_file': 'section_03_device_description.txt', 'categories': ['device_description']},
        {'number': 4, 'title': 'Intended Purpose', 'prompt_file': 'section_04_intended_purpose.txt', 'categories': ['intended_use']},
        {'number': 5, 'title': 'Clinical Background and State of the Art', 'prompt_file': 'section_07_clinical_background_sota.txt', 'categories': ['literature']},
        {'number': 6, 'title': 'Clinical Data Analysis', 'prompt_file': 'section_13_data_analysis.txt', 'categories': ['clinical_study', 'performance_testing']},
        {'number': 7, 'title': 'Safety Evaluation', 'prompt_file': 'section_14_safety_evaluation.txt', 'categories': ['risk_management', 'clinical_study', 'post_market']},
        {'number': 8, 'title': 'Performance Evaluation', 'prompt_file': 'section_15_performance_evaluation.txt', 'categories': ['performance_testing', 'clinical_study']},
        {'number': 9, 'title': 'Risk-Benefit Analysis', 'prompt_file': 'section_16_risk_benefit_analysis.txt', 'categories': ['risk_management', 'clinical_study']},
        {'number': 10, 'title': 'Conclusions', 'prompt_file': 'section_17_conclusions.txt', 'categories': ['clinical_study', 'risk_management']},
    ]

    def __init__(self, section_generator: SectionGenerator):
        self.section_generator = section_generator

    def get_sections(self) -> List[Dict]:
        return self.SECTIONS.copy()

    def generate_section(self, project_id: str, section_config: Dict, device_info: Dict) -> Dict:
        return self.section_generator.generate_section(
            project_id=project_id,
            report_type='CER',
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
