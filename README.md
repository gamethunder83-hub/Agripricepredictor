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

## Dataset Format

The CSV file must contain:

```csv
date,price
2025-01-01,22.10
2025-01-02,22.40
```

- `date`: market date
- `price`: commodity price
- Prices should ideally be stored per kg
- If your source data is per quintal, set `PRICE_UNIT = "quintal"` inside `backend/train_model.py`

## How Training Works

The training script:
1. Loads the CSV dataset from `data/price_data.csv`
2. Cleans invalid rows
3. Converts the date into `month` and `day`
4. Creates:
   - `lag1_price`
   - `lag7_price`
5. Trains a `RandomForestRegressor`
6. Saves the trained model to `backend/model.pkl`
7. Saves training metrics to `backend/model_metadata.json`

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

This repository is now structured for a root-level Flask deployment on Vercel.

Vercel setup:

1. Import the GitHub repository
2. Set the Root Directory to the repository root
3. Keep the framework detection automatic
4. Deploy

Deployment notes:

- `app.py` at the project root is the Vercel Flask entrypoint
- `public/` contains the static dashboard files Vercel serves directly
- If `backend/model.pkl` is missing, the app auto-trains a Random Forest model in memory from `data/price_data.csv`
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
