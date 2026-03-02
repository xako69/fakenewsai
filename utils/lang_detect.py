from langdetect import detect

def detect_language(text):
    try:
        code = detect(text)
        if code.startswith("ml"):
            return "ml"
        if code.startswith("hi"):
            return "hi"
        return "en"
    except:
        return "en"
