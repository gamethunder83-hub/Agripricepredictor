const COMMODITY_PROFILES = {
  onion: { basePrice: 2100, seasonalAmplitude: 320, trend: 1.1, weatherSensitivity: 4.0 },
  potato: { basePrice: 1750, seasonalAmplitude: 180, trend: 0.7, weatherSensitivity: 2.5 },
  pulses: { basePrice: 6200, seasonalAmplitude: 260, trend: 1.8, weatherSensitivity: 1.1 }
};

const MODEL_METRICS = {
  onion: { mae: 38.42, rmse: 54.2, r2: 0.9214 },
  potato: { mae: 28.35, rmse: 41.8, r2: 0.9071 },
  pulses: { mae: 52.11, rmse: 73.6, r2: 0.8942 }
};

function deterministicNoise(seed) {
  return Math.sin(seed * 12.9898) * 43.5453;
}

function round(value) {
  return Number(value.toFixed(2));
}

function generateHistorySeries(commodity, totalDays = 220) {
  const profile = COMMODITY_PROFILES[commodity] || COMMODITY_PROFILES.onion;
  const startDate = new Date("2025-09-01T00:00:00Z");
  const rows = [];

  for (let index = 0; index < totalDays; index += 1) {
    const currentDate = new Date(startDate);
    currentDate.setUTCDate(startDate.getUTCDate() + index);

    const seasonalWave = Math.sin((2 * Math.PI * ((index % 365) + 1)) / 365);
    const rainfall = Math.max(0, 28 + (12 * seasonalWave) + (deterministicNoise(index + 3) % 5));
    const temperature = 26 + (7 * Math.cos((2 * Math.PI * ((index % 365) + 1)) / 365)) + ((deterministicNoise(index + 7) % 2) - 1);
    const arrivals = Math.max(10, 90 - (0.6 * rainfall) + (deterministicNoise(index + 11) % 8));
    const price =
      profile.basePrice +
      (profile.seasonalAmplitude * seasonalWave) +
      (profile.trend * index) +
      (profile.weatherSensitivity * rainfall) -
      (2.2 * arrivals) +
      (deterministicNoise(index + 17) % 40);

    rows.push({
      date: currentDate.toISOString().slice(0, 10),
      commodity,
      modal_price: round(price),
      arrivals_ton: round(arrivals),
      rainfall_mm: round(rainfall),
      temperature_c: round(temperature),
      market: "Demo Agmarknet Market"
    });
  }

  return rows;
}

function getMetrics(commodity) {
  return {
    random_forest: MODEL_METRICS[commodity] || MODEL_METRICS.onion,
    lstm: "Demo-only in live fallback mode"
  };
}

function buildForecast(commodity, horizonDays) {
  const history = generateHistorySeries(commodity, 220);
  const recentHistory = history.slice(-14);
  const latestObservedPrice = recentHistory[recentHistory.length - 1].modal_price;
  const profile = COMMODITY_PROFILES[commodity] || COMMODITY_PROFILES.onion;
  const predictions = [];

  for (let offset = 1; offset <= horizonDays; offset += 1) {
    const anchor = recentHistory[recentHistory.length - 1];
    const recentAverage = recentHistory.reduce((sum, row) => sum + row.modal_price, 0) / recentHistory.length;
    const seasonalBump = Math.sin((2 * Math.PI * (offset + 90)) / 30) * (profile.seasonalAmplitude * 0.12);
    const predictedPrice = recentAverage + seasonalBump + (profile.trend * offset * 5);
    const uncertainty = 42 + (offset * 4);
    const forecastDate = new Date(`${anchor.date}T00:00:00Z`);
    forecastDate.setUTCDate(forecastDate.getUTCDate() + offset);

    predictions.push({
      date: forecastDate.toISOString().slice(0, 10),
      predicted_price: round(predictedPrice),
      lower_bound: round(predictedPrice - uncertainty),
      upper_bound: round(predictedPrice + uncertainty)
    });
  }

  return {
    commodity,
    modelType: "random_forest",
    horizonDays,
    latestObservedPrice,
    predictions,
    metrics: MODEL_METRICS[commodity] || MODEL_METRICS.onion
  };
}

export async function demoCheckHealth() {
  return { status: "ok", mode: "demo-fallback" };
}

export async function demoFetchHistory(commodity, lookbackDays = 60) {
  const history = generateHistorySeries(commodity).slice(-lookbackDays);
  return {
    commodity,
    history,
    metrics: getMetrics(commodity),
    availableModels: ["random_forest", "lstm"]
  };
}

export async function demoTrainModel(payload = {}) {
  const commodity = payload.commodity || "all";
  const targets = commodity === "all" ? Object.keys(COMMODITY_PROFILES) : [commodity];
  return {
    message: "Training complete (demo fallback)",
    commodity,
    modelType: "random_forest",
    results: targets.map((name) => ({
      commodity: name,
      modelType: "random_forest",
      metrics: MODEL_METRICS[name]
    }))
  };
}

export async function demoPredictCommodity(payload = {}) {
  return buildForecast(payload.commodity || "onion", Number(payload.horizon_days || 7));
}
