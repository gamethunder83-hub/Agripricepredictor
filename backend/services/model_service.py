from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from services.data_service import COMMODITIES, CommodityDataService

try:
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.models import Sequential, load_model

    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False


MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class CommodityModelService:
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

    def _rf_model_path(self, commodity: str) -> Path:
        return MODELS_DIR / f"{commodity}_random_forest.joblib"

    def _rf_meta_path(self, commodity: str) -> Path:
        return MODELS_DIR / f"{commodity}_random_forest_meta.joblib"

    def _lstm_model_path(self, commodity: str) -> Path:
        return MODELS_DIR / f"{commodity}_lstm.keras"

    def _lstm_meta_path(self, commodity: str) -> Path:
        return MODELS_DIR / f"{commodity}_lstm_meta.joblib"

    def available_model_types(self, commodity: str) -> list[str]:
        available = []
        if self._rf_model_path(commodity).exists():
            available.append("random_forest")
        if self._lstm_model_path(commodity).exists():
            available.append("lstm")
        return available or ["random_forest"]

    def get_latest_metrics(self, commodity: str) -> dict[str, Any]:
        meta_path = self._rf_meta_path(commodity)
        if not meta_path.exists():
            return {
                "random_forest": None,
                "lstm": None if TENSORFLOW_AVAILABLE else "TensorFlow unavailable",
            }

        rf_metrics = joblib.load(meta_path)["metrics"]
        lstm_meta = self._lstm_meta_path(commodity)
        lstm_metrics = joblib.load(lstm_meta)["metrics"] if lstm_meta.exists() else None
        if not TENSORFLOW_AVAILABLE and lstm_metrics is None:
            lstm_metrics = "TensorFlow unavailable"
        return {"random_forest": rf_metrics, "lstm": lstm_metrics}

    def train_models(self, commodity: str = "all", model_type: str = "both", include_weather: bool = True) -> list[dict[str, Any]]:
        targets = COMMODITIES if commodity == "all" else (commodity,)
        results: list[dict[str, Any]] = []

        for commodity_name in targets:
            frame = self.data_service.build_features(commodity_name, include_weather=include_weather)
            feature_columns = self._feature_columns()
            X = frame[feature_columns]
            y = frame["modal_price"]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

            if model_type in {"random_forest", "both"}:
                rf_model = RandomForestRegressor(
                    n_estimators=300,
                    max_depth=14,
                    min_samples_split=3,
                    random_state=42,
                )
                rf_model.fit(X_train, y_train)
                rf_predictions = rf_model.predict(X_test)
                rf_metrics = self._build_metrics(y_test, rf_predictions)
                joblib.dump(rf_model, self._rf_model_path(commodity_name))
                joblib.dump(
                    {"metrics": rf_metrics, "feature_columns": feature_columns},
                    self._rf_meta_path(commodity_name),
                )
                results.append(
                    {
                        "commodity": commodity_name,
                        "modelType": "random_forest",
                        "metrics": rf_metrics,
                    }
                )

            if model_type in {"lstm", "both"}:
                if TENSORFLOW_AVAILABLE:
                    lstm_metrics = self._train_lstm_model(frame=frame, commodity=commodity_name)
                    results.append(
                        {
                            "commodity": commodity_name,
                            "modelType": "lstm",
                            "metrics": lstm_metrics,
                        }
                    )
                else:
                    results.append(
                        {
                            "commodity": commodity_name,
                            "modelType": "lstm",
                            "skipped": True,
                            "reason": "TensorFlow is not installed in the environment.",
                        }
                    )

        return results

    def _build_metrics(self, y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
        rmse = float(np.sqrt(mean_squared_error(y_true, predictions)))
        return {
            "mae": round(float(mean_absolute_error(y_true, predictions)), 2),
            "rmse": round(rmse, 2),
            "r2": round(float(r2_score(y_true, predictions)), 4),
        }

    def _train_lstm_model(self, frame: pd.DataFrame, commodity: str) -> dict[str, float]:
        feature_columns = self._feature_columns()
        sequence_length = 14

        scaler_x = MinMaxScaler()
        scaler_y = MinMaxScaler()
        X_scaled = scaler_x.fit_transform(frame[feature_columns])
        y_scaled = scaler_y.fit_transform(frame[["modal_price"]])

        X_sequences = []
        y_sequences = []
        for index in range(sequence_length, len(frame)):
            X_sequences.append(X_scaled[index - sequence_length:index])
            y_sequences.append(y_scaled[index])

        X_seq = np.array(X_sequences)
        y_seq = np.array(y_sequences)
        split_index = int(len(X_seq) * 0.8)
        X_train, X_test = X_seq[:split_index], X_seq[split_index:]
        y_train, y_test = y_seq[:split_index], y_seq[split_index:]

        model = Sequential(
            [
                LSTM(64, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=False),
                Dense(32, activation="relu"),
                Dense(1),
            ]
        )
        model.compile(optimizer="adam", loss="mse")
        model.fit(X_train, y_train, epochs=20, batch_size=16, verbose=0)

        predictions = scaler_y.inverse_transform(model.predict(X_test, verbose=0)).flatten()
        actual = scaler_y.inverse_transform(y_test).flatten()
        metrics = self._build_metrics(pd.Series(actual), predictions)

        model.save(self._lstm_model_path(commodity))
        joblib.dump(
            {
                "metrics": metrics,
                "feature_columns": feature_columns,
                "sequence_length": sequence_length,
                "scaler_x": scaler_x,
                "scaler_y": scaler_y,
            },
            self._lstm_meta_path(commodity),
        )
        return metrics

    def predict(self, commodity: str, horizon_days: int, model_type: str = "random_forest") -> dict[str, Any]:
        if model_type == "lstm":
            if not TENSORFLOW_AVAILABLE or not self._lstm_model_path(commodity).exists():
                model_type = "random_forest"
            else:
                return self._predict_with_lstm(commodity=commodity, horizon_days=horizon_days)

        if not self._rf_model_path(commodity).exists():
            self.train_models(commodity=commodity, model_type="random_forest")

        return self._predict_with_random_forest(commodity=commodity, horizon_days=horizon_days)

    def _predict_with_random_forest(self, commodity: str, horizon_days: int) -> dict[str, Any]:
        model = joblib.load(self._rf_model_path(commodity))
        metadata = joblib.load(self._rf_meta_path(commodity))
        feature_columns = metadata["feature_columns"]
        metrics = metadata["metrics"]

        commodity_frame = self.data_service.load_dataset()
        commodity_frame = commodity_frame[commodity_frame["commodity"] == commodity].copy().sort_values("date")

        base_history = commodity_frame[["date", "modal_price", "rainfall_mm", "temperature_c", "arrivals_ton"]].copy()
        forecast_rows = []

        for offset in range(1, horizon_days + 1):
            current_date = commodity_frame["date"].max() + pd.Timedelta(days=offset)
            price_series = base_history["modal_price"]
            rain_series = base_history["rainfall_mm"].tail(14)
            temp_series = base_history["temperature_c"].tail(14)
            arrival_series = base_history["arrivals_ton"].tail(14)

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

    def _predict_with_lstm(self, commodity: str, horizon_days: int) -> dict[str, Any]:
        frame = self.data_service.build_features(commodity)
        metadata = joblib.load(self._lstm_meta_path(commodity))
        model = load_model(self._lstm_model_path(commodity))
        scaler_x = metadata["scaler_x"]
        scaler_y = metadata["scaler_y"]
        sequence_length = metadata["sequence_length"]
        feature_columns = metadata["feature_columns"]

        rolling_frame = frame.copy()
        forecast_rows = []

        for _ in range(horizon_days):
            sequence = rolling_frame[feature_columns].tail(sequence_length)
            scaled_sequence = scaler_x.transform(sequence)
            prediction_scaled = model.predict(np.array([scaled_sequence]), verbose=0)
            predicted_price = float(scaler_y.inverse_transform(prediction_scaled)[0][0])

            current_date = rolling_frame["date"].max() + pd.Timedelta(days=1)
            latest_row = rolling_frame.iloc[-1].copy()
            new_row = latest_row.copy()
            new_row["date"] = current_date
            new_row["modal_price"] = predicted_price
            new_row["day_of_week"] = current_date.dayofweek
            new_row["month"] = current_date.month
            new_row["week_of_year"] = int(current_date.isocalendar().week)
            new_row["lag_1"] = rolling_frame["modal_price"].iloc[-1]
            new_row["lag_3"] = rolling_frame["modal_price"].tail(3).mean()
            new_row["lag_7"] = rolling_frame["modal_price"].tail(7).mean()
            new_row["rolling_mean_7"] = rolling_frame["modal_price"].tail(7).mean()
            new_row["rolling_mean_14"] = rolling_frame["modal_price"].tail(14).mean()
            new_row["rolling_std_7"] = rolling_frame["modal_price"].tail(7).std(ddof=0)
            new_row["price_change_1"] = rolling_frame["modal_price"].iloc[-1] - rolling_frame["modal_price"].iloc[-2]
            new_row["price_change_7"] = rolling_frame["modal_price"].iloc[-1] - rolling_frame["modal_price"].iloc[-7]

            rolling_frame = pd.concat([rolling_frame, pd.DataFrame([new_row])], ignore_index=True)
            forecast_rows.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "predicted_price": round(predicted_price, 2),
                    "lower_bound": round(predicted_price * 0.97, 2),
                    "upper_bound": round(predicted_price * 1.03, 2),
                }
            )

        return {
            "commodity": commodity,
            "modelType": "lstm",
            "horizonDays": horizon_days,
            "latestObservedPrice": round(float(frame["modal_price"].iloc[-1]), 2),
            "predictions": forecast_rows,
            "metrics": metadata["metrics"],
        }
