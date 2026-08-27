import re
import hashlib
from typing import Set, List

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "about", "above", "after", "again",
    "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both",
    "by", "can", "cannot", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself",
    "yourselves", "why", "does", "mystery", "behind", "what", "happens", "place",
    "imagine", "discovering", "studied", "studies", "discovers", "uncover", "uncovered"
}

def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and normalize whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def compute_fingerprint(text: str) -> str:
    """Compute SHA-256 fingerprint of normalized text."""
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def extract_meaningful_tokens(text: str) -> Set[str]:
    """Extract set of non-stopword tokens from text."""
    normalized = normalize_text(text)
    words = normalized.split()
    return {w for w in words if w not in STOPWORDS and len(w) > 2}

def token_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts ratio (0.0 to 1.0).
    Uses RapidFuzz ratio if available, otherwise Jaccard token overlap.
    """
    if HAS_RAPIDFUZZ:
        return fuzz.token_sort_ratio(normalize_text(text1), normalize_text(text2)) / 100.0
    
    tokens1 = extract_meaningful_tokens(text1)
    tokens2 = extract_meaningful_tokens(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / float(len(union))

def count_words(text: str) -> int:
    """Count words in script or sentence."""
    if not text:
        return 0
    words = re.findall(r'\b\w+\b', text)
    return len(words)

def extract_concise_keywords(narration_or_concept: str, max_words: int = 5) -> str:
    """
    Extract a concise 2-5 word visual query from narration or concept description.
    Ensures query is short, clear, and focused on key visual nouns.
    """
    cleaned = normalize_text(narration_or_concept)
    words = cleaned.split()
    meaningful = [w for w in words if w not in STOPWORDS]
    if not meaningful:
        meaningful = words[:max_words]
    else:
        meaningful = meaningful[:max_words]
    return " ".join(meaningful)
