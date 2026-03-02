print("✅ merge_datasets.py started running...")

import os
import pandas as pd
from utils.preprocess import clean_text

RAW_DIR = "dataset/raw"
OUTPUT_FILE = "dataset/merged_news.csv"

# Candidates for different dataset column names
TEXT_COL_CANDIDATES = [
    "text", "content", "news", "article", "statement", "body", "full_text",
    "title"
]

LABEL_COL_CANDIDATES = [
    "label", "class", "target", "category", "is_fake", "fake", "y"
]

def standardize_label(x):
    """
    Converts different label styles into:
      0 = FAKE
      1 = REAL
    """
    if pd.isna(x):
        return None

    s = str(x).strip().lower()

    # numeric labels
    if s == "0":
        return 0
    if s == "1":
        return 1

    # string labels
    if "fake" in s or "false" in s or "unreliable" in s:
        return 0
    if "real" in s or "true" in s or "reliable" in s:
        return 1

    return None


def find_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def read_csv_safely(path):
    """
    Reads CSV safely.
    - Skips empty/corrupt files
    - Tries utf-8 then latin1
    Returns: DataFrame OR None
    """
    fname = os.path.basename(path)

    try:
        df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
        if df.empty or len(df.columns) == 0:
            print(f"⚠️ {fname} is empty/corrupt (no rows/columns). Skipping.")
            return None
        return df

    except pd.errors.EmptyDataError:
        print(f"⚠️ {fname} has no columns (EmptyDataError). Skipping.")
        return None

    except UnicodeDecodeError:
        try:
            df = pd.read_csv(path, encoding="latin1", on_bad_lines="skip")
            if df.empty or len(df.columns) == 0:
                print(f"⚠️ {fname} is empty/corrupt (no rows/columns). Skipping.")
                return None
            return df
        except Exception as e:
            print(f"⚠️ Failed reading {fname} with latin1: {e}")
            return None

    except Exception as e:
        print(f"⚠️ Failed reading {fname}: {e}")
        return None


def load_isot(true_path, fake_path):
    """
    Loads ISOT dataset (True.csv + Fake.csv) robustly.
    Returns DataFrame(text,label) OR None
    """
    # Skip if empty size
    if os.path.getsize(true_path) < 20 or os.path.getsize(fake_path) < 20:
        print("⚠️ ISOT True/Fake are empty (0 bytes). Skipping ISOT.")
        return None

    true_df = read_csv_safely(true_path)
    fake_df = read_csv_safely(fake_path)

    if true_df is None or fake_df is None:
        print("⚠️ ISOT files corrupt. Skipping ISOT.")
        return None

    # Add labels
    true_df["label"] = 1
    fake_df["label"] = 0

    df = pd.concat([true_df, fake_df], ignore_index=True)
    df.columns = [c.lower().strip() for c in df.columns]

    # Combine title + text if possible
    if "title" in df.columns and "text" in df.columns:
        df["text"] = df["title"].astype(str) + " " + df["text"].astype(str)

    if "text" not in df.columns:
        print("⚠️ ISOT missing 'text' column. Skipping.")
        return None

    return df[["text", "label"]]


def main():
    print("========== DATASET MERGER ==========")
    print("📌 RAW_DIR =", RAW_DIR)

    # Check folder exists
    if not os.path.exists(RAW_DIR):
        raise FileNotFoundError(f"❌ Folder not found: {RAW_DIR}")

    # List CSV files
    files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".csv")]
    print("📌 CSV Files Found:", files)

    if not files:
        raise ValueError("❌ No CSV files found in dataset/raw/")

    all_rows = []

    # --- Load ISOT dataset if available ---
    true_path = os.path.join(RAW_DIR, "True.csv")
    fake_path = os.path.join(RAW_DIR, "Fake.csv")

    if os.path.exists(true_path) and os.path.exists(fake_path):
        print("\n✅ ISOT dataset detected (True.csv + Fake.csv). Loading...")
        isot_df = load_isot(true_path, fake_path)

        if isot_df is not None:
            isot_df["text"] = isot_df["text"].astype(str).apply(clean_text)
            isot_df = isot_df[isot_df["text"].str.len() > 20]
            all_rows.append(isot_df)
            print("✅ ISOT loaded rows:", len(isot_df))
        else:
            print("⚠️ ISOT skipped.")

        # Remove these from remaining files
        files = [f for f in files if f not in ["True.csv", "Fake.csv"]]

    # --- Load all other datasets ---
    for f in files:
        path = os.path.join(RAW_DIR, f)
        print(f"\n📌 Reading dataset: {f}")

        df = read_csv_safely(path)
        if df is None:
            continue

        df.columns = [c.lower().strip() for c in df.columns]
        print("✅ Columns:", list(df.columns))

        text_col = find_column(df, TEXT_COL_CANDIDATES)
        label_col = find_column(df, LABEL_COL_CANDIDATES)

        if text_col is None:
            print(f"⚠️ Skipping {f}: No text column detected.")
            continue

        if label_col is None:
            print(f"⚠️ Skipping {f}: No label column detected.")
            continue

        temp = df[[text_col, label_col]].copy()
        temp.columns = ["text", "label"]

        # Standardize labels
        temp["label"] = temp["label"].apply(standardize_label)
        temp = temp.dropna()

        # Clean text
        temp["text"] = temp["text"].astype(str).apply(clean_text)
        temp = temp[temp["text"].str.len() > 20]

        if len(temp) == 0:
            print(f"⚠️ Skipping {f}: No valid rows after cleaning.")
            continue

        print(f"✅ Loaded rows from {f}: {len(temp)}")
        all_rows.append(temp)

    # --- Merge results ---
    if not all_rows:
        raise ValueError("❌ No valid datasets loaded. Check your CSV formats.")

    merged = pd.concat(all_rows, ignore_index=True)

    # Remove duplicates
    merged = merged.drop_duplicates(subset=["text"])

    # Save output
    os.makedirs("dataset", exist_ok=True)
    merged.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("\n========== MERGE SUMMARY ==========")
    print("✅ Total merged rows:", len(merged))
    print("✅ Label counts:\n", merged["label"].value_counts())
    print(f"\n✅ Generated successfully: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
