"""
inference/predictor.py
-----------------------
Runtime inference module.  Called by the Flask backend during live scans.

Usage (from backend scanner_service.py):
    from model.inference.predictor import predict_risk

    risk = predict_risk({
        "url_length":         45,
        "parameter_count":     2,
        "form_present":        1,
        "input_fields":        3,
        "special_characters":  2,
        "response_size":   14500,
        "status_code":       200,
        "endpoint_depth":      2,
    })
    # → "High"

The module loads the model once (lazily) and caches it in memory for
subsequent calls — avoiding a disk read on every scan request.
"""

import os
import logging
from typing import Any

import numpy as np
import joblib

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE        = os.path.dirname(os.path.abspath(__file__))
_ROOT        = os.path.dirname(_HERE)
_MODEL_PATH  = os.path.join(_ROOT, "saved_models", "vulnerability_risk_model.pkl")
_ENCODER_PATH= os.path.join(_ROOT, "saved_models", "label_encoder.pkl")

# ── Feature order — must match training/train_model.py FEATURE_COLS ───────────
_FEATURE_NAMES = [
    "url_length",
    "parameter_count",
    "form_present",
    "input_fields",
    "special_characters",
    "response_size",
    "status_code",
    "endpoint_depth",
]

# ── Risk label order (used by the fallback heuristic) ─────────────────────────
_RISK_LABELS = ["Low", "Medium", "High", "Critical"]

# ── Module-level cache ────────────────────────────────────────────────────────
_pipeline = None
_encoder  = None


def _load_model():
    """
    Lazily load the trained pipeline and label encoder from disk.
    Caches the result so subsequent calls return the in-memory objects.
    """
    global _pipeline, _encoder

    if _pipeline is not None:
        return _pipeline, _encoder

    if os.path.exists(_MODEL_PATH) and os.path.exists(_ENCODER_PATH):
        try:
            _pipeline = joblib.load(_MODEL_PATH)
            _encoder  = joblib.load(_ENCODER_PATH)
            logger.info("[predictor] Model loaded from %s", _MODEL_PATH)
        except Exception as exc:
            logger.error("[predictor] Failed to load model: %s", exc)
            _pipeline = _encoder = None
    else:
        logger.warning(
            "[predictor] Model file not found at '%s'. "
            "Using rule-based fallback. Run training/train_model.py to generate it.",
            _MODEL_PATH,
        )

    return _pipeline, _encoder


def predict_risk(features: dict[str, Any]) -> str:
    """
    Predict the vulnerability risk level for a single endpoint.

    Args:
        features: Dict mapping feature name → numeric value.
                  Missing keys default to 0.

    Returns:
        One of: "Low" | "Medium" | "High" | "Critical"
    """
    pipeline, encoder = _load_model()

    if pipeline is not None and encoder is not None:
        return _model_predict(pipeline, encoder, features)
    else:
        return _heuristic_predict(features)


def predict_risk_batch(feature_list: list[dict[str, Any]]) -> list[str]:
    """
    Predict risk levels for multiple endpoints at once.
    More efficient than calling predict_risk() in a loop for large scans.

    Args:
        feature_list: List of feature dicts.

    Returns:
        List of risk label strings in the same order.
    """
    pipeline, encoder = _load_model()

    if pipeline is not None and encoder is not None:
        matrix = np.array([
            [float(f.get(name, 0)) for name in _FEATURE_NAMES]
            for f in feature_list
        ])
        try:
            preds = pipeline.predict(matrix)
            return [str(encoder.inverse_transform([p])[0]) for p in preds]
        except Exception as exc:
            logger.error("[predictor] Batch prediction failed: %s", exc)

    # Fallback: predict individually
    return [_heuristic_predict(f) for f in feature_list]


def get_risk_probability(features: dict[str, Any]) -> dict[str, float]:
    """
    Return probability scores for each risk class (if the model supports it).

    Args:
        features: Feature dict.

    Returns:
        Dict mapping class name → probability (0.0–1.0).
        Returns equal weights if probabilities are unavailable.
    """
    pipeline, encoder = _load_model()

    if pipeline is not None and encoder is not None:
        if hasattr(pipeline, "predict_proba"):
            vector = np.array([[float(features.get(n, 0)) for n in _FEATURE_NAMES]])
            try:
                probs = pipeline.predict_proba(vector)[0]
                return {
                    str(label): float(prob)
                    for label, prob in zip(encoder.classes_, probs)
                }
            except Exception as exc:
                logger.warning("[predictor] predict_proba failed: %s", exc)

    # Equal-weight fallback
    return {label: 0.25 for label in _RISK_LABELS}


# ── Private helpers ───────────────────────────────────────────────────────────

def _model_predict(pipeline, encoder, features: dict[str, Any]) -> str:
    """Run a single prediction through the trained model pipeline."""
    vector = np.array([[float(features.get(n, 0)) for n in _FEATURE_NAMES]])
    try:
        pred  = pipeline.predict(vector)[0]
        label = str(encoder.inverse_transform([pred])[0])
        logger.debug("[predictor] Model → %s  (features=%s)", label, features)
        return label
    except Exception as exc:
        logger.error("[predictor] Prediction error: %s — falling back to heuristic", exc)
        return _heuristic_predict(features)


def _heuristic_predict(features: dict[str, Any]) -> str:
    """
    Rule-based fallback used when no trained model is available.
    Accumulates a risk score from feature thresholds.
    """
    score = 0

    if features.get("url_length", 0)         > 100: score += 2
    if features.get("parameter_count", 0)    > 5:   score += 3
    if features.get("input_fields", 0)        > 5:   score += 2
    if features.get("special_characters", 0) > 8:   score += 3
    if features.get("form_present", 0)               :score += 1
    if features.get("response_size", 0)      > 50_000: score += 1
    if features.get("status_code", 200)      >= 500: score += 2
    if features.get("endpoint_depth", 0)     >= 4:   score += 1

    if   score >= 10: return "Critical"
    elif score >= 6:  return "High"
    elif score >= 3:  return "Medium"
    else:             return "Low"


# ── CLI quick-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        {   # Expected: Low
            "url_length": 18, "parameter_count": 0, "form_present": 0,
            "input_fields": 0, "special_characters": 0,
            "response_size": 4_200, "status_code": 200, "endpoint_depth": 1,
        },
        {   # Expected: Medium
            "url_length": 55, "parameter_count": 2, "form_present": 1,
            "input_fields": 2, "special_characters": 3,
            "response_size": 12_000, "status_code": 200, "endpoint_depth": 3,
        },
        {   # Expected: High
            "url_length": 95, "parameter_count": 5, "form_present": 1,
            "input_fields": 5, "special_characters": 8,
            "response_size": 35_000, "status_code": 500, "endpoint_depth": 4,
        },
        {   # Expected: Critical
            "url_length": 160, "parameter_count": 12, "form_present": 1,
            "input_fields": 10, "special_characters": 20,
            "response_size": 90_000, "status_code": 500, "endpoint_depth": 6,
        },
    ]

    print("Predictor quick-test\n" + "-" * 40)
    for i, tc in enumerate(test_cases, 1):
        risk   = predict_risk(tc)
        probs  = get_risk_probability(tc)
        p_str  = "  ".join(f"{k}: {v:.2f}" for k, v in probs.items())
        print(f"Case {i}: {risk:10s}  | {p_str}")
