import axios from "axios";
import {
  demoCheckHealth,
  demoFetchHistory,
  demoPredictCommodity,
  demoTrainModel
} from "./demoApi";

const externalApiBase = import.meta.env.VITE_API_BASE_URL || "";
const localApiPrefix = externalApiBase ? "" : "/api";

const api = axios.create({
  baseURL: externalApiBase,
  headers: {
    "Content-Type": "application/json"
  }
});

function isHtmlShell(payload) {
  return typeof payload === "string" && payload.toLowerCase().includes("<!doctype html");
}

async function withDemoFallback(requestFn, fallbackFn) {
  try {
    const response = await requestFn();
    if (isHtmlShell(response?.data)) {
      return fallbackFn();
    }
    return response.data;
  } catch {
    return fallbackFn();
  }
}

export async function fetchHistory(commodity, lookbackDays = 60) {
  return withDemoFallback(
    () =>
      api.get(`${localApiPrefix}/get-history`, {
        params: { commodity, lookback_days: lookbackDays }
      }),
    () => demoFetchHistory(commodity, lookbackDays)
  );
}

export async function trainModel(payload) {
  return withDemoFallback(
    () => api.post(`${localApiPrefix}/train-model`, payload),
    () => demoTrainModel(payload)
  );
}

export async function predictCommodity(payload) {
  return withDemoFallback(
    () => api.post(`${localApiPrefix}/predict`, payload),
    () => demoPredictCommodity(payload)
  );
}

export async function checkHealth() {
  return withDemoFallback(
    () => api.get(`${localApiPrefix}/health`),
    () => demoCheckHealth()
  );
}
