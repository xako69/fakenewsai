import cv2
import numpy as np
import pytesseract
import re
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# --------------------------------------------------
# Detect headline region (top dominant text)
# --------------------------------------------------
def detect_headline_region(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # DO NOT threshold aggressively
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, bw = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
    dilated = cv2.dilate(bw, kernel, iterations=2)

    contours, _ = cv2.findContours(
        dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    h, w = img.shape[:2]
    best = None
    max_area = 0

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        area = cw * ch
        if cw > w * 0.5 and ch > 45 and y < h * 0.6:
            if area > max_area:
                max_area = area
                best = (x, y, cw, ch)

    if best:
        x, y, cw, ch = best
        return img[y:y + ch, x:x + cw]

    return img[: int(h * 0.5), :]


# --------------------------------------------------
# Malayalam ligature repair
# --------------------------------------------------
def repair_malayalam(text):
    fixes = {
        "്െ": "െ",
        "്ി": "ി",
        "്ു": "ു",
        "്ാ": "ാ",
        "്ീ": "ീ",
        "്ു്": "ു",
        "്്": "",
        "ണ്‍": "ണ്",
        "ന്‍": "ന്",
        "ന് ്": "ന്",
        " ി": "ി",
        " െ": "െ",
        " ു": "ു",
        " ്": "",
    }

    for k, v in fixes.items():
        text = text.replace(k, v)

    return text


# --------------------------------------------------
# Clean Malayalam headline
# --------------------------------------------------
def clean_malayalam(text):
    # Remove numbers, dates, junk
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[(),:;•●■◆▶◀]", "", text)

    # Keep Malayalam only
    text = re.sub(r"[^\u0D00-\u0D7F\s]", "", text)

    text = re.sub(r"\s+", " ", text).strip()
    return repair_malayalam(text)


# --------------------------------------------------
# MAIN OCR FUNCTION
# --------------------------------------------------
def extract_text_from_image(image: Image.Image):
    img = np.array(image)

    roi = detect_headline_region(img)

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # VERY IMPORTANT: NO inversion here
    config = "--oem 3 --psm 6 -l mal"

    raw = pytesseract.image_to_string(gray, config=config)

    clean = clean_malayalam(raw)

    confidence = 0.9 if len(clean) > 15 else 0.6
    return clean, confidence
