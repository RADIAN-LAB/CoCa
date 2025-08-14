"""Capacity prediction utility migrated from original project.

The model file and sample CSV are expected under `models/files/` relative to the project root.
"""
from pathlib import Path
import pickle
from typing import List

import pandas as pd
from xgboost import XGBRegressor  # type: ignore

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
MODULE_DIR = Path(__file__).resolve().parent
FILES_DIR = MODULE_DIR / "files"
MODEL_PATH = FILES_DIR / "capacity_model.pkl"
SAMPLE_CSV = FILES_DIR / "capacity_sample.csv"

# ---------------------------------------------------------------------
# Load model once at import time (small file, acceptable)
# ---------------------------------------------------------------------
if MODEL_PATH.exists():
    with MODEL_PATH.open("rb") as fh:
        _MODEL: XGBRegressor = pickle.load(fh)
else:
    raise FileNotFoundError(
        f"Capacity model not found at {MODEL_PATH}. Please ensure the file is copied into the new structure."
    )

pd.set_option("display.max_columns", None)

def predict_capacity() -> List[int]:
    """Return a list of predicted capacities for each region (placeholder logic)."""
    df = pd.read_csv(SAMPLE_CSV)
    X = df.drop(["occupancy"], axis=1)
    y_pred = _MODEL.predict(X)
    return [int(x) - 40 for x in y_pred]

__all__ = ["predict_capacity"]
