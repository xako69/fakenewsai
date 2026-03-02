import re

STOPWORDS = set("""
a an the is are was were to of in on at for with from by as and or not this that
it its into about over after before during between under above
""".split())

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\u0D00-\u0D7F\u0900-\u097F\s]", " ", text)  # keeps Malayalam+Hindi
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_keywords(text: str, max_keywords: int = 8) -> str:
    """
    Extract main theme keywords (works for English mostly; for Malayalam/Hindi it keeps tokens).
    For Malayalam/Hindi, stopword removal is minimal but still works as theme query.
    """
    text = normalize_text(text)

    tokens = [t for t in text.split() if len(t) > 2]
    tokens = [t for t in tokens if t not in STOPWORDS]

    # take unique tokens in order (theme words)
    seen = set()
    keywords = []
    for t in tokens:
        if t not in seen:
            keywords.append(t)
            seen.add(t)
        if len(keywords) >= max_keywords:
            break

    return " ".join(keywords)
