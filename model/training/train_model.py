"""
training/train_model.py
------------------------
Loads the synthetic dataset, preprocesses it, trains three classifiers,
selects the best one by cross-validated F1 score, and saves the winner.

Trained model is saved to:
    saved_models/vulnerability_risk_model.pkl

Run from the project root:
    python training/train_model.py
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble      import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree          import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline      import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics       import classification_report, accuracy_score

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATASET_PATH    = os.path.join(ROOT, "dataset", "vulnerability_dataset.csv")
MODEL_SAVE_PATH = os.path.join(ROOT, "saved_models", "vulnerability_risk_model.pkl")
LABEL_ENC_PATH  = os.path.join(ROOT, "saved_models", "label_encoder.pkl")

# ── Feature columns (must match feature_extractor.py FEATURE_NAMES) ──────────
FEATURE_COLS = [
    "url_length",
    "parameter_count",
    "form_present",
    "input_fields",
    "special_characters",
    "response_size",
    "status_code",
    "endpoint_depth",
]
TARGET_COL = "risk_level"

# ── Risk label ordering (used to make confusion matrices readable) ────────────
RISK_ORDER = ["Low", "Medium", "High", "Critical"]


# ── 1. Data loading ───────────────────────────────────────────────────────────

def load_data(path: str) -> pd.DataFrame:
    """
    Load the CSV dataset. If it doesn't exist, auto-generate it first.
    """
    if not os.path.exists(path):
        print("[train] Dataset not found — generating synthetic data…")
        from dataset.generate_dataset import generate_dataset
        generate_dataset(1200, output_path=path)

    df = pd.read_csv(path)
    print(f"[train] Loaded {len(df)} rows from {path}")
    print(f"[train] Class distribution:\n{df[TARGET_COL].value_counts().to_string()}\n")
    return df


# ── 2. Preprocessing ──────────────────────────────────────────────────────────

def preprocess(df: pd.DataFrame):
    """
    Encode target labels and split into train / test sets.

    Returns:
        X_train, X_test, y_train, y_test, label_encoder
    """
    le = LabelEncoder()
    le.fit(RISK_ORDER)                     # fixed class ordering
    df = df.copy()
    df[TARGET_COL] = le.transform(df[TARGET_COL])

    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"[train] Split → train: {len(X_train)}, test: {len(X_test)}")
    return X_train, X_test, y_train, y_test, le


# ── 3. Model definitions ──────────────────────────────────────────────────────

def build_candidates() -> dict[str, Pipeline]:
    """
    Return a dict of named scikit-learn Pipeline objects.
    Each pipeline = StandardScaler + classifier.
    Scaling helps tree-based models when feature ranges differ a lot.
    """
    return {
        "RandomForest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    RandomForestClassifier(
                n_estimators=150,
                max_depth=None,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )),
        ]),
        "GradientBoosting": Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    GradientBoostingClassifier(
                n_estimators=120,
                learning_rate=0.1,
                max_depth=4,
                random_state=42,
            )),
        ]),
        "DecisionTree": Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    DecisionTreeClassifier(
                max_depth=8,
                min_samples_leaf=3,
                random_state=42,
            )),
        ]),
    }


# ── 4. Training & selection ───────────────────────────────────────────────────

def train_and_select(
    candidates: dict[str, Pipeline],
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[str, Pipeline]:
    """
    Train each candidate using 5-fold cross-validation.
    Select the model with the highest mean weighted F1 score.

    Returns:
        (best_name, best_pipeline)
    """
    results: dict[str, float] = {}

    for name, pipeline in candidates.items():
        scores = cross_val_score(
            pipeline, X_train, y_train,
            cv=5, scoring="f1_weighted", n_jobs=-1
        )
        mean_f1 = float(scores.mean())
        results[name] = mean_f1
        print(f"[train]   {name:20s}  CV F1 = {mean_f1:.4f}  (±{scores.std():.4f})")

    best_name = max(results, key=results.__getitem__)
    print(f"\n[train] ✓ Best model: {best_name}  (F1 = {results[best_name]:.4f})\n")

    # Re-fit the winner on the full training set
    best_pipeline = candidates[best_name]
    best_pipeline.fit(X_train, y_train)
    return best_name, best_pipeline


# ── 5. Final evaluation on hold-out test set ─────────────────────────────────

def evaluate_on_test(
    pipeline: Pipeline,
    X_test: np.ndarray,
    y_test: np.ndarray,
    le: LabelEncoder,
    model_name: str,
) -> None:
    """Print accuracy and a full classification report on the test set."""
    y_pred = pipeline.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)

    print(f"[train] Test accuracy ({model_name}): {acc:.4f}\n")
    print(classification_report(
        y_test, y_pred,
        target_names=le.classes_,
        zero_division=0,
    ))


# ── 6. Save artefacts ─────────────────────────────────────────────────────────

def save_artefacts(pipeline: Pipeline, le: LabelEncoder) -> None:
    """Persist the trained model pipeline and label encoder to disk."""
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_SAVE_PATH)
    joblib.dump(le,       LABEL_ENC_PATH)
    print(f"[train] Model saved   → {MODEL_SAVE_PATH}")
    print(f"[train] Encoder saved → {LABEL_ENC_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  Vulnerability Risk Classifier — Training Pipeline")
    print("=" * 60 + "\n")

    df                              = load_data(DATASET_PATH)
    X_train, X_test, y_train, y_test, le = preprocess(df)
    candidates                      = build_candidates()

    print("[train] Running cross-validation on all candidates…")
    best_name, best_pipeline        = train_and_select(candidates, X_train, y_train)

    evaluate_on_test(best_pipeline, X_test, y_test, le, best_name)
    save_artefacts(best_pipeline, le)

    print("\n[train] Done.")


if __name__ == "__main__":
    main()
