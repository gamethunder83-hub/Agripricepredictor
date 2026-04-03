from flask import Flask, jsonify, request
from flask_cors import CORS

from _lib.data_service import CommodityDataService
from _lib.model_service import CommodityModelService

app = Flask(__name__)
CORS(app)

data_service = CommodityDataService()
model_service = CommodityModelService(data_service=data_service)


@app.route("/", methods=["POST"])
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
