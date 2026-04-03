from __future__ import annotations

from http import HTTPStatus

from flask import Flask, jsonify, request
from flask_cors import CORS

from _lib.data_service import CommodityDataService
from _lib.model_service import CommodityModelService


data_service = CommodityDataService()
model_service = CommodityModelService(data_service=data_service)


def register_routes(app: Flask) -> None:
    route_prefixes = ("", "/api")

    for prefix in route_prefixes:
        app.add_url_rule(f"{prefix}/health", endpoint=f"health_{prefix or 'root'}", view_func=health_check, methods=["GET"])
        app.add_url_rule(f"{prefix}/get-history", endpoint=f"history_{prefix or 'root'}", view_func=get_history, methods=["GET"])
        app.add_url_rule(f"{prefix}/train-model", endpoint=f"train_{prefix or 'root'}", view_func=train_model, methods=["POST"])
        app.add_url_rule(f"{prefix}/predict", endpoint=f"predict_{prefix or 'root'}", view_func=predict, methods=["POST"])


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    CORS(app)
    register_routes(app)
    return app


def health_check():
    return jsonify({"status": "ok"})


def get_history():
    commodity = request.args.get("commodity", "onion")
    lookback_days = int(request.args.get("lookback_days", 60))
    history = data_service.get_history(commodity=commodity, lookback_days=lookback_days)
    metrics = model_service.get_latest_metrics(commodity=commodity)
    return jsonify(
        {
            "commodity": commodity,
            "history": history.to_dict(orient="records"),
            "metrics": metrics,
            "availableModels": model_service.available_model_types(commodity),
        }
    )


def train_model():
    payload = request.get_json(silent=True) or {}
    commodity = payload.get("commodity", "all")
    include_weather = bool(payload.get("include_weather", True))
    results = model_service.train_models(commodity=commodity, include_weather=include_weather)
    return jsonify(
        {
            "message": "Training complete",
            "commodity": commodity,
            "modelType": "random_forest",
            "results": results,
        }
    )


def predict():
    payload = request.get_json(silent=True) or {}
    commodity = payload.get("commodity", "onion")
    horizon_days = int(payload.get("horizon_days", 7))

    if horizon_days < 1 or horizon_days > 30:
        return jsonify({"error": "horizon_days must be between 1 and 30"}), HTTPStatus.BAD_REQUEST

    prediction_data = model_service.predict(
        commodity=commodity,
        horizon_days=horizon_days,
        model_type="random_forest",
    )
    return jsonify(prediction_data)


app = create_app()
