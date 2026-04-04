import json
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, redirect, request, send_from_directory

try:
    from backend.data_utils import DEFAULT_COMMODITY, DEFAULT_DATA_FILE, prepare_price_dataset
    from backend.train_model import build_model_bundle
except ModuleNotFoundError:
    from data_utils import DEFAULT_COMMODITY, DEFAULT_DATA_FILE, prepare_price_dataset
    from train_model import build_model_bundle

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
PUBLIC_DIR = PROJECT_DIR / "public"
DATA_FILE = DEFAULT_DATA_FILE
MODEL_FILE = BASE_DIR / "model.pkl"
METADATA_FILE = BASE_DIR / "model_metadata.json"

app = Flask(__name__, static_folder=None)


def convert_price_to_kg(price, unit_hint=None):
    if unit_hint == "quintal":
        return round(float(price) / 100.0, 4)
    return round(float(price), 4)


def load_metadata():
    if not METADATA_FILE.exists():
        return None
    return json.loads(METADATA_FILE.read_text())


def static_dir():
    if PUBLIC_DIR.exists():
        return PUBLIC_DIR
    return FRONTEND_DIR


def load_model_bundle():
    if not MODEL_FILE.exists():
        bundle, metadata = build_model_bundle(save_artifacts=False)
        return bundle, metadata
    return joblib.load(MODEL_FILE), load_metadata()


def recent_history(limit=14):
    df, schema = prepare_price_dataset(data_file=DATA_FILE, commodity=DEFAULT_COMMODITY)
    tail = df.tail(limit).copy()
    tail["date"] = tail["date"].dt.strftime("%Y-%m-%d")
    rows = tail.to_dict(orient="records")
    return {"rows": rows, "schema": schema}


@app.get("/")
def index():
    return redirect("/index.html", code=307)


@app.get("/index.html")
def html():
    return send_from_directory(static_dir(), "index.html")


@app.get("/styles.css")
def styles():
    return send_from_directory(static_dir(), "styles.css")


@app.get("/script.js")
def script():
    return send_from_directory(static_dir(), "script.js")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model_ready": MODEL_FILE.exists()})


@app.get("/api/history")
def history():
    history_data = recent_history()
    return jsonify({"history": history_data["rows"], "source_schema": history_data["schema"]})


@app.post("/api/predict")
def predict():
    try:
        payload = request.get_json(force=True)
        month = int(payload.get("month"))
        day = int(payload.get("day"))
        lag1 = float(payload.get("lag1_price"))
        lag7 = float(payload.get("lag7_price"))
        input_unit = payload.get("input_unit", "kg")

        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")
        if day < 1 or day > 31:
            raise ValueError("Day must be between 1 and 31.")
        if lag1 <= 0 or lag7 <= 0:
            raise ValueError("Lag prices must be greater than zero.")

        bundle, metadata = load_model_bundle()
        model = bundle["model"]
        training_unit = bundle.get("price_unit", "kg")

        lag1_kg = convert_price_to_kg(lag1, input_unit)
        lag7_kg = convert_price_to_kg(lag7, input_unit)

        features = pd.DataFrame(
            [
                {
                    "month": month,
                    "day": day,
                    "lag1_price": lag1_kg,
                    "lag7_price": lag7_kg,
                }
            ]
        )
        prediction = float(model.predict(features)[0])

        return jsonify(
            {
                "predicted_price_per_kg": round(prediction, 2),
                "model_price_unit": training_unit,
                "message": "Prediction generated successfully.",
                "metadata": metadata,
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Unexpected server error: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
