"""
Text processing utilities
"""
import re
from typing import List, Dict
import tiktoken


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')

    return text.strip()


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text"""
    # Simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimate
        return len(text.split()) * 1.3


def truncate_text(text: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str:
    """Truncate text to maximum token count"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    except:
        # Fallback: word-based truncation
        words = text.split()
        max_words = int(max_tokens / 1.3)
        return ' '.join(words[:max_words])


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract key terms from text (simple frequency-based)"""
    # Convert to lowercase and split
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())

    # Common stopwords
    stopwords = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her',
        'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
        'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did',
        'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with', 'this', 'that',
        'from', 'have', 'they', 'will', 'what', 'been', 'more', 'when', 'your',
        'into', 'than', 'them', 'then', 'some', 'would', 'could', 'which', 'their'
    }

    # Count word frequencies
    word_freq = {}
    for word in words:
        if word not in stopwords and len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    return [word for word, freq in sorted_words[:top_n]]


def create_excerpt(text: str, max_length: int = 200) -> str:
    """Create a short excerpt from text"""
    if len(text) <= max_length:
        return text

    # Try to break at sentence end
    excerpt = text[:max_length]
    last_period = excerpt.rfind('.')
    last_question = excerpt.rfind('?')
    last_exclaim = excerpt.rfind('!')

    break_point = max(last_period, last_question, last_exclaim)

    if break_point > max_length * 0.7:  # If we found a good break point
        return text[:break_point + 1]
    else:
        # Break at space
        last_space = excerpt.rfind(' ')
        if last_space > 0:
            return text[:last_space] + "..."
        return excerpt + "..."


def find_text_matches(text: str, keywords: List[str]) -> Dict[str, int]:
    """Find keyword matches in text"""
    text_lower = text.lower()
    matches = {}

    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = text_lower.count(keyword_lower)
        if count > 0:
            matches[keyword] = count

    return matches


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple word overlap similarity between two texts"""
    words1 = set(re.findall(r'\b[a-z]{3,}\b', text1.lower()))
    words2 = set(re.findall(r'\b[a-z]{3,}\b', text2.lower()))

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


def format_numbered_list(items: List[str]) -> str:
    """Format list items with numbers"""
    return '\n'.join([f"{i+1}. {item}" for i, item in enumerate(items)])


def format_bullet_list(items: List[str]) -> str:
    """Format list items with bullets"""
    return '\n'.join([f"• {item}" for item in items])


def normalize_whitespace(text: str) -> str:
    """Normalize all whitespace to single spaces"""
    return ' '.join(text.split())


def remove_extra_newlines(text: str, max_consecutive: int = 2) -> str:
    """Remove excessive newlines"""
    pattern = r'\n{' + str(max_consecutive + 1) + r',}'
    return re.sub(pattern, '\n' * max_consecutive, text)


def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text"""
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches]


def contains_medical_terms(text: str) -> bool:
    """Check if text contains common medical/regulatory terms"""
    medical_terms = [
        'patient', 'clinical', 'medical', 'device', 'safety', 'efficacy',
        'treatment', 'diagnosis', 'therapy', 'regulatory', 'fda', 'ce mark',
        'iso', 'risk', 'adverse', 'contraindication', 'indication'
    ]

    text_lower = text.lower()
    return any(term in text_lower for term in medical_terms)
