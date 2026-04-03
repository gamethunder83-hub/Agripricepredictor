import axios from "axios";

const externalApiBase = import.meta.env.VITE_API_BASE_URL || "";
const localApiPrefix = externalApiBase ? "" : "/api";

const api = axios.create({
  baseURL: externalApiBase,
  headers: {
    "Content-Type": "application/json"
  }
});

export async function fetchHistory(commodity, lookbackDays = 60) {
  const response = await api.get(`${localApiPrefix}/get-history`, {
    params: { commodity, lookback_days: lookbackDays }
  });
  return response.data;
}

export async function trainModel(payload) {
  const response = await api.post(`${localApiPrefix}/train-model`, payload);
  return response.data;
}

export async function predictCommodity(payload) {
  const response = await api.post(`${localApiPrefix}/predict`, payload);
  return response.data;
}

export async function checkHealth() {
  const response = await api.get(`${localApiPrefix}/health`);
  return response.data;
}
