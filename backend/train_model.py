import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from backend.data_utils import DEFAULT_COMMODITY, DEFAULT_DATA_FILE, prepare_price_dataset
except ModuleNotFoundError:
    from data_utils import DEFAULT_COMMODITY, DEFAULT_DATA_FILE, prepare_price_dataset

BASE_DIR = Path(__file__).resolve().parent
MODEL_FILE = BASE_DIR / "model.pkl"
METADATA_FILE = BASE_DIR / "model_metadata.json"
DATA_FILE = Path(os.getenv("PRICE_DATA_FILE", DEFAULT_DATA_FILE))
TARGET_COMMODITY = os.getenv("TARGET_COMMODITY", DEFAULT_COMMODITY)
TARGET_PRICE_COLUMN = os.getenv("TARGET_PRICE_COLUMN", "modal_price")

def load_dataset():
    df, schema = prepare_price_dataset(
        data_file=DATA_FILE,
        commodity=TARGET_COMMODITY,
        price_column=TARGET_PRICE_COLUMN,
    )

    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["lag1_price"] = df["price"].shift(1)
    df["lag7_price"] = df["price"].shift(7)
    df = df.dropna().reset_index(drop=True)

    if len(df) < 15:
        raise ValueError("Dataset is too small after creating lag features. Add more rows.")

    return df, schema


def build_model_bundle(save_artifacts=True):
    df, schema = load_dataset()
    feature_columns = ["month", "day", "lag1_price", "lag7_price"]
    X = df[feature_columns]
    y = df["price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        random_state=42,
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "r2": round(float(r2_score(y_test, predictions)), 4),
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "price_unit": "kg",
        "feature_columns": feature_columns,
        "source_schema": schema,
        "source_file": str(DATA_FILE),
        "commodity": TARGET_COMMODITY,
        "price_column": TARGET_PRICE_COLUMN,
    }

    bundle = {
        "model": model,
        "feature_columns": feature_columns,
        "price_unit": "kg",
        "source_schema": schema,
        "commodity": TARGET_COMMODITY,
        "price_column": TARGET_PRICE_COLUMN,
    }

    if save_artifacts:
        joblib.dump(bundle, MODEL_FILE)
        METADATA_FILE.write_text(json.dumps(metrics, indent=2))

    return bundle, metrics


def train_model():
    bundle, metrics = build_model_bundle(save_artifacts=True)

    print("Model trained successfully.")
    print(f"Saved model to: {MODEL_FILE}")
    print(json.dumps(metrics, indent=2))
    return bundle, metrics


if __name__ == "__main__":
    train_model()
