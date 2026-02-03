"""
Entity extraction from documents
"""
import re
import json
import logging
from typing import Dict, List, Optional
from config import DEVICE_ENTITIES, PROMPTS_DIR
from ..utils.text_utils import create_excerpt

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract structured entities from documents"""

    def __init__(self, llm_client=None):
        """
        Initialize entity extractor

        Args:
            llm_client: LLM client for extraction
        """
        self.llm_client = llm_client
        self.entity_types = DEVICE_ENTITIES

    def extract_rule_based(self, text: str) -> Dict[str, any]:
        """
        Extract entities using rule-based methods (fast, no LLM)

        Args:
            text: Document text

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Device class extraction (Roman numerals or text)
        device_class_pattern = r'Class\s+(III|IIb|IIa|II|I|3|2a|2b|2|1)'
        class_match = re.search(device_class_pattern, text, re.IGNORECASE)
        if class_match:
            entities['device_class'] = class_match.group(1)

        # Model number patterns
        model_patterns = [
            r'Model\s*(?:Number|No\.?|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'Product\s*(?:Number|No\.?|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'Catalog\s*(?:Number|No\.?|#)?\s*:?\s*([A-Z0-9\-]+)'
        ]
        for pattern in model_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities['device_model'] = match.group(1)
                break

        # Sterile/Non-sterile
        if re.search(r'\bsterile\b', text, re.IGNORECASE):
            entities['sterile'] = 'Yes'
        elif re.search(r'\bnon-sterile\b', text, re.IGNORECASE):
            entities['sterile'] = 'No'

        # Single use
        if re.search(r'\bsingle[\s-]use\b', text, re.IGNORECASE):
            entities['single_use'] = 'Yes'
        elif re.search(r'\breusable\b|\bmulti[\s-]use\b', text, re.IGNORECASE):
            entities['single_use'] = 'No'

        # Implantable
        if re.search(r'\bimplant(?:able|ed)?\b', text, re.IGNORECASE):
            entities['implantable'] = 'Yes'

        # Active device
        if re.search(r'\bactive\s+(?:medical\s+)?device\b', text, re.IGNORECASE):
            entities['active_device'] = 'Yes'

        # Software
        if re.search(r'\bsoftware\b|\bIEC\s+62304\b|\balgorithm\b', text, re.IGNORECASE):
            entities['contains_software'] = 'Yes'

        # ISO standards
        iso_pattern = r'ISO\s+\d{4,5}(?:[-:]\d+)?'
        iso_matches = re.findall(iso_pattern, text)
        if iso_matches:
            entities['applicable_standards'] = list(set(iso_matches))

        return entities

    def extract_llm_based(self, text: str, filename: str = "") -> Dict[str, any]:
        """
        Extract entities using LLM (more comprehensive)

        Args:
            text: Document text
            filename: Original filename

        Returns:
            Dictionary of extracted entities
        """
        if not self.llm_client:
            logger.warning("LLM client not available, using rule-based extraction")
            return self.extract_rule_based(text)

        try:
            # Create excerpt (use more text than classification)
            excerpt = create_excerpt(text, max_length=3000)

            # Build prompt
            prompt = self._build_extraction_prompt(filename, excerpt)

            # Call LLM
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=800
            )

            # Parse response
            entities = self._parse_extraction_response(response)

            # Merge with rule-based results
            rule_based = self.extract_rule_based(text)
            for key, value in rule_based.items():
                if key not in entities or not entities[key]:
                    entities[key] = value

            return entities

        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {e}")
            return self.extract_rule_based(text)

    def _build_extraction_prompt(self, filename: str, excerpt: str) -> str:
        """Build prompt for entity extraction"""
        # Load prompt template
        prompt_file = PROMPTS_DIR / "extraction" / "extract_entities.txt"

        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                template = f.read()
            return template.format(filename=filename, content=excerpt)
        else:
            # Fallback built-in prompt
            entity_list = "\n".join([
                f"- {key}: {desc}"
                for key, desc in self.entity_types.items()
            ])

            return f"""You are a medical device regulatory expert. Extract the following entities from this document:

Entities to extract:
{entity_list}

Document filename: {filename}
Document content (excerpt):
{excerpt}

Respond with ONLY a JSON object with the entity values. Use null for any entity you cannot find.
Example format:
{{
    "device_name": "Example Device",
    "device_class": "IIa",
    "manufacturer": "Example Corp",
    ...
}}"""

    def _parse_extraction_response(self, response: str) -> Dict:
        """Parse LLM extraction response"""
        try:
            # Extract JSON from response
            response = response.strip()
            start = response.find('{')
            end = response.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                entities = json.loads(json_str)

                # Filter out null/empty values
                return {k: v for k, v in entities.items() if v}
            else:
                raise ValueError("No JSON object found in response")

        except Exception as e:
            logger.error(f"Error parsing extraction response: {e}")
            return {}

    def extract(self, text: str, filename: str = "",
               use_llm: bool = False) -> Dict[str, any]:
        """
        Extract entities (auto-select method)

        Args:
            text: Document text
            filename: Original filename
            use_llm: Whether to use LLM-based extraction

        Returns:
            Dictionary of extracted entities
        """
        if use_llm and self.llm_client:
            return self.extract_llm_based(text, filename)
        else:
            return self.extract_rule_based(text)

    def merge_entities(self, entities_list: List[Dict]) -> Dict[str, any]:
        """
        Merge entities from multiple documents

        Args:
            entities_list: List of entity dictionaries

        Returns:
            Merged entities with preference for most complete/confident values
        """
        merged = {}

        for entities in entities_list:
            for key, value in entities.items():
                if not value:
                    continue

                if key not in merged:
                    merged[key] = value
                elif isinstance(value, list):
                    # Merge lists
                    if isinstance(merged[key], list):
                        merged[key].extend(value)
                        merged[key] = list(set(merged[key]))  # Remove duplicates
                    else:
                        merged[key] = value
                elif len(str(value)) > len(str(merged[key])):
                    # Prefer longer/more detailed value
                    merged[key] = value

        return merged

    def validate_entities(self, entities: Dict) -> Dict[str, bool]:
        """
        Validate extracted entities

        Args:
            entities: Dictionary of entities

        Returns:
            Dictionary mapping entity names to validation status
        """
        validation = {}

        # Validate device class
        if 'device_class' in entities:
            valid_classes = ['I', 'IIa', 'IIb', 'III', '1', '2a', '2b', '3']
            validation['device_class'] = entities['device_class'] in valid_classes

        # Validate yes/no fields
        yes_no_fields = ['sterile', 'single_use', 'implantable', 'active_device',
                        'contains_software', 'contains_medicinal']
        for field in yes_no_fields:
            if field in entities:
                validation[field] = entities[field] in ['Yes', 'No']

        return validation

    def extract_from_multiple_files(self, file_texts: Dict[str, str],
                                   use_llm: bool = False) -> Dict[str, any]:
        """
        Extract entities from multiple files and merge

        Args:
            file_texts: Dictionary mapping filenames to text content
            use_llm: Whether to use LLM-based extraction

        Returns:
            Merged entity dictionary
        """
        all_entities = []

        for filename, text in file_texts.items():
            entities = self.extract(text, filename, use_llm)
            if entities:
                all_entities.append(entities)

        return self.merge_entities(all_entities)

    def get_entity_confidence(self, entity_value: str, text: str) -> float:
        """
        Estimate confidence in extracted entity

        Args:
            entity_value: Extracted value
            text: Source text

        Returns:
            Confidence score (0-1)
        """
        if not entity_value or not text:
            return 0.0

        # Count occurrences in text
        occurrences = text.lower().count(str(entity_value).lower())

        if occurrences == 0:
            return 0.3  # Low confidence if not found in text
        elif occurrences == 1:
            return 0.6  # Medium confidence
        elif occurrences <= 5:
            return 0.8  # High confidence
        else:
            return 0.95  # Very high confidence (mentioned frequently)

    def format_entities_for_display(self, entities: Dict) -> str:
        """
        Format entities for human-readable display

        Args:
            entities: Entity dictionary

        Returns:
            Formatted string
        """
        if not entities:
            return "No entities extracted"

        lines = []
        for key, value in entities.items():
            label = self.entity_types.get(key, key).replace('_', ' ').title()

            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)

            lines.append(f"{label}: {value_str}")

        return "\n".join(lines)
