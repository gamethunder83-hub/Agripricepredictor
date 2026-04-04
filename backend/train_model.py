import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_FILE = PROJECT_DIR / "data" / "price_data.csv"
MODEL_FILE = BASE_DIR / "model.pkl"
METADATA_FILE = BASE_DIR / "model_metadata.json"
PRICE_UNIT = "kg"  # Change to "quintal" if your dataset prices are rupees/quintal.


def convert_prices(df):
    if PRICE_UNIT == "quintal":
        df["price"] = df["price"] / 100.0
    return df


def load_dataset():
    df = pd.read_csv(DATA_FILE)
    required_columns = {"date", "price"}
    if not required_columns.issubset(df.columns):
        raise ValueError("Dataset must contain 'date' and 'price' columns.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)
    df = convert_prices(df)

    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["lag1_price"] = df["price"].shift(1)
    df["lag7_price"] = df["price"].shift(7)
    df = df.dropna().reset_index(drop=True)

    if len(df) < 15:
        raise ValueError("Dataset is too small after creating lag features. Add more rows.")

    return df


def build_model_bundle(save_artifacts=True):
    df = load_dataset()
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
    }

    bundle = {
        "model": model,
        "feature_columns": feature_columns,
        "price_unit": "kg",
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
