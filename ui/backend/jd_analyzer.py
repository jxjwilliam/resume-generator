import re
from collections import Counter
from typing import Optional

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "dare", "ought", "used", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "because", "as", "if", "while",
    "this", "that", "these", "those", "it", "its", "you", "your",
    "we", "our", "they", "them", "their", "what", "which", "who",
    "whom", "i", "me", "my", "he", "him", "his", "she", "her",
}


def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    """Extract the most frequent meaningful keywords from JD text."""
    text = text.lower()
    words = re.findall(r"[a-z][a-z0-9+#.-]{2,}", text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def extract_text_from_pdf(path: str) -> Optional[str]:
    """Extract text from a PDF file. Returns None on failure."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages) if pages else None
    except Exception:
        return None
