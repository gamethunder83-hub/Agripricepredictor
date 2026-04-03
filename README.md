# AI-ML Based Price Prediction System for Agri-Horticultural Commodities

A full-stack web application that predicts future prices of onion, potato, and pulses using machine learning. The project combines a Flask REST API, feature-engineered forecasting models, and a React dashboard designed for farmer-friendly decision support.

## Project Structure

```text
.
|-- backend/
|   |-- api/
|   |-- data/
|   |-- services/
|   |-- utils/
|   |-- app.py
|   `-- requirements.txt
|-- frontend/
|   |-- public/
|   |-- src/
|   |-- package.json
|   `-- vercel.json
|-- models/
|-- screenshots/
|-- render.yaml
`-- README.md
```

## Features

- Predicts 7, 14, 21, or 30 days ahead for onion, potato, and pulses
- Random Forest Regression as the default production model
- Optional LSTM training when TensorFlow is available
- Historical trends, future forecasts, and confidence intervals
- REST API endpoints for model training, prediction, and price history
- Demo-ready synthetic dataset shaped like mandi/Agmarknet-style commodity data
- Clean dashboard built with React and Recharts

## Tech Stack

- Frontend: React, Vite, Axios, Recharts, Lucide React
- Backend: Flask, Flask-CORS, pandas, numpy, scikit-learn, TensorFlow, joblib
- Deployment:
  - Frontend: Vercel or Netlify
  - Backend: Render

## API Endpoints

- `GET /health`
- `GET /get-history?commodity=onion&lookback_days=60`
- `POST /train-model`
- `POST /predict`

## Sample prediction output

```json
{
  "commodity": "onion",
  "modelType": "random_forest",
  "horizonDays": 7,
  "latestObservedPrice": 2154.0,
  "predictions": [
    {
      "date": "2026-04-04",
      "predicted_price": 2161.48,
      "lower_bound": 2106.72,
      "upper_bound": 2216.24
    }
  ],
  "metrics": {
    "mae": 38.42,
    "rmse": 54.2,
    "r2": 0.9214
  }
}
```

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:5000` in `frontend/.env`.

## Deployment

### Backend on Render

- Use `backend` as the root directory
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

### Frontend on Vercel

- Set the project root to `frontend`
- Add environment variable `VITE_API_BASE_URL=<your-backend-url>`

## Notes

- Replace `backend/data/commodity_prices.csv` with real Agmarknet data for production.
- If the CSV is missing or too small, the backend auto-generates a larger synthetic demo dataset.
