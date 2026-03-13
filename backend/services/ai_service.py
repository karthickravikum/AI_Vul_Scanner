"""
services/ai_service.py
-----------------------
Loads a pre-trained scikit-learn model and uses it to predict the
risk level of a given endpoint based on extracted features.

Risk levels (model output labels):
    0 → "Low"
    1 → "Medium"
    2 → "High"
    3 → "Critical"

If no trained model file exists yet, the service falls back to a
simple rule-based heuristic so the rest of the pipeline still works
during development / demos.
"""

import logging
import os
from typing import Dict, Any

import joblib
import numpy as np

from config import config

logger = logging.getLogger(__name__)

# Module-level cache — we load the model once and reuse it
_model = None


def _load_model():
    """
    Load the serialised ML model from disk (lazy, cached).
    Returns the model object, or None if the file doesn't exist yet.
    """
    global _model

    if _model is not None:
        return _model  # Already loaded

    if os.path.exists(config.MODEL_PATH):
        try:
            _model = joblib.load(config.MODEL_PATH)
            logger.info("ML model loaded from %s", config.MODEL_PATH)
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            _model = None
    else:
        logger.warning(
            "Model file not found at '%s'. Using rule-based fallback.",
            config.MODEL_PATH
        )

    return _model


# Mapping from numeric label → human-readable risk string
_RISK_LABELS = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}


def predict_risk(features: Dict[str, Any]) -> str:
    """
    Predict the vulnerability risk level for a single endpoint.

    Args:
        features: Dict produced by utils/feature_extractor.py, e.g.:
            {
                "url_length": 45,
                "num_parameters": 2,
                "num_input_fields": 3,
                "response_size": 12800,
                "status_code": 200,
                "num_special_chars": 5,
                "has_forms": 1,
                "has_password_field": 0,
            }

    Returns:
        One of: "Low", "Medium", "High", "Critical"
    """
    model = _load_model()

    if model is not None:
        return _predict_with_model(model, features)
    else:
        return _rule_based_fallback(features)


def _predict_with_model(model, features: Dict[str, Any]) -> str:
    """Use the trained scikit-learn model to predict risk."""
    # The model expects a 2-D array; we build a single-row feature vector.
    # The feature order must match the training data — adjust if needed.
    feature_vector = np.array([[
        features.get("url_length",          0),
        features.get("num_parameters",      0),
        features.get("num_input_fields",    0),
        features.get("response_size",       0),
        features.get("status_code",         200),
        features.get("num_special_chars",   0),
        features.get("has_forms",           0),
        features.get("has_password_field",  0),
    ]])

    try:
        prediction: int = int(model.predict(feature_vector)[0])
        risk = _RISK_LABELS.get(prediction, "Medium")
        logger.debug("Model predicted risk=%s for features=%s", risk, features)
        return risk
    except Exception as exc:
        logger.error("Model prediction failed: %s. Falling back to heuristic.", exc)
        return _rule_based_fallback(features)


def _rule_based_fallback(features: Dict[str, Any]) -> str:
    """
    Simple heuristic used when no trained model is available.
    Score-based: accumulate risk points and bucket into a label.
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
