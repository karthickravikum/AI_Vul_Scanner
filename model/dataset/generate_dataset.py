"""
dataset/generate_dataset.py
----------------------------
Generates a realistic synthetic dataset for training the vulnerability
risk classifier.

Each row represents one scanned web endpoint. Feature values are drawn
from distributions that reflect real-world observations:
  - Low-risk endpoints have short URLs, few parameters, small responses.
  - Critical endpoints have many parameters, password fields, large bodies,
    and error-level status codes.

Output: vulnerability_dataset.csv  (saved in the same directory)

Run directly:
    python dataset/generate_dataset.py
"""

import os
import numpy as np
import pandas as pd

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
RNG  = np.random.default_rng(SEED)

# ── Dataset size ─────────────────────────────────────────────────────────────
N_SAMPLES = 1200

# ── Risk level distribution (roughly realistic) ──────────────────────────────
RISK_DIST = {
    "Low":      0.30,
    "Medium":   0.30,
    "High":     0.25,
    "Critical": 0.15,
}


def _generate_for_risk(label: str, n: int) -> pd.DataFrame:
    """
    Generate `n` synthetic endpoint rows for a given risk label.
    Each risk class has distinct feature distributions to make the
    classification task meaningful.
    """
    rows = []

    for _ in range(n):
        if label == "Low":
            url_length         = int(RNG.integers(10, 40))
            parameter_count    = int(RNG.integers(0, 2))
            form_present       = int(RNG.random() < 0.15)
            input_fields       = int(RNG.integers(0, 2)) if form_present else 0
            special_characters = int(RNG.integers(0, 3))
            response_size      = int(RNG.integers(500, 8_000))
            status_code        = RNG.choice([200, 301, 304], p=[0.85, 0.10, 0.05])
            endpoint_depth     = int(RNG.integers(1, 3))

        elif label == "Medium":
            url_length         = int(RNG.integers(30, 70))
            parameter_count    = int(RNG.integers(1, 4))
            form_present       = int(RNG.random() < 0.45)
            input_fields       = int(RNG.integers(1, 4)) if form_present else 0
            special_characters = int(RNG.integers(2, 6))
            response_size      = int(RNG.integers(5_000, 20_000))
            status_code        = RNG.choice([200, 400, 403], p=[0.75, 0.15, 0.10])
            endpoint_depth     = int(RNG.integers(2, 4))

        elif label == "High":
            url_length         = int(RNG.integers(60, 120))
            parameter_count    = int(RNG.integers(3, 8))
            form_present       = int(RNG.random() < 0.70)
            input_fields       = int(RNG.integers(3, 7)) if form_present else 0
            special_characters = int(RNG.integers(5, 12))
            response_size      = int(RNG.integers(15_000, 60_000))
            status_code        = RNG.choice([200, 500, 403, 400], p=[0.55, 0.20, 0.15, 0.10])
            endpoint_depth     = int(RNG.integers(3, 6))

        else:  # Critical
            url_length         = int(RNG.integers(100, 200))
            parameter_count    = int(RNG.integers(6, 15))
            form_present       = int(RNG.random() < 0.85)
            input_fields       = int(RNG.integers(5, 12)) if form_present else 0
            special_characters = int(RNG.integers(10, 25))
            response_size      = int(RNG.integers(40_000, 150_000))
            status_code        = RNG.choice([200, 500, 400, 403], p=[0.40, 0.30, 0.20, 0.10])
            endpoint_depth     = int(RNG.integers(4, 8))

        rows.append({
            "url_length":         url_length,
            "parameter_count":    parameter_count,
            "form_present":       form_present,
            "input_fields":       input_fields,
            "special_characters": special_characters,
            "response_size":      response_size,
            "status_code":        int(status_code),
            "endpoint_depth":     endpoint_depth,
            "risk_level":         label,
        })

    return pd.DataFrame(rows)


def generate_dataset(n_samples: int = N_SAMPLES, output_path: str | None = None) -> pd.DataFrame:
    """
    Build and return the full synthetic dataset.

    Args:
        n_samples:   Total number of rows to generate.
        output_path: If given, the CSV is saved to this path.

    Returns:
        A pandas DataFrame with all rows shuffled.
    """
    parts = []
    for label, fraction in RISK_DIST.items():
        count = max(1, int(n_samples * fraction))
        parts.append(_generate_for_risk(label, count))

    df = pd.concat(parts, ignore_index=True)
    # Shuffle so classes aren't grouped together
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"[dataset] Saved {len(df)} rows → {output_path}")

    return df


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out  = os.path.join(here, "vulnerability_dataset.csv")
    df   = generate_dataset(N_SAMPLES, output_path=out)

    print("\nClass distribution:")
    print(df["risk_level"].value_counts().to_string())
    print(f"\nShape: {df.shape}")
    print("\nSample rows:")
    print(df.head(6).to_string(index=False))
