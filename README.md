# Commodity Price Prediction with Flask and Random Forest

This project is a lightweight agri-commodity price prediction system built with Flask, scikit-learn, and a simple HTML/CSS/JavaScript dashboard.

## Project Structure

```text
backend/
  app.py
  __init__.py
  train_model.py
  requirements.txt
frontend/
  index.html
  styles.css
  script.js
public/
  index.html
  styles.css
  script.js
app.py
requirements.txt
.python-version
vercel.json
data/
  agmarknet_sample.csv
  price_data.csv
README.md
```

## Features

- Flask backend with API endpoints for health, history, and prediction
- RandomForestRegressor model trained on:
  - `month`
  - `day`
  - `lag1_price`
  - `lag7_price`
- Dataset preprocessing:
  - `date` converted into `month` and `day`
  - lag features generated from the `price` column
- Optional quintal to kg conversion for user inputs
- Clean frontend dashboard with simple form-based prediction flow
- Basic error handling for invalid input and missing model files
- Vercel-ready root Flask entrypoint plus `public/` static assets
- Supports both:
  - simple CSVs with `date,price`
  - real mandi CSVs with Agmarknet-style fields such as `Arrival_Date`, `Commodity`, `Min_Price`, `Max_Price`, and `Modal_Price`

## Dataset Format

The app now supports two dataset styles.

### 1. Simple demo CSV

```csv
date,price
2025-01-01,22.10
2025-01-02,22.40
```

### 2. Real mandi / Agmarknet-style CSV

Common supported columns:

```text
State
District
Market
Commodity
Variety
Arrival_Date
Min_Price
Max_Price
Modal_Price
```

How it is handled:

- `Arrival_Date` becomes `date`
- `Modal_Price` is used as the target by default
- mandi prices are assumed to be in rupees per quintal
- the training pipeline converts them to rupees per kg by dividing by `100`
- rows are filtered to the selected commodity, then averaged by date when multiple markets exist

The official government mandi catalog confirms daily wholesale min, max, and modal prices from AGMARKNET:
- [Current daily price of various commodities from various markets (Mandi)](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi)
- [Resource page on data.gov.in](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)

This repo also includes a small mandi-style example file:
- `data/agmarknet_sample.csv`

## How Training Works

The training script:
1. Loads the CSV dataset from `data/price_data.csv`
2. Cleans invalid rows
3. Detects whether the file is:
   - a simple `date,price` dataset, or
   - a mandi-style dataset with `Arrival_Date` and `Modal_Price`
4. Converts mandi prices from quintal to kg when needed
5. Converts the date into `month` and `day`
6. Creates:
   - `lag1_price`
   - `lag7_price`
7. Trains a `RandomForestRegressor`
8. Saves the trained model to `backend/model.pkl`
9. Saves training metrics to `backend/model_metadata.json`

You can choose the target commodity with an environment variable before training:

```powershell
$env:TARGET_COMMODITY="Onion"
python backend/train_model.py
```

Examples:
- `Onion`
- `Potato`
- `Pulses`

You can also override the source file:

```powershell
$env:PRICE_DATA_FILE="data\\agmarknet_prices.csv"
python backend/train_model.py
```

## Run Locally

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

### 2. Install backend dependencies

```powershell
pip install -r backend/requirements.txt
```

### 3. Train the model

```powershell
python backend/train_model.py
```

This creates:
- `backend/model.pkl`
- `backend/model_metadata.json`

### 4. Start the Flask app

```powershell
python backend/app.py
```

### 5. Open the dashboard

Visit:

```text
http://127.0.0.1:5000/
```

## Deploy On Vercel

This repository is now structured for a Vercel Flask deployment from the repository root.

Vercel setup:

1. Import the GitHub repository
2. Set the Root Directory to the repository root
3. Keep the framework detection automatic
4. Deploy

Deployment notes:

- `app.py` at the project root is the Vercel Flask entrypoint
- `public/` contains the static dashboard files Vercel serves directly
- `vercel.json` includes an `experimentalServices` entry so Vercel can map the repo to a single root service
- If `backend/model.pkl` is missing, the app auto-trains a Random Forest model in memory from the configured CSV
- If you want a saved `model.pkl`, run `python backend/train_model.py` locally before deploying

## API Endpoints

### `GET /api/health`
Returns API status and whether the model is ready.

### `GET /api/history`
Returns the recent rows from the dataset.

### `POST /api/predict`
Request body:

```json
{
  "month": 4,
  "day": 10,
  "lag1_price": 28.5,
  "lag7_price": 27.8,
  "input_unit": "kg"
}
```

Response:

```json
{
  "predicted_price_per_kg": 29.14,
  "model_price_unit": "kg",
  "message": "Prediction generated successfully."
}
```

## Notes

- This repo is ready to push to GitHub.
- Vercel reads Python dependencies from the root `requirements.txt` and Python version from `.python-version`.
- The live Vercel app can still predict even without a committed `model.pkl`, because the backend auto-trains from the CSV when needed.
- If you want to retrain on another commodity, replace the CSV data and rerun the training script.
