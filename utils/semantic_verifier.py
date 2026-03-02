from sentence_transformers import SentenceTransformer, util
import feedparser
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup

from utils.advanced_processing import translate_to_english

# -----------------------------------
# LOAD MODEL
# -----------------------------------

print("🔥 Loading semantic model...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print("✅ Semantic model loaded")


# -----------------------------------
# RSS FEEDS (EXPANDED)
# -----------------------------------

RSS_FEEDS = [
    # 🌍 GLOBAL
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.reuters.com/rssFeed/worldNews",
    "https://rss.cnn.com/rss/edition_world.rss",
    "https://apnews.com/rss",
    "https://www.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.france24.com/en/rss",
    "https://www.dw.com/en/top-stories/rss",

    # 🇮🇳 INDIA
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://indianexpress.com/feed/",
    "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
    "https://www.indiatoday.in/rss/home",

    # 🇮🇳 MALAYALAM (VERY IMPORTANT)
    "https://www.manoramaonline.com/news/latest-news.rss",
    "https://www.manoramaonline.com/news/kerala.rss",
    "https://www.mathrubhumi.com/rss/news/latest.rss",
    "https://www.asianetnews.com/rss",
    "https://www.onmanorama.com/rss",
    "https://www.madhyamam.com/rss",
    "https://www.deshabhimani.com/rss",
]


# -----------------------------------
# CLEAN TEXT
# -----------------------------------

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s\u0D00-\u0D7F]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# -----------------------------------
# SCRAPE ORIGINAL ARTICLE
# -----------------------------------

def scrape_article_title(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        og = soup.find("meta", property="og:title")
        if og:
            return og.get("content", "")
        return soup.title.string if soup.title else ""
    except:
        return ""


# -----------------------------------
# STOPWORDS & KEYWORD EXTRACTION
# -----------------------------------

MAL_STOPWORDS = {
    "ആണ്","എന്ന്","ഇത്","ഒരു","ഉണ്ട്","ഇല്ല","എന്നും",
    "എന്ന","ആയി","പോയി","കഴിഞ്ഞു","വരെ","കൂടെ",
    "നിന്ന്","എന്നാൽ","അതേസമയം","അത്","ഈ","മാത്രം"
}

EN_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with","by","as","is","was","were","are","be",
    "this","that","it","from","bbc","cnn","news","live","updates","al","jazeera","reuters","ap","times","post",
    "edition","com","www","https","http","says","video","watch","breaking","exclusive","report"
}

def extract_malayalam_keywords(text):
    words = text.split()
    words = [w for w in words if w not in MAL_STOPWORDS and len(w) > 2]
    # Keep up to 8 keywords so we don't lose context at the end of long sentences
    return words[:8]

def extract_english_keywords(text):
    words = text.split()
    # Let 2-letter words live (US, UN, UK, El)
    words = [w for w in words if w not in EN_STOPWORDS and len(w) > 1]
    # 🔥 THE FIX: Keep up to 12 keywords so names/entities at the end are NOT deleted!
    return words[:12]


# -----------------------------------
# KEYWORD & ENTITY OVERLAP
# -----------------------------------

def keyword_overlap(q, t):
    return len(set(q.split()) & set(t.split())) / max(len(q.split()), 1)

def entity_match(q, t):
    return sum(1 for w in q.split() if len(w) > 3 and w in t)


# -----------------------------------
# FETCH RSS ARTICLES
# -----------------------------------

def fetch_rss_articles(limit=60):
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                if len(title) > 12:
                    articles.append({"title": title, "link": link})
        except:
            continue
    return articles


# -----------------------------------
# GOOGLE NEWS SEARCH
# -----------------------------------

def google_news_search(query, max_results=50, lang="en"):
    try:
        q = urllib.parse.quote(query)
        if lang == "ml":
            url = f"https://news.google.com/rss/search?q={q}&hl=ml&gl=IN&ceid=IN:ml"
        else:
            url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_results]:
            results.append({"title": entry.get("title", ""), "link": entry.get("link", "")})
        return results
    except:
        return []

# -----------------------------------
# REMOVE DUPLICATES
# -----------------------------------

def remove_duplicates(articles):
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


# -----------------------------------
# MAIN VERIFIER (FINAL SYSTEM)
# -----------------------------------
def semantic_verify(query, source_domain=None):

    original_query = query
    query_ml = clean_text(query)

    is_malayalam = bool(re.search(r'[\u0D00-\u0D7F]', query_ml))
    query_en = clean_text(translate_to_english(query_ml))

    search_queries_ml = []
    search_queries_en = []

    # Strip publisher footprints
    clean_query_en = " ".join([w for w in query_en.split() if w not in {"bbc", "cnn", "news", "edition", "com"}])
    search_queries_en.append(clean_query_en)

    if is_malayalam:
        keywords = extract_malayalam_keywords(query_ml)
        search_queries_ml.append(query_ml)
        if len(keywords) >= 3:
            search_queries_ml.append(" ".join(keywords))

    # Add targeted English keyword queries
    en_keywords = extract_english_keywords(clean_query_en)
    if len(en_keywords) > 2:
        search_queries_en.append(" ".join(en_keywords))

    # 🔥 FETCH ARTICLES
    articles = []
    articles.extend(fetch_rss_articles())

    trusted_publishers = {
        "asianetnews.com": "asianet news", 
        "manoramaonline.com": "manorama", 
        "mathrubhumi.com": "mathrubhumi"
    }
    
    if is_malayalam:
        short_query_ml = " ".join(keywords[:4]) if len(keywords) >= 4 else query_ml
        short_query_en = " ".join(en_keywords[:4]) if len(en_keywords) >= 4 else query_en 
        
        for domain, brand in trusted_publishers.items():
            q_ml = f"{short_query_ml} {brand}"
            articles.extend(google_news_search(q_ml, max_results=5, lang="ml"))
            
            q_en = f"{short_query_en} {brand}"
            articles.extend(google_news_search(q_en, max_results=5, lang="en"))

    for q in search_queries_ml:
        articles.extend(google_news_search(q, lang="ml"))

    for q in search_queries_en:
        articles.extend(google_news_search(q, lang="en"))

    articles = remove_duplicates(articles)

    if not articles:
        return "NOT VERIFIED ❌", 0, []

    titles = [clean_text(a["title"]) for a in articles]

    # 🔥 EMBEDDINGS
    query_emb_ml = model.encode([query_ml], convert_to_tensor=True)
    query_emb_en = model.encode([clean_query_en], convert_to_tensor=True)
    title_embs = model.encode(titles, convert_to_tensor=True)

    sim_ml = util.cos_sim(query_emb_ml, title_embs)[0]
    sim_en = util.cos_sim(query_emb_en, title_embs)[0]

    valid_matches = []

    for i in range(len(sim_ml)):
        score_ml = float(sim_ml[i])
        score_en = float(sim_en[i])
        score = max(score_ml, score_en)
        title = titles[i]

        overlap_ml = keyword_overlap(query_ml, title)
        overlap_en = keyword_overlap(clean_query_en, title)
        overlap = max(overlap_ml, overlap_en)

        entity_score_ml = entity_match(query_ml, title)
        entity_score_en = entity_match(clean_query_en, title)
        entity_score = max(entity_score_ml, entity_score_en)

        if score < 0.50:
            continue
            
        # 🔥 THE FIX: Lowered overlap penalty slightly so alternate headlines survive
        if score < 0.75 and overlap < 0.10:
            continue

        # FINAL SCORE
        final_score = (
            0.6 * score +
            0.25 * overlap +
            0.15 * (entity_score / 5)
        )

        final_score = min(final_score, 1.0)
        art = articles[i]
        domain = urllib.parse.urlparse(art["link"]).netloc

        if source_domain and source_domain in domain:
            final_score += 0.10

        if is_malayalam and any(x in domain for x in ["manorama", "mathrubhumi", "asianet"]):
            final_score += 0.10

        final_score = min(final_score, 1.0)

        if final_score >= 0.75:
            level = "HIGH"
        elif final_score >= 0.60:
            level = "MEDIUM"
        else:
            level = "LOW"

        record = {
            "title": art["title"],
            "score": round(final_score * 100, 2),
            "publisher": domain,
            "link": art["link"],
            "confidence": level
        }

        if not any(m['link'] == record['link'] for m in valid_matches):
            valid_matches.append(record)

    matches = sorted(valid_matches, key=lambda x: x["score"], reverse=True)
    matches = matches[:15]
    
    verified_count = len(matches)

    # -----------------------------------
    # FINAL DECISION
    # -----------------------------------
    
    unique_high_publishers = set([m["publisher"] for m in matches if m["confidence"] == "HIGH"])
    unique_medium_publishers = set([m["publisher"] for m in matches if m["confidence"] == "MEDIUM"])
    
    high = len(unique_high_publishers)
    medium = len(unique_medium_publishers)
    
    top_score = matches[0]["score"] if matches else 0

    if high >= 3:
        decision = "REAL (Widely Reported)"
    elif high >= 1 and top_score > 80.0:
        decision = "REAL (Verified Match)"
    elif (high + medium) >= 2:
        decision = "LIKELY REAL"
    elif (high + medium) == 1:
        decision = "NEEDS MORE SOURCES"
    else:
        decision = "NOT VERIFIED"

    return decision, verified_count, matches