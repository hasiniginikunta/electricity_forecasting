
from pathlib import Path
import json
import joblib
import pandas as pd

# Locate project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "Models"

# Load saved model and feature definitions
model = joblib.load(MODEL_DIR / "demand_model.pkl")

with open(MODEL_DIR / "demand_features.json", "r") as f:
    FEATURES = json.load(f)


def predict_demand(input_data):
    """
    Predict electricity demand from one row of prepared features.

    input_data must contain every feature used during model training.
    """
    missing = [feature for feature in FEATURES if feature not in input_data]

    if missing:
        raise ValueError(f"Missing required features: {missing}")

    X = pd.DataFrame(
        [[input_data[feature] for feature in FEATURES]],
        columns=FEATURES
    )

    prediction = float(model.predict(X)[0])

    return {
        "demand_forecast_mw": prediction
    }
