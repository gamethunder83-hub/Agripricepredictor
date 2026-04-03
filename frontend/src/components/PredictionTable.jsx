export default function PredictionTable({ predictions }) {
  return (
    <div className="table-shell">
      <table className="prediction-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Predicted Price</th>
            <th>Lower Bound</th>
            <th>Upper Bound</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((row) => (
            <tr key={row.date}>
              <td>{row.date}</td>
              <td>Rs. {row.predicted_price}</td>
              <td>Rs. {row.lower_bound}</td>
              <td>Rs. {row.upper_bound}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
