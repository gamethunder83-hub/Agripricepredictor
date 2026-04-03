import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export function HistoryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="historyFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3f7d20" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#3f7d20" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#d9decd" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "#40513b", fontSize: 12 }} />
        <YAxis tick={{ fill: "#40513b", fontSize: 12 }} />
        <Tooltip />
        <Area type="monotone" dataKey="modal_price" stroke="#2b5a17" fill="url(#historyFill)" strokeWidth={3} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function ForecastChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data}>
        <CartesianGrid stroke="#eadfce" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "#6a5133", fontSize: 12 }} />
        <YAxis tick={{ fill: "#6a5133", fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="predicted_price" name="Predicted" stroke="#b76d2b" strokeWidth={3} dot={false} />
        <Line type="monotone" dataKey="lower_bound" name="Lower CI" stroke="#d4a373" strokeDasharray="4 4" dot={false} />
        <Line type="monotone" dataKey="upper_bound" name="Upper CI" stroke="#6d9773" strokeDasharray="4 4" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
