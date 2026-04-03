from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


COMMODITIES = ("onion", "potato", "pulses")
LOCAL_DATASET = Path(__file__).resolve().parents[3] / "backend" / "data" / "commodity_prices.csv"


@dataclass(frozen=True)
class CommodityProfile:
    base_price: float
    seasonal_amplitude: float
    trend: float
    weather_sensitivity: float


PROFILES = {
    "onion": CommodityProfile(2100, 320, 1.1, 4.0),
    "potato": CommodityProfile(1750, 180, 0.7, 2.5),
    "pulses": CommodityProfile(6200, 260, 1.8, 1.1),
}


class CommodityDataService:
    def __init__(self) -> None:
        self._cached_frame: pd.DataFrame | None = None

    def _generate_demo_dataset(self) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
        rows: list[dict] = []

        for commodity, profile in PROFILES.items():
            for index, current_date in enumerate(dates):
                day_of_year = current_date.timetuple().tm_yday
                seasonal_wave = np.sin((2 * np.pi * day_of_year) / 365)
                rainfall_mm = max(0, 28 + (12 * seasonal_wave) + rng.normal(0, 5))
                temperature_c = 26 + (7 * np.cos((2 * np.pi * day_of_year) / 365)) + rng.normal(0, 1.8)
                arrivals_ton = max(10, 90 - (0.6 * rainfall_mm) + rng.normal(0, 7))
                price = (
                    profile.base_price
                    + (profile.seasonal_amplitude * seasonal_wave)
                    + (profile.trend * index)
                    + (profile.weather_sensitivity * rainfall_mm)
                    - (2.2 * arrivals_ton)
                    + rng.normal(0, 45)
                )
                rows.append(
                    {
                        "date": current_date,
                        "commodity": commodity,
                        "modal_price": round(price, 2),
                        "arrivals_ton": round(arrivals_ton, 2),
                        "rainfall_mm": round(rainfall_mm, 2),
                        "temperature_c": round(temperature_c, 2),
                        "market": "Demo Agmarknet Market",
                    }
                )

        return pd.DataFrame(rows)

    def load_dataset(self) -> pd.DataFrame:
        if self._cached_frame is not None:
            return self._cached_frame.copy()

        if LOCAL_DATASET.exists():
            frame = pd.read_csv(LOCAL_DATASET)
            frame["date"] = pd.to_datetime(frame["date"])
            if len(frame) < 180:
                frame = self._generate_demo_dataset()
        else:
            frame = self._generate_demo_dataset()

        frame = frame.sort_values(["commodity", "date"]).reset_index(drop=True)
        self._cached_frame = frame
        return frame.copy()

    def get_history(self, commodity: str, lookback_days: int = 60) -> pd.DataFrame:
        frame = self.load_dataset()
        filtered = frame[frame["commodity"] == commodity].copy().tail(lookback_days)
        filtered["date"] = filtered["date"].dt.strftime("%Y-%m-%d")
        return filtered

    def available_commodities(self) -> Iterable[str]:
        return COMMODITIES

    def build_features(self, commodity: str, include_weather: bool = True) -> pd.DataFrame:
        frame = self.load_dataset()
        frame = frame[frame["commodity"] == commodity].copy().sort_values("date")

        frame["day_of_week"] = frame["date"].dt.dayofweek
        frame["month"] = frame["date"].dt.month
        frame["week_of_year"] = frame["date"].dt.isocalendar().week.astype(int)
        frame["lag_1"] = frame["modal_price"].shift(1)
        frame["lag_3"] = frame["modal_price"].shift(3)
        frame["lag_7"] = frame["modal_price"].shift(7)
        frame["rolling_mean_7"] = frame["modal_price"].rolling(window=7).mean()
        frame["rolling_mean_14"] = frame["modal_price"].rolling(window=14).mean()
        frame["rolling_std_7"] = frame["modal_price"].rolling(window=7).std()
        frame["price_change_1"] = frame["modal_price"].diff(1)
        frame["price_change_7"] = frame["modal_price"].diff(7)

        if not include_weather:
            frame["rainfall_mm"] = 0
            frame["temperature_c"] = 0

        return frame.dropna().reset_index(drop=True)
