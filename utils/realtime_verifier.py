import requests
from sentence_transformers import SentenceTransformer, util
from urllib.parse import urlparse

# -----------------------
# Load Semantic Model
# -----------------------
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# -----------------------
# Trusted Domains
# -----------------------
TRUSTED_DOMAINS = [
    "bbc.com","bbc.co.uk","reuters.com","apnews.com","aljazeera.com",
    "theguardian.com","cnn.com","ndtv.com","indiatoday.in",
    "manoramaonline.com","mathrubhumi.com","asianetnews.com",
    "thehindu.com","timesofindia.indiatimes.com"
]

# -----------------------
# PUT YOUR API KEY HERE
# -----------------------
BING_KEY = "131f7d5b8cmsh2688bf16c01aaa7p193dd9jsnc55592621319"

HEADERS = {
    "X-BingApis-SDK": "true",
    "X-RapidAPI-Key": BING_KEY,
    "X-RapidAPI-Host": "bing-news-search1.p.rapidapi.com"
}

# -----------------------
# Domain Helper
# -----------------------
def domain_of(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""

# -----------------------
# Bing Search
# -----------------------
def bing_search(query):
    url = "https://bing-news-search1.p.rapidapi.com/news/search"
    params = {"q": query, "count": 50}

    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    data = r.json()

    results = []
    for item in data.get("value", []):
        results.append({
            "title": item["name"],
            "link": item["url"]
        })

    return results

# -----------------------
# MAIN VERIFIER
# -----------------------
def verify_news_theme(text):

    articles = bing_search(text)

    if not articles:
        return "NOT VERIFIED ❌ (No search results)", 0, [], text

    query_emb = model.encode(text, convert_to_tensor=True)

    matches = []
    publishers = set()

    for art in articles:
        domain = domain_of(art["link"])

        if not any(t in domain for t in TRUSTED_DOMAINS):
            continue

        emb = model.encode(art["title"], convert_to_tensor=True)
        score = util.cos_sim(query_emb, emb).item() * 100

        if score >= 65:
            publishers.add(domain)
            matches.append({
                "publisher": domain,
                "title": art["title"],
                "score": round(score,2),
                "link": art["link"]
            })

    count = len(publishers)

    if count >= 4:
        decision = "REAL ✅ (Verified by multiple trusted sources)"
    elif count >= 1:
        decision = "UNCERTAIN ⚠️"
    else:
        decision = "NOT VERIFIED ❌"

    return decision, count, matches, text
