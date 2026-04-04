from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_DIR / "data" / "price_data.csv"
DEFAULT_COMMODITY = "Onion"
PULSE_KEYWORDS = [
    "arhar",
    "bengal gram",
    "black gram",
    "gram",
    "green gram",
    "lentil",
    "masur",
    "moong",
    "pea",
    "peas",
    "pigeon pea",
    "pulses",
    "tur",
    "urd",
]


def normalize_columns(df):
    df = df.copy()
    df.columns = [column.strip().lower().replace(" ", "_") for column in df.columns]
    return df


def commodity_matcher(target):
    target = (target or "").strip().lower()

    def matches(value):
        current = str(value).strip().lower()
        if target == "pulses":
            return any(keyword in current for keyword in PULSE_KEYWORDS)
        return current == target

    return matches


def convert_quintal_to_kg(series):
    return pd.to_numeric(series, errors="coerce") / 100.0


def prepare_simple_dataset(df):
    if not {"date", "price"}.issubset(df.columns):
        raise ValueError("Simple dataset must contain 'date' and 'price' columns.")

    prepared = df[["date", "price"]].copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    prepared["price"] = pd.to_numeric(prepared["price"], errors="coerce")
    prepared = prepared.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)
    return prepared


def prepare_mandi_dataset(df, commodity=DEFAULT_COMMODITY, price_column="modal_price"):
    date_column = next(
        (column for column in ("arrival_date", "date") if column in df.columns),
        None,
    )
    if date_column is None:
        raise ValueError("Mandi dataset must contain 'Arrival_Date' or 'date'.")

    available_price_column = next(
        (column for column in (price_column, "modal_price", "max_price", "min_price") if column in df.columns),
        None,
    )
    if available_price_column is None:
        raise ValueError(
            "Mandi dataset must contain one of 'Modal_Price', 'Max_Price', or 'Min_Price'."
        )

    prepared = df.copy()

    if "commodity" in prepared.columns and commodity:
        matcher = commodity_matcher(commodity)
        prepared = prepared[prepared["commodity"].apply(matcher)]
        if prepared.empty:
            raise ValueError(f"No rows found for commodity '{commodity}'.")

    prepared["date"] = pd.to_datetime(prepared[date_column], errors="coerce")
    prepared["price"] = convert_quintal_to_kg(prepared[available_price_column])
    prepared = prepared.dropna(subset=["date", "price"]).sort_values("date").reset_index(drop=True)

    if "market" in prepared.columns:
        prepared = (
            prepared.groupby("date", as_index=False)["price"]
            .mean()
            .sort_values("date")
            .reset_index(drop=True)
        )
    else:
        prepared = prepared[["date", "price"]]

    return prepared


def prepare_price_dataset(
    data_file=DEFAULT_DATA_FILE,
    commodity=DEFAULT_COMMODITY,
    price_column="modal_price",
):
    df = pd.read_csv(data_file)
    normalized = normalize_columns(df)

    if {"date", "price"}.issubset(normalized.columns):
        prepared = prepare_simple_dataset(normalized)
        schema = "simple"
    else:
        prepared = prepare_mandi_dataset(
            normalized,
            commodity=commodity,
            price_column=price_column,
        )
        schema = "mandi"

    return prepared, schema
