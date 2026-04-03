from http import HTTPStatus

from flask import Flask, jsonify, request
from flask_cors import CORS

from _lib.data_service import CommodityDataService
from _lib.model_service import CommodityModelService

app = Flask(__name__)
CORS(app)

data_service = CommodityDataService()
model_service = CommodityModelService(data_service=data_service)


@app.route("/", methods=["POST"])
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
