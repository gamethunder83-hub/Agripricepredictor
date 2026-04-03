import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000",
  headers: {
    "Content-Type": "application/json"
  }
});

export async function fetchHistory(commodity, lookbackDays = 60) {
  const response = await api.get("/get-history", {
    params: { commodity, lookback_days: lookbackDays }
  });
  return response.data;
}

export async function trainModel(payload) {
  const response = await api.post("/train-model", payload);
  return response.data;
}

export async function predictCommodity(payload) {
  const response = await api.post("/predict", payload);
  return response.data;
}

export async function checkHealth() {
  const response = await api.get("/health");
  return response.data;
}
