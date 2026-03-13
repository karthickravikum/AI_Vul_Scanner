"""
services/ai_service.py
-----------------------
Loads a pre-trained scikit-learn model and uses it to predict the
risk level of a given endpoint based on extracted features.

Risk levels (model output labels):
    Low | Medium | High | Critical

Changes from original:
    - Model loads at MODULE IMPORT TIME (startup) not on first request
    - Both pipeline and label encoder loaded together
    - gc.collect() called after predictions to free memory
    - Robust path resolution that works both locally and on Render
"""

import gc
import logging
import os
from typing import Dict, Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# ── Resolve model paths ───────────────────────────────────────────────────────
# Works in all environments:
#   Local:  backend/ → ../model/saved_models/
#   Render: /opt/render/project/src/backend/ → ../model/saved_models/

def _resolve_model_path() -> str:
    """
    Find the model file by checking multiple possible locations.
    Returns the first valid path found.
    """
    # 1. Check environment variable first (set in .env or Render dashboard)
    env_path = os.getenv("MODEL_PATH", "")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. Relative path from backend/ folder
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(here)  # services/ → backend/

    candidates = [
        os.path.join(backend_dir, "..", "model", "saved_models", "vulnerability_risk_model.pkl"),
        os.path.join(backend_dir, "model", "saved_models", "vulnerability_risk_model.pkl"),
        os.path.join(backend_dir, "saved_models", "vulnerability_risk_model.pkl"),
        # Render absolute path fallback
        "/opt/render/project/src/model/saved_models/vulnerability_risk_model.pkl",
    ]

    for path in candidates:
        normalised = os.path.normpath(path)
        if os.path.exists(normalised):
            return normalised

    # Return the default even if it doesn't exist — caller handles missing file
    return os.path.normpath(candidates[0])


def _resolve_encoder_path(model_path: str) -> str:
    """Derive the label encoder path from the model path."""
    return model_path.replace(
        "vulnerability_risk_model.pkl",
        "label_encoder.pkl"
    )


# ── Load model at startup (module import time) ────────────────────────────────
# Loading here means:
#   - Memory is allocated ONCE and shared across all requests
#   - No per-request loading overhead
#   - Faster response on first scan request

_MODEL_PATH   = _resolve_model_path()
_ENCODER_PATH = _resolve_encoder_path(_MODEL_PATH)

_pipeline = None
_encoder  = None

try:
    if os.path.exists(_MODEL_PATH) and os.path.exists(_ENCODER_PATH):
        _pipeline = joblib.load(_MODEL_PATH)
        _encoder  = joblib.load(_ENCODER_PATH)
        logger.info("ML model loaded at startup from: %s", _MODEL_PATH)
        logger.info("Label encoder loaded from: %s", _ENCODER_PATH)
    else:
        logger.warning(
            "Model not found at '%s'. Using rule-based fallback. "
            "Run model/training/train_model.py to generate it.",
            _MODEL_PATH
        )
except Exception as exc:
    logger.error("Failed to load model at startup: %s", exc)
    _pipeline = None
    _encoder  = None


# ── Public API ────────────────────────────────────────────────────────────────

def predict_risk(features: Dict[str, Any]) -> str:
    """
    Predict the vulnerability risk level for a single endpoint.

    Args:
        features: Dict produced by utils/feature_extractor.py, e.g.:
            {
                "url_length":         45,
                "num_parameters":      2,
                "num_input_fields":    3,
                "response_size":   12800,
                "status_code":       200,
                "num_special_chars":   5,
                "has_forms":           1,
                "has_password_field":  0,
            }

    Returns:
        One of: "Low", "Medium", "High", "Critical"
    """
    if _pipeline is not None and _encoder is not None:
        return _predict_with_model(features)
    else:
        return _rule_based_fallback(features)


# ── Private helpers ───────────────────────────────────────────────────────────

def _predict_with_model(features: Dict[str, Any]) -> str:
    """
    Use the trained scikit-learn pipeline to predict risk.
    Calls gc.collect() after prediction to free any temporary memory.
    """
    # Build a single-row feature vector in the exact order used during training
    feature_vector = np.array([[
        features.get("url_length",          0),
        features.get("num_parameters",      0),
        features.get("num_input_fields",    0),
        features.get("response_size",       0),
        features.get("status_code",       200),
        features.get("num_special_chars",   0),
        features.get("has_forms",           0),
        features.get("has_password_field",  0),
    ]])

    try:
        raw_prediction: int = int(_pipeline.predict(feature_vector)[0])

        # Use label encoder to convert numeric label → string
        try:
            risk = str(_encoder.inverse_transform([raw_prediction])[0])
        except Exception:
            # Fallback label map if encoder fails
            risk = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}.get(
                raw_prediction, "Medium"
            )

        logger.debug("Model predicted risk=%s for features=%s", risk, features)
        return risk

    except Exception as exc:
        logger.error("Model prediction failed: %s — falling back to heuristic.", exc)
        return _rule_based_fallback(features)

    finally:
        # Free any temporary numpy/sklearn memory immediately
        gc.collect()


def _rule_based_fallback(features: Dict[str, Any]) -> str:
    """
    Score-based heuristic used when no trained model is available.
    Accumulates risk points from feature thresholds and buckets into a label.
    """
    score = 0

    # Longer URLs with many parameters are more likely to be exploitable
    if features.get("url_length", 0) > 100:
        score += 1
    if features.get("num_parameters", 0) > 3:
        score += 2

    # Pages with many input fields offer more attack surface
    if features.get("num_input_fields", 0) > 5:
        score += 2

    # Password fields always increase risk
    if features.get("has_password_field", 0):
        score += 3

    # Forms submitted to the page increase risk
    if features.get("has_forms", 0):
        score += 1

    # Special characters in the URL may indicate injection attempts
    if features.get("num_special_chars", 0) > 5:
        score += 2

    # Large responses may contain verbose error messages
    if features.get("response_size", 0) > 100_000:
        score += 1

    if score >= 8:
        return "Critical"
    elif score >= 5:
        return "High"
    elif score >= 2:
        return "Medium"
    else:
        return "Low"