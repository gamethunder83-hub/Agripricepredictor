import { useEffect, useMemo, useState } from "react";
import { CloudSun, Cpu, Leaf, RefreshCw, TrendingUp } from "lucide-react";

import SummaryCard from "./components/SummaryCard";
import PredictionTable from "./components/PredictionTable";
import { ForecastChart, HistoryChart } from "./components/TrendChart";
import { checkHealth, fetchHistory, predictCommodity, trainModel } from "./services/api";

const commodityOptions = [
  { value: "onion", label: "Onion" },
  { value: "potato", label: "Potato" },
  { value: "pulses", label: "Pulses" }
];

const modelOptions = [
  { value: "random_forest", label: "Random Forest" },
  { value: "lstm", label: "LSTM" }
];

export default function App() {
  const [commodity, setCommodity] = useState("onion");
  const [modelType, setModelType] = useState("random_forest");
  const [horizonDays, setHorizonDays] = useState(7);
  const [historyPayload, setHistoryPayload] = useState({ history: [], metrics: {} });
  const [predictionPayload, setPredictionPayload] = useState({ predictions: [], metrics: {} });
  const [health, setHealth] = useState("checking");
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [message, setMessage] = useState("Load historical data to begin forecasting.");

  const latestHistoryPoint = historyPayload.history.at(-1);
  const lastPrediction = predictionPayload.predictions.at(-1);

  const trendDelta = useMemo(() => {
    if (!latestHistoryPoint || !lastPrediction) return "--";
    const change = lastPrediction.predicted_price - latestHistoryPoint.modal_price;
    const pct = (change / latestHistoryPoint.modal_price) * 100;
    return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
  }, [latestHistoryPoint, lastPrediction]);

  async function loadDashboardData(selectedCommodity = commodity, selectedModel = modelType, selectedHorizon = horizonDays) {
    setLoading(true);
    try {
      const [history, prediction] = await Promise.all([
        fetchHistory(selectedCommodity),
        predictCommodity({ commodity: selectedCommodity, model_type: selectedModel, horizon_days: selectedHorizon })
      ]);
      setHistoryPayload(history);
      setPredictionPayload(prediction);
      setMessage(`Showing ${selectedHorizon}-day ${selectedModel.replace("_", " ")} forecast for ${selectedCommodity}.`);
    } catch (error) {
      setMessage(error?.response?.data?.error || "Unable to connect to the API. Start the Flask backend first.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        await checkHealth();
        setHealth("online");
      } catch {
        setHealth("offline");
      }
    }
    bootstrap();
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [commodity, modelType, horizonDays]);

  async function handleTraining() {
    setTraining(true);
    try {
      const response = await trainModel({ commodity, model_type: modelType === "lstm" ? "both" : modelType });
      setMessage(`${response.message}. Refreshed ${commodity} models successfully.`);
      await loadDashboardData();
    } catch (error) {
      setMessage(error?.response?.data?.error || "Training failed. Check backend logs.");
    } finally {
      setTraining(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">AI-ML Commodity Forecasting</span>
          <h1>AgriCast AI price prediction dashboard for onions, potatoes, and pulses.</h1>
          <p>
            A farmer-friendly forecasting workspace powered by feature-engineered commodity history,
            weather-aware signals, Random Forest regression, and optional LSTM modeling.
          </p>
          <div className="hero-badges">
            <span className={`status-badge ${health}`}>API {health}</span>
            <span className="status-badge neutral">Forecast horizon: {horizonDays} days</span>
            <span className="status-badge neutral">Market: Demo Agmarknet Market</span>
          </div>
        </div>

        <div className="hero-card">
          <div className="hero-card-row"><Leaf size={18} /><span>Commodity signals + seasonality</span></div>
          <div className="hero-card-row"><CloudSun size={18} /><span>Weather-aware forecasting input</span></div>
          <div className="hero-card-row"><Cpu size={18} /><span>Trainable Random Forest and LSTM models</span></div>
          <div className="hero-card-row"><TrendingUp size={18} /><span>Confidence interval for decision support</span></div>
        </div>
      </header>

      <section className="control-panel">
        <div className="field-group">
          <label>Commodity</label>
          <select value={commodity} onChange={(event) => setCommodity(event.target.value)}>
            {commodityOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label>Model</label>
          <select value={modelType} onChange={(event) => setModelType(event.target.value)}>
            {modelOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label>Forecast window</label>
          <select value={horizonDays} onChange={(event) => setHorizonDays(Number(event.target.value))}>
            {[7, 14, 21, 30].map((days) => <option key={days} value={days}>{days} days</option>)}
          </select>
        </div>
        <button className="primary-button" onClick={() => loadDashboardData()}><RefreshCw size={16} />Refresh forecast</button>
        <button className="secondary-button" onClick={handleTraining} disabled={training}>{training ? "Training..." : "Train model"}</button>
      </section>

      <section className="summary-grid">
        <SummaryCard label="Latest observed price" value={latestHistoryPoint ? `Rs. ${latestHistoryPoint.modal_price}` : "--"} hint="Most recent market modal price" />
        <SummaryCard label="Forecast end price" value={lastPrediction ? `Rs. ${lastPrediction.predicted_price}` : "--"} hint={`${horizonDays}-day forecasted terminal price`} accent="grain" />
        <SummaryCard label="Expected movement" value={trendDelta} hint="Relative change from latest observed price" accent="soil" />
        <SummaryCard label="Model accuracy" value={predictionPayload.metrics?.rmse ? `RMSE ${predictionPayload.metrics.rmse}` : "Pending"} hint="Latest saved training metric" accent="sky" />
      </section>

      <section className="chart-grid">
        <article className="panel">
          <div className="panel-header"><div><span className="panel-kicker">Historical market trend</span><h2>Past price movement</h2></div><span className="panel-chip">{loading ? "Loading" : "Updated"}</span></div>
          <HistoryChart data={historyPayload.history} />
        </article>
        <article className="panel warm">
          <div className="panel-header"><div><span className="panel-kicker">Projected trajectory</span><h2>Future price forecast</h2></div><span className="panel-chip">{modelType.replace("_", " ")}</span></div>
          <ForecastChart data={predictionPayload.predictions} />
        </article>
      </section>

      <section className="lower-grid">
        <article className="panel">
          <div className="panel-header"><div><span className="panel-kicker">Prediction table</span><h2>Day-wise forecast output</h2></div></div>
          <PredictionTable predictions={predictionPayload.predictions} />
        </article>
        <article className="panel notes-panel">
          <div className="panel-header"><div><span className="panel-kicker">System insight</span><h2>Current dashboard status</h2></div></div>
          <p className="message-box">{message}</p>
          <div className="metric-list">
            <div><span>MAE</span><strong>{predictionPayload.metrics?.mae || "--"}</strong></div>
            <div><span>RMSE</span><strong>{predictionPayload.metrics?.rmse || "--"}</strong></div>
            <div><span>R2</span><strong>{predictionPayload.metrics?.r2 || "--"}</strong></div>
          </div>
          <ul className="bullet-list">
            <li>Use 7-day forecasts for market timing and short-term planning.</li>
            <li>Use 30-day forecasts for inventory, procurement, and crop sale strategy.</li>
            <li>Train models again after uploading fresher Agmarknet or mandi data.</li>
          </ul>
        </article>
      </section>
    </div>
  );
}
