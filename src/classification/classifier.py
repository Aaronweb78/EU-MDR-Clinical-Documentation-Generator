"""
Document classification using Ollama LLM
"""
import json
import logging
from typing import Dict, Optional
from pathlib import Path
from config import DOCUMENT_CATEGORIES, PROMPTS_DIR
from ..utils.text_utils import create_excerpt, find_text_matches

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classify documents into predefined categories"""

    def __init__(self, llm_client=None):
        """
        Initialize classifier

        Args:
            llm_client: LLM client for classification (optional, for LLM-based classification)
        """
        self.llm_client = llm_client
        self.categories = DOCUMENT_CATEGORIES

    def classify_keyword_based(self, text: str, filename: str = "") -> Dict:
        """
        Classify document using keyword matching (fast, no LLM needed)

        Args:
            text: Document text
            filename: Original filename

        Returns:
            Dictionary with category, confidence, and reasoning
        """
        if not text:
            return {
                'category': 'other',
                'confidence': 0.0,
                'reasoning': 'No text content'
            }

        # Score each category based on keyword matches
        scores = {}
        text_lower = text.lower()
        filename_lower = filename.lower()

        for category, info in self.categories.items():
            score = 0
            keywords = info.get('keywords', [])

            # Check text for keywords
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Count occurrences, with diminishing returns
                count = text_lower.count(keyword_lower)
                score += min(count, 5)  # Cap at 5 per keyword

            # Check filename for keywords
            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    score += 3  # Bonus for filename match

            scores[category] = score

        # Get best category
        if not scores or max(scores.values()) == 0:
            return {
                'category': 'other',
                'confidence': 0.5,
                'reasoning': 'No strong keyword matches found'
            }

        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]

        # Calculate confidence (normalize to 0-1)
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0

        # Ensure minimum confidence threshold
        if confidence < 0.3:
            best_category = 'other'
            confidence = 0.5

        return {
            'category': best_category,
            'confidence': round(confidence, 2),
            'reasoning': f'Keyword analysis suggests {best_category} (score: {max_score})'
        }

    def classify_llm_based(self, text: str, filename: str = "") -> Dict:
        """
        Classify document using LLM (more accurate, requires Ollama)

        Args:
            text: Document text
            filename: Original filename

        Returns:
            Dictionary with category, confidence, and reasoning
        """
        if not self.llm_client:
            logger.warning("LLM client not available, falling back to keyword-based classification")
            return self.classify_keyword_based(text, filename)

        try:
            # Create excerpt for LLM (don't send full text)
            excerpt = create_excerpt(text, max_length=1500)

            # Build prompt
            prompt = self._build_classification_prompt(filename, excerpt)

            # Call LLM
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=200
            )

            # Parse response
            result = self._parse_classification_response(response)

            return result

        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Fall back to keyword-based
            return self.classify_keyword_based(text, filename)

    def _build_classification_prompt(self, filename: str, excerpt: str) -> str:
        """Build prompt for classification"""
        # Load prompt template
        prompt_file = PROMPTS_DIR / "classification" / "classify_document.txt"

        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                template = f.read()
            return template.format(filename=filename, content=excerpt)
        else:
            # Fallback built-in prompt
            categories_list = "\n".join([
                f"- {cat}: {info['description']}"
                for cat, info in self.categories.items()
            ])

            return f"""You are a medical device regulatory expert. Classify the following document into exactly ONE of these categories:

Categories:
{categories_list}

Document filename: {filename}
Document content (excerpt):
{excerpt}

Respond with ONLY a JSON object in this exact format:
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation"
}}"""

    def _parse_classification_response(self, response: str) -> Dict:
        """Parse LLM classification response"""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Find JSON object in response
            start = response.find('{')
            end = response.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)

                # Validate category
                if result.get('category') not in self.categories:
                    result['category'] = 'other'

                # Ensure confidence is float between 0 and 1
                confidence = float(result.get('confidence', 0.5))
                result['confidence'] = max(0.0, min(1.0, confidence))

                return result
            else:
                raise ValueError("No JSON object found in response")

        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            return {
                'category': 'other',
                'confidence': 0.5,
                'reasoning': 'Failed to parse classification response'
            }

    def classify(self, text: str, filename: str = "",
                use_llm: bool = False) -> Dict:
        """
        Classify document (auto-select method)

        Args:
            text: Document text
            filename: Original filename
            use_llm: Whether to use LLM-based classification

        Returns:
            Dictionary with category, confidence, and reasoning
        """
        if use_llm and self.llm_client:
            return self.classify_llm_based(text, filename)
        else:
            return self.classify_keyword_based(text, filename)

    def get_category_info(self, category: str) -> Optional[Dict]:
        """Get information about a category"""
        return self.categories.get(category)

    def get_all_categories(self) -> Dict:
        """Get all available categories"""
        return self.categories.copy()

    def suggest_category(self, text: str, filename: str = "") -> list:
        """
        Suggest multiple possible categories with scores

        Args:
            text: Document text
            filename: Original filename

        Returns:
            List of (category, score) tuples, sorted by score
        """
        scores = {}
        text_lower = text.lower()
        filename_lower = filename.lower()

        for category, info in self.categories.items():
            score = 0
            keywords = info.get('keywords', [])

            for keyword in keywords:
                keyword_lower = keyword.lower()
                count = text_lower.count(keyword_lower)
                score += min(count, 5)

            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    score += 3

            if score > 0:
                scores[category] = score

        # Sort by score
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_categories

    def batch_classify(self, documents: list, use_llm: bool = False) -> list:
        """
        Classify multiple documents

        Args:
            documents: List of (text, filename) tuples
            use_llm: Whether to use LLM-based classification

        Returns:
            List of classification results
        """
        results = []

        for text, filename in documents:
            result = self.classify(text, filename, use_llm)
            results.append({
                'filename': filename,
                **result
            })

        return results

    def validate_classification(self, category: str) -> bool:
        """Check if category is valid"""
        return category in self.categories
