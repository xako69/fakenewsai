import os
import joblib
import pandas as pd
from collections import Counter

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier, LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from utils.preprocess import clean_text

# ------------------ Paths ------------------
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fake_news_model.pkl")
VECT_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")


# ------------------ Dataset Loader ------------------
def load_dataset():
    """
    Supports 2 formats:

    FORMAT 1 (Single file):
      dataset/news.csv with columns: text,label

    FORMAT 2 (ISOT Kaggle dataset):
      dataset/True.csv and dataset/Fake.csv
    """

    news_path = "dataset/news.csv"
    true_path = "dataset/True.csv"
    fake_path = "dataset/Fake.csv"

    # ---------- Case 1: news.csv ----------
    if os.path.exists(news_path):
        print("✅ Found dataset/news.csv")

        # Check file size to avoid EmptyDataError
        if os.path.getsize(news_path) < 20:
            raise ValueError("❌ dataset/news.csv is empty. Replace with a real dataset.")

        df = pd.read_csv(news_path)

        if df.empty or len(df.columns) == 0:
            raise ValueError("❌ dataset/news.csv has no columns or no data.")

        df.columns = [c.lower().strip() for c in df.columns]

        # Check required columns
        if "text" not in df.columns or "label" not in df.columns:
            raise ValueError("❌ dataset/news.csv must contain columns: text,label")

        return df[["text", "label"]]

    # ---------- Case 2: True.csv + Fake.csv ----------
    elif os.path.exists(true_path) and os.path.exists(fake_path):
        print("✅ Found dataset/True.csv and dataset/Fake.csv (ISOT format)")

        true_df = pd.read_csv(true_path)
        fake_df = pd.read_csv(fake_path)

        # Assign labels
        true_df["label"] = 1  # REAL
        fake_df["label"] = 0  # FAKE

        # Combine
        df = pd.concat([true_df, fake_df], ignore_index=True)

        # Combine title + text if available
        if "title" in df.columns and "text" in df.columns:
            df["text"] = df["title"].astype(str) + " " + df["text"].astype(str)

        return df[["text", "label"]]

    else:
        raise FileNotFoundError(
            "❌ Dataset not found!\n"
            "Put either:\n"
            "1) dataset/news.csv (text,label)\n"
            "OR\n"
            "2) dataset/True.csv + dataset/Fake.csv"
        )


# ------------------ Safe Train-Test Split ------------------
def safe_split(X, y):
    """
    Uses stratify only if each class has at least 2 samples.
    Avoids:
    ValueError: least populated class has only 1 member
    """
    counts = Counter(y)
    min_class_count = min(counts.values())

    if min_class_count < 2:
        print("⚠️ Dataset too small for stratify. Splitting without stratify...")
        return train_test_split(X, y, test_size=0.2, random_state=42)

    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


# ------------------ Training ------------------
def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Load data
    df = load_dataset()

    # Preprocess text
    df["text"] = df["text"].astype(str).apply(clean_text)

    # Normalize labels if string
    label_map = {"fake": 0, "real": 1, "FAKE": 0, "REAL": 1}
    if df["label"].dtype == object:
        df["label"] = df["label"].astype(str).str.strip()
        df["label"] = df["label"].map(lambda x: label_map.get(x.lower(), x))

    # Drop missing
    df = df.dropna()

    X = df["text"]
    y = df["label"].astype(int)

    print("\n📌 Total Samples:", len(df))
    print("📌 Class Distribution:", Counter(y))

    # Split
    X_train, X_test, y_train, y_test = safe_split(X, y)

    # TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_df=0.7,
        ngram_range=(1, 2)
    )

    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Models (2 models for uniqueness)
    models = {
        "PassiveAggressiveClassifier": PassiveAggressiveClassifier(max_iter=1000, random_state=42),
        "LogisticRegression": LogisticRegression(max_iter=1000)
    }

    best_model = None
    best_name = None
    best_acc = 0

    # Train & Evaluate
    for name, model in models.items():
        model.fit(X_train_tfidf, y_train)
        preds = model.predict(X_test_tfidf)
        acc = accuracy_score(y_test, preds)

        print(f"\n=============================")
        print(f"✅ Model: {name}")
        print(f"✅ Accuracy: {acc:.4f}")
        print("Confusion Matrix:\n", confusion_matrix(y_test, preds))
        print("Classification Report:\n", classification_report(y_test, preds))

        if acc > best_acc:
            best_acc = acc
            best_model = model
            best_name = name

    # Save best model
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(vectorizer, VECT_PATH)

    print(f"\n🏆 BEST MODEL: {best_name} (Accuracy: {best_acc:.4f})")
    print(f"✅ Model Saved: {MODEL_PATH}")
    print(f"✅ Vectorizer Saved: {VECT_PATH}")
    print("\n✅ Training complete successfully!")


if __name__ == "__main__":
    main()
