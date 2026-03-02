import urllib.parse
import requests
import feedparser
from rapidfuzz import fuzz
from utils.lang_detect import detect_language
from deep_translator import GoogleTranslator


# ✅ trusted publishers list (add more if you want)
TRUSTED_DOMAINS = [
    "bbc.co.uk", "bbc.com",
    "asianetnews.com",
    "timesofindia.indiatimes.com",
    "manoramaonline.com",
    "thehindu.com",
    "mathrubhumi.com",
    "reuters.com",
    "aljazeera.com",
    "theguardian.com",
    "apnews.com",
    "cnn.com",
    "ndtv.com",
    "indiatoday.in",
    "mathrubhumi.com",
    "asianetnews.com",
    "reporterlive.com",
    "mediaoneonline.com",
    "24news.in",
]

HEADERS = {"User-Agent": "Mozilla/5.0"}


# ---------------------------
# Keyword extractor (Theme)
# ---------------------------
STOPWORDS = set("""
a an the is are was were to of in on at for with from by as and or not this that
it its into about over after before during between under above
""".split())


def normalize_text(text: str) -> str:
    import re
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    # keep English + Malayalam + Hindi unicode blocks
    text = re.sub(r"[^a-zA-Z0-9\u0D00-\u0D7F\u0900-\u097F\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str, max_keywords: int = 10) -> str:
    text = normalize_text(text)
    tokens = [t for t in text.split() if len(t) > 2]
    tokens = [t for t in tokens if t not in STOPWORDS]

    # unique in order
    seen = set()
    keywords = []
    for t in tokens:
        if t not in seen:
            keywords.append(t)
            seen.add(t)
        if len(keywords) >= max_keywords:
            break

    return " ".join(keywords)


# ---------------------------
# Google News RSS Search
# ---------------------------
def google_news_rss_search(query: str, max_results: int = 30):
    lang = detect_language(query)

    if lang == "ml":
        hl, gl, ceid = "ml-IN", "IN", "IN:ml"
    elif lang == "hi":
        hl, gl, ceid = "hi-IN", "IN", "IN:hi"
    else:
        hl, gl, ceid = "en-IN", "IN", "IN:en"

    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

    r = requests.get(url, headers=HEADERS, timeout=12)
    r.raise_for_status()

    feed = feedparser.parse(r.text)

    results = []
    for e in feed.entries[:max_results]:
        title = e.get("title", "")
        link = e.get("link", "")
        src = e.get("source", {}).get("href", "") if "source" in e else ""
        results.append({"title": title, "link": link, "source": src})

    return results

# ---------------------------
# Helpers
# ---------------------------
def domain_of(url: str):
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except:
        return ""


def is_trusted_domain(domain: str):
    d = domain.lower()
    return any(td in d for td in TRUSTED_DOMAINS)


def resolve_final_url(url: str):
    """
    Google News RSS often gives redirect links.
    Resolve to publisher URL.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.url
    except:
        return url


def detect_publisher_domain(item: dict):
    # 1) Try RSS source field
    if item.get("source"):
        dom = domain_of(item["source"])
        if dom:
            return dom

    # 2) Resolve redirect
    final_url = resolve_final_url(item["link"])
    return domain_of(final_url)


# ---------------------------
# Headline Verification (exact-ish)
# ---------------------------
def verify_news_theme(input_text: str, threshold: int = 65, max_results: int = 30):
    """
    ✅ Theme-based verification (LANGUAGE AWARE)
    - Malayalam: lower threshold
    - Hindi: medium threshold
    - English: default threshold
    """

    # 🔍 Detect language
    lang = detect_language(input_text)

    # 🎯 Language-specific threshold
    if lang == "ml":
        effective_threshold = 45
    elif lang == "hi":
        effective_threshold = 55
    else:
        effective_threshold = threshold  # English default (65)

    # 🔑 Extract theme keywords
    theme_query = extract_keywords(input_text, max_keywords=10)

    # 🌐 Search Google News RSS using correct language feed
    results = google_news_rss_search(theme_query, max_results=max_results)

    matches = []
    matched_publishers = set()

    input_theme = extract_keywords(input_text, max_keywords=12)

    for r in results:
        publisher = detect_publisher_domain(r)

        # ❌ Skip untrusted domains
        if not is_trusted_domain(publisher):
            continue

        result_theme = extract_keywords(r["title"], max_keywords=12)

        # 🧠 Theme similarity (NOT exact title)
        score = fuzz.token_set_ratio(input_theme, result_theme)

        if score >= effective_threshold:
            matched_publishers.add(publisher)
            matches.append({
                "title": r["title"],
                "score": score,
                "publisher": publisher,
                "link": r["link"],
                "theme": result_theme
            })

    verified_count = len(matched_publishers)

    # ✅ Final decision
    if verified_count >= 4:
        decision = "REAL ✅ (Theme verified by >= 4 trusted publishers)"
    elif verified_count >= 1:
        decision = "UNCERTAIN ⚠️ (Theme partially verified)"
    else:
        decision = "NOT VERIFIED ❌ (Theme not found)"

    return decision, verified_count, matches, theme_query



# ---------------------------
# Theme Verification (keywords / main idea)
# ---------------------------
def verify_news_theme(input_text: str, threshold: int = 65, max_results: int = 30):
    lang = detect_language(input_text)

    # Language-specific thresholds
    if lang == "ml":
        effective_threshold = 45
    elif lang == "hi":
        effective_threshold = 55
    else:
        effective_threshold = threshold

    # --------- STEP 1: Malayalam verification ----------
    theme_query = extract_keywords(input_text, max_keywords=10)
    results = google_news_rss_search(theme_query, max_results=max_results)

    matches = []
    matched_publishers = set()

    input_theme = extract_keywords(input_text, max_keywords=12)

    for r in results:
        publisher = detect_publisher_domain(r)
        if not is_trusted_domain(publisher):
            continue

        result_theme = extract_keywords(r["title"], max_keywords=12)
        score = fuzz.token_set_ratio(input_theme, result_theme)

        if score >= effective_threshold:
            matched_publishers.add(publisher)
            matches.append({
                "title": r["title"],
                "score": score,
                "publisher": publisher,
                "link": r["link"],
                "theme": result_theme
            })

    verified_count = len(matched_publishers)

    # ✅ SUCCESS in Malayalam
    if verified_count >= 4:
        return "REAL ✅ (Malayalam sources verified)", verified_count, matches, theme_query

    # --------- STEP 2: FALLBACK → English verification ----------
    if lang == "ml":
        try:
            translated = GoogleTranslator(source="ml", target="en").translate(input_text)
        except:
            translated = ""

        if translated:
            en_theme = extract_keywords(translated, max_keywords=10)
            en_results = google_news_rss_search(en_theme, max_results=max_results)

            en_matches = []
            en_publishers = set()

            for r in en_results:
                publisher = detect_publisher_domain(r)
                if not is_trusted_domain(publisher):
                    continue

                score = fuzz.token_set_ratio(en_theme, extract_keywords(r["title"], 12))
                if score >= 60:
                    en_publishers.add(publisher)
                    en_matches.append({
                        "title": r["title"],
                        "score": score,
                        "publisher": publisher,
                        "link": r["link"],
                        "theme": en_theme
                    })

            if len(en_publishers) >= 4:
                return (
                    "REAL ✅ (Verified via cross-language sources)",
                    len(en_publishers),
                    en_matches,
                    en_theme
                )

            if len(en_publishers) >= 1:
                return (
                    "UNCERTAIN ⚠️ (Limited coverage, regional news)",
                    len(en_publishers),
                    en_matches,
                    en_theme
                )

    # --------- FINAL ----------
    return "NOT VERIFIED ❌ (Limited regional coverage)", 0, [], theme_query




# utils/semantic_verifier.py

from sentence_transformers import SentenceTransformer, util
import feedparser
import urllib.parse
import re
from datetime import datetime

print("🔥 Loading semantic model...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("✅ Semantic model loaded")

# --------------------------------------------------
# Trusted RSS Feeds (Direct Publishers)
# --------------------------------------------------

RSS_FEEDS = [
    # International
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://apnews.com/rss",

    # India
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",

    # Malayalam
    "https://www.manoramaonline.com/news/latest-news.rss",
    "https://www.mathrubhumi.com/rss/news/latest.rss",
    "https://www.asianetnews.com/rss"
]

# --------------------------------------------------
# Text Cleaning
# --------------------------------------------------

def clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\u0D00-\u0D7F\u0900-\u097F\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# --------------------------------------------------
# Date Extractor
# --------------------------------------------------

def extract_datetime(entry):
    if "published_parsed" in entry and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6])
        return dt.strftime("%Y-%m-%d %H:%M")
    return "Unknown"

# --------------------------------------------------
# Fetch Direct RSS Articles
# --------------------------------------------------

def fetch_rss_articles(limit=40):
    articles = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for e in feed.entries[:limit]:
            title = e.get("title", "")
            link = e.get("link", "")

            if len(title) > 15:
                articles.append({
                    "title": title,
                    "link": link,
                    "published": extract_datetime(e)
                })

    return articles

# --------------------------------------------------
# Google News RSS Search
# --------------------------------------------------

def google_news_search(query, max_results=50):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}"

    feed = feedparser.parse(url)

    results = []

    for e in feed.entries[:max_results]:
        results.append({
            "title": e.get("title", ""),
            "link": e.get("link", ""),
            "published": extract_datetime(e)
        })

    return results

# --------------------------------------------------
# MAIN SEMANTIC VERIFIER
# --------------------------------------------------

def semantic_verify(query, threshold=0.55):

    query = clean(query)

    articles = []
    articles.extend(fetch_rss_articles())
    articles.extend(google_news_search(query))

    if len(articles) == 0:
        return "NOT VERIFIED ❌", 0, []

    titles = [clean(a["title"]) for a in articles]

    # Encode
    q_emb = model.encode([query], convert_to_tensor=True)
    t_emb = model.encode(titles, convert_to_tensor=True)

    sims = util.cos_sim(q_emb, t_emb)[0]

    matches = []
    domains = set()

    for i, score in enumerate(sims):
        score = float(score)

        if score >= threshold:
            link = articles[i]["link"]
            domain = urllib.parse.urlparse(link).netloc

            domains.add(domain)

            matches.append({
                "title": articles[i]["title"],
                "score": round(score * 100, 2),
                "publisher": domain,
                "link": link,
                "published": articles[i]["published"]
            })

    count = len(domains)

    if count >= 4:
        decision = "REAL ✅ (Verified by multiple trusted sources)"
    elif count >= 1:
        decision = "UNCERTAIN ⚠️"
    else:
        decision = "NOT VERIFIED ❌"

    return decision, count, matches
