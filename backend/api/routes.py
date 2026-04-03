from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from services.data_service import CommodityDataService
from services.model_service import CommodityModelService

api_bp = Blueprint("api", __name__)

data_service = CommodityDataService()
model_service = CommodityModelService(data_service=data_service)


@api_bp.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@api_bp.get("/get-history")
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


@api_bp.post("/train-model")
def train_model():
    payload = request.get_json(silent=True) or {}
    commodity = payload.get("commodity", "all")
    model_type = payload.get("model_type", "both")
    include_weather = bool(payload.get("include_weather", True))

    results = model_service.train_models(
        commodity=commodity,
        model_type=model_type,
        include_weather=include_weather,
    )
    return jsonify(
        {
            "message": "Training complete",
            "commodity": commodity,
            "modelType": model_type,
            "results": results,
        }
    )


@api_bp.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    commodity = payload.get("commodity", "onion")
    horizon_days = int(payload.get("horizon_days", 7))
    model_type = payload.get("model_type", "random_forest")

    if horizon_days < 1 or horizon_days > 30:
        return (
            jsonify({"error": "horizon_days must be between 1 and 30"}),
            HTTPStatus.BAD_REQUEST,
        )

    prediction = model_service.predict(
        commodity=commodity,
        horizon_days=horizon_days,
        model_type=model_type,
    )
    return jsonify(prediction)
