from flask import Flask, jsonify, request
from flask_cors import CORS

from _lib.data_service import CommodityDataService
from _lib.model_service import CommodityModelService

app = Flask(__name__)
CORS(app)

data_service = CommodityDataService()
model_service = CommodityModelService(data_service=data_service)


@app.route("/")
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
