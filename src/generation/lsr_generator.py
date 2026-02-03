"""
Literature Search Report (LSR) Generator
"""
from typing import Dict, List
from .section_generator import SectionGenerator


class LSRGenerator:
    """Generate Literature Search Report documents"""

    SECTIONS = [
        {'number': 1, 'title': 'Introduction', 'prompt_file': 'section_01_introduction.txt', 'categories': ['literature', 'regulatory']},
        {'number': 2, 'title': 'PICO Framework', 'prompt_file': 'section_03_pico_framework.txt', 'categories': ['intended_use', 'clinical_study']},
        {'number': 3, 'title': 'Search Strings and Terms', 'prompt_file': 'section_05_search_strings.txt', 'categories': ['literature']},
        {'number': 4, 'title': 'Search Results', 'prompt_file': 'section_09_search_results.txt', 'categories': ['literature']},
    ]

    def __init__(self, section_generator: SectionGenerator):
        self.section_generator = section_generator

    def get_sections(self) -> List[Dict]:
        return self.SECTIONS.copy()

    def generate_section(self, project_id: str, section_config: Dict, device_info: Dict) -> Dict:
        return self.section_generator.generate_section(
            project_id=project_id,
            report_type='LSR',
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
