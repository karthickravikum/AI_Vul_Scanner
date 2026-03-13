"""
training/evaluate_model.py
---------------------------
Loads the saved model and produces a comprehensive evaluation report:

  • Accuracy, Precision, Recall, F1 (per class + weighted avg)
  • Confusion matrix heatmap
  • Per-class F1 bar chart
  • Feature importance chart (for tree-based models)

All charts are saved to:  model/evaluation_plots/

Run from the project root:
    python training/evaluate_model.py
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # non-interactive backend (safe for servers)
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATASET_PATH = os.path.join(ROOT, "dataset", "vulnerability_dataset.csv")
MODEL_PATH   = os.path.join(ROOT, "saved_models", "vulnerability_risk_model.pkl")
ENCODER_PATH = os.path.join(ROOT, "saved_models", "label_encoder.pkl")
PLOTS_DIR    = os.path.join(ROOT, "evaluation_plots")

FEATURE_COLS = [
    "url_length", "parameter_count", "form_present", "input_fields",
    "special_characters", "response_size", "status_code", "endpoint_depth",
]
RISK_ORDER = ["Low", "Medium", "High", "Critical"]

# ── Plot theme ────────────────────────────────────────────────────────────────
DARK_BG   = "#0d1117"
PANEL_BG  = "#161b22"
ACCENT    = "#00d4ff"
GRID_CLR  = "#21262d"
TEXT_CLR  = "#c9d1d9"
SEVERITY_PALETTE = {
    "Low":      "#30d158",
    "Medium":   "#ffd60a",
    "High":     "#ff6b2b",
    "Critical": "#ff2d55",
}

def _apply_dark_theme() -> None:
    plt.rcParams.update({
        "figure.facecolor":  DARK_BG,
        "axes.facecolor":    PANEL_BG,
        "axes.edgecolor":    GRID_CLR,
        "axes.labelcolor":   TEXT_CLR,
        "xtick.color":       TEXT_CLR,
        "ytick.color":       TEXT_CLR,
        "text.color":        TEXT_CLR,
        "grid.color":        GRID_CLR,
        "font.family":       "monospace",
        "font.size":         11,
    })


# ── 1. Load artefacts ─────────────────────────────────────────────────────────

def load_artefacts():
    """Load model pipeline and label encoder from disk."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}.\n"
            "Run  python training/train_model.py  first."
        )
    pipeline = joblib.load(MODEL_PATH)
    le       = joblib.load(ENCODER_PATH)
    print(f"[eval] Model loaded from {MODEL_PATH}")
    return pipeline, le


# ── 2. Prepare test data ──────────────────────────────────────────────────────

def prepare_test_data(le):
    """Reload dataset and recreate the exact same test split as training."""
    df      = pd.read_csv(DATASET_PATH)
    df_copy = df.copy()
    df_copy["risk_level"] = le.transform(df_copy["risk_level"])

    X = df_copy[FEATURE_COLS].values
    y = df_copy["risk_level"].values

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    return X_test, y_test


# ── 3. Metrics ────────────────────────────────────────────────────────────────

def print_metrics(y_true, y_pred, class_names) -> dict:
    """Print a formatted metrics table and return metric values."""
    acc = accuracy_score(y_true, y_pred)
    p   = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    r   = recall_score   (y_true, y_pred, average="weighted", zero_division=0)
    f1  = f1_score       (y_true, y_pred, average="weighted", zero_division=0)

    print("\n" + "=" * 52)
    print("  EVALUATION METRICS")
    print("=" * 52)
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  Precision : {p:.4f}  (weighted)")
    print(f"  Recall    : {r:.4f}  (weighted)")
    print(f"  F1 Score  : {f1:.4f}  (weighted)")
    print("=" * 52)
    print("\nPer-class report:\n")
    print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))

    return {"accuracy": acc, "precision": p, "recall": r, "f1": f1}


# ── 4. Confusion matrix plot ──────────────────────────────────────────────────

def plot_confusion_matrix(y_true, y_pred, class_names: list[str], save_path: str) -> None:
    """Save a heatmap of the normalised confusion matrix."""
    _apply_dark_theme()
    cm      = confusion_matrix(y_true, y_pred)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)

    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    sns.heatmap(
        cm_norm,
        annot=True, fmt=".2f",
        xticklabels=class_names,
        yticklabels=class_names,
        cmap="Blues",
        linewidths=0.5,
        linecolor=GRID_CLR,
        ax=ax,
        cbar_kws={"shrink": 0.8},
        annot_kws={"size": 12, "color": "white"},
    )
    ax.set_title("Confusion Matrix (Normalised)", color=ACCENT, pad=14, fontsize=14)
    ax.set_xlabel("Predicted Label",  fontsize=11)
    ax.set_ylabel("True Label",       fontsize=11)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"[eval] Confusion matrix → {save_path}")


# ── 5. Per-class F1 bar chart ─────────────────────────────────────────────────

def plot_f1_bars(y_true, y_pred, class_names: list[str], save_path: str) -> None:
    """Save a horizontal bar chart of per-class F1 scores."""
    _apply_dark_theme()
    f1s    = f1_score(y_true, y_pred, average=None, zero_division=0)
    colors = [SEVERITY_PALETTE.get(c, ACCENT) for c in class_names]

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)

    bars = ax.barh(class_names, f1s, color=colors, height=0.55)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("F1 Score")
    ax.set_title("Per-Class F1 Score", color=ACCENT, pad=12, fontsize=14)
    ax.axvline(x=0.8, color=GRID_CLR, linestyle="--", linewidth=1)

    for bar, val in zip(bars, f1s):
        ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=11, color=TEXT_CLR)

    ax.spines[:].set_color(GRID_CLR)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"[eval] F1 bar chart     → {save_path}")


# ── 6. Feature importance ─────────────────────────────────────────────────────

def plot_feature_importance(pipeline, feature_names: list[str], save_path: str) -> None:
    """
    Save a feature importance chart.
    Works for RandomForest and GradientBoosting (which expose .feature_importances_).
    Silently skips if the classifier doesn't support it.
    """
    clf = pipeline.named_steps.get("clf")
    if not hasattr(clf, "feature_importances_"):
        print("[eval] Classifier has no feature_importances_ — skipping chart.")
        return

    importances = clf.feature_importances_
    indices     = np.argsort(importances)
    names_sorted = [feature_names[i] for i in indices]
    imp_sorted   = importances[indices]

    _apply_dark_theme()
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)

    ax.barh(names_sorted, imp_sorted, color=ACCENT, height=0.55)
    ax.set_xlabel("Importance")
    ax.set_title("Feature Importance", color=ACCENT, pad=12, fontsize=14)
    ax.spines[:].set_color(GRID_CLR)

    for i, val in enumerate(imp_sorted):
        ax.text(val + 0.002, i, f"{val:.3f}", va="center", fontsize=10, color=TEXT_CLR)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print(f"[eval] Feature importance → {save_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 52)
    print("  Vulnerability Risk Classifier — Evaluation")
    print("=" * 52 + "\n")

    os.makedirs(PLOTS_DIR, exist_ok=True)

    pipeline, le    = load_artefacts()
    class_names     = list(le.classes_)          # ["Critical","High","Low","Medium"]
    ordered_classes = [c for c in RISK_ORDER if c in class_names]

    X_test, y_test  = prepare_test_data(le)
    y_pred          = pipeline.predict(X_test)

    # ---- Metrics ----
    print_metrics(y_test, y_pred, ordered_classes)

    # ---- Plots ----
    plot_confusion_matrix(
        y_test, y_pred, ordered_classes,
        save_path=os.path.join(PLOTS_DIR, "confusion_matrix.png"),
    )
    plot_f1_bars(
        y_test, y_pred, ordered_classes,
        save_path=os.path.join(PLOTS_DIR, "f1_scores.png"),
    )
    plot_feature_importance(
        pipeline, FEATURE_COLS,
        save_path=os.path.join(PLOTS_DIR, "feature_importance.png"),
    )

    print(f"\n[eval] All plots saved to: {PLOTS_DIR}/")
    print("[eval] Evaluation complete.")


if __name__ == "__main__":
    main()
