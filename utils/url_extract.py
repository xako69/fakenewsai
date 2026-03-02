# utils/url_extract.py

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def extract_title_from_url(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Try OpenGraph title (most news sites)
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()

        # Try normal <title>
        if soup.title and soup.title.string:
            return soup.title.string.strip()

    except Exception:
        pass

    # Final fallback: newspaper3k
    try:
        from newspaper import Article
        art = Article(url)
        art.download()
        art.parse()
        return art.title
    except Exception:
        return None
