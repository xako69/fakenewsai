import requests

BING_KEY = "131f7d5b8cmsh2688bf16c01aaa7p193dd9jsnc5559262f319"
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/news/search"

def bing_search(query, count=50):
    headers = {"Ocp-Apim-Subscription-Key": BING_KEY}
    params = {
        "q": query,
        "mkt": "en-IN",
        "count": count
    }
    r = requests.get(BING_ENDPOINT, headers=headers, params=params)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("value", []):
        results.append({
            "title": item["name"],
            "url": item["url"]
        })

    return results
