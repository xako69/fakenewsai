import pandas as pd
import pickle
import os

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("dataset/merged_news.csv")

df = df[["text", "label"]]
df.dropna(inplace=True)

# Normalize labels
df["label"] = df["label"].astype(str).str.upper()
df["label"] = df["label"].replace({"1": "REAL", "0": "FAKE"})

print("Dataset:", df.shape)

# -----------------------------
# SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df["text"],
    df["label"],
    test_size=0.2,
    stratify=df["label"],
    random_state=42
)

# -----------------------------
# PIPELINE (UPGRADED)
# -----------------------------
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        stop_words="english",
        max_features=20000,
        ngram_range=(1,2),
        sublinear_tf=True
    )),
    ("model", LogisticRegression(
        max_iter=2000,
        class_weight="balanced"
    ))
])

print("Training model...")
pipeline.fit(X_train, y_train)

# -----------------------------
# EVALUATION
# -----------------------------
y_pred = pipeline.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred)*100)
print("\n", classification_report(y_test, y_pred))

# -----------------------------
# SAVE
# -----------------------------
os.makedirs("models", exist_ok=True)

pickle.dump(pipeline, open("models/ml_model.pkl", "wb"))

print("✅ Model saved in models/ml_model.pkl")