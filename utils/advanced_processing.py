from newspaper import Article
from deep_translator import GoogleTranslator


# -----------------------------------
# 🔥 Extract FULL article content
# -----------------------------------
def extract_full_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        title = article.title
        text = article.text

        return title, text
    except Exception as e:
        print("Extraction error:", e)
        return "", ""


# -----------------------------------
# 🌍 Translate to English
# -----------------------------------
def translate_to_english(text):
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated
    except Exception as e:
        print("Translation error:", e)
        return text  # fallback