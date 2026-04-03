from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .data_service import COMMODITIES, CommodityDataService


class CommodityModelService:
    _model_cache: dict[str, dict[str, Any]] = {}

    def __init__(self, data_service: CommodityDataService) -> None:
        self.data_service = data_service

    @staticmethod
    def _feature_columns() -> list[str]:
        return [
            "arrivals_ton",
            "rainfall_mm",
            "temperature_c",
            "day_of_week",
            "month",
            "week_of_year",
            "lag_1",
            "lag_3",
            "lag_7",
            "rolling_mean_7",
            "rolling_mean_14",
            "rolling_std_7",
            "price_change_1",
            "price_change_7",
        ]

    def available_model_types(self, commodity: str) -> list[str]:
        return ["random_forest"]

    def _build_metrics(self, y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
        rmse = float(np.sqrt(mean_squared_error(y_true, predictions)))
        return {
            "mae": round(float(mean_absolute_error(y_true, predictions)), 2),
            "rmse": round(rmse, 2),
            "r2": round(float(r2_score(y_true, predictions)), 4),
        }

    def _train_random_forest(self, commodity: str, include_weather: bool = True) -> dict[str, Any]:
        frame = self.data_service.build_features(commodity, include_weather=include_weather)
        feature_columns = self._feature_columns()
        X = frame[feature_columns]
        y = frame["modal_price"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=14,
            min_samples_split=3,
            random_state=42,
        )
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        metrics = self._build_metrics(y_test, predictions)

        trained = {"model": model, "metrics": metrics, "feature_columns": feature_columns}
        self._model_cache[commodity] = trained
        return trained

    def train_models(self, commodity: str = "all", model_type: str = "random_forest", include_weather: bool = True) -> list[dict[str, Any]]:
        targets = COMMODITIES if commodity == "all" else (commodity,)
        results: list[dict[str, Any]] = []
        for commodity_name in targets:
            trained = self._train_random_forest(commodity_name, include_weather=include_weather)
            results.append(
                {
                    "commodity": commodity_name,
                    "modelType": "random_forest",
                    "metrics": trained["metrics"],
                }
            )
        return results

    def get_latest_metrics(self, commodity: str) -> dict[str, Any]:
        if commodity not in self._model_cache:
            return {"random_forest": None, "lstm": "Not available in Vercel deployment"}
        return {"random_forest": self._model_cache[commodity]["metrics"], "lstm": "Not available in Vercel deployment"}

    def predict(self, commodity: str, horizon_days: int, model_type: str = "random_forest") -> dict[str, Any]:
        if commodity not in self._model_cache:
            self._train_random_forest(commodity)

        trained = self._model_cache[commodity]
        model = trained["model"]
        feature_columns = trained["feature_columns"]
        metrics = trained["metrics"]

        commodity_frame = self.data_service.load_dataset()
        commodity_frame = commodity_frame[commodity_frame["commodity"] == commodity].copy().sort_values("date")
        base_history = commodity_frame[["date", "modal_price", "rainfall_mm", "temperature_c", "arrivals_ton"]].copy()
        forecast_rows = []

        for offset in range(1, horizon_days + 1):
            current_date = commodity_frame["date"].max() + pd.Timedelta(days=offset)
            rain_series = base_history["rainfall_mm"].tail(14)
            temp_series = base_history["temperature_c"].tail(14)
            arrival_series = base_history["arrivals_ton"].tail(14)
            price_series = base_history["modal_price"]

            feature_row = pd.DataFrame(
                [
                    {
                        "arrivals_ton": float(arrival_series.mean()),
                        "rainfall_mm": float(rain_series.mean()),
                        "temperature_c": float(temp_series.mean()),
                        "day_of_week": current_date.dayofweek,
                        "month": current_date.month,
                        "week_of_year": int(current_date.isocalendar().week),
                        "lag_1": float(price_series.iloc[-1]),
                        "lag_3": float(price_series.iloc[-3:].mean()),
                        "lag_7": float(price_series.iloc[-7:].mean()),
                        "rolling_mean_7": float(price_series.iloc[-7:].mean()),
                        "rolling_mean_14": float(price_series.iloc[-14:].mean()),
                        "rolling_std_7": float(price_series.iloc[-7:].std(ddof=0)),
                        "price_change_1": float(price_series.iloc[-1] - price_series.iloc[-2]),
                        "price_change_7": float(price_series.iloc[-1] - price_series.iloc[-7]),
                    }
                ]
            )[feature_columns]

            tree_predictions = np.array([tree.predict(feature_row)[0] for tree in model.estimators_])
            predicted_price = float(tree_predictions.mean())
            uncertainty = float(tree_predictions.std(ddof=0))

            forecast_rows.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "predicted_price": round(predicted_price, 2),
                    "lower_bound": round(predicted_price - (1.96 * uncertainty), 2),
                    "upper_bound": round(predicted_price + (1.96 * uncertainty), 2),
                }
            )

            next_history_row = {
                "date": current_date,
                "modal_price": predicted_price,
                "rainfall_mm": float(rain_series.mean()),
                "temperature_c": float(temp_series.mean()),
                "arrivals_ton": float(arrival_series.mean()),
            }
            base_history = pd.concat([base_history, pd.DataFrame([next_history_row])], ignore_index=True)

        latest_price = float(commodity_frame["modal_price"].iloc[-1])
        return {
            "commodity": commodity,
            "modelType": "random_forest",
            "horizonDays": horizon_days,
            "latestObservedPrice": round(latest_price, 2),
            "predictions": forecast_rows,
            "metrics": metrics,
        }
