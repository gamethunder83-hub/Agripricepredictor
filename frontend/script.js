const monthInput = document.getElementById("month");
const dayInput = document.getElementById("day");
const lag1Input = document.getElementById("lag1");
const lag7Input = document.getElementById("lag7");
const inputUnit = document.getElementById("inputUnit");
const predictBtn = document.getElementById("predictBtn");
const refreshHistoryBtn = document.getElementById("refreshHistory");
const result = document.getElementById("result");
const statusText = document.getElementById("status");
const historyList = document.getElementById("historyList");

async function loadHistory() {
  historyList.innerHTML = "";
  statusText.textContent = "Loading recent market history...";

  try {
    const response = await fetch("/api/history");
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Failed to fetch history.");
    }

    historyList.innerHTML = "";
    payload.history.forEach((entry) => {
      const row = document.createElement("article");
      row.className = "history-item";
      row.innerHTML = `
        <strong>${entry.date}</strong>
        <span>Price: Rs ${Number(entry.price).toFixed(2)} / kg</span>
      `;
      historyList.appendChild(row);
    });

    statusText.textContent = "History loaded. You can run a prediction now.";
  } catch (error) {
    statusText.textContent = error.message;
    historyList.innerHTML = `<article class="history-item"><span>${error.message}</span></article>`;
  }
}

async function predictPrice() {
  const payload = {
    month: Number(monthInput.value),
    day: Number(dayInput.value),
    lag1_price: Number(lag1Input.value),
    lag7_price: Number(lag7Input.value),
    input_unit: inputUnit.value,
  };

  const missingFields = [];
  if (!Number.isFinite(payload.month) || payload.month < 1 || payload.month > 12) {
    missingFields.push("month");
  }
  if (!Number.isFinite(payload.day) || payload.day < 1 || payload.day > 31) {
    missingFields.push("day");
  }
  if (!Number.isFinite(payload.lag1_price) || payload.lag1_price <= 0) {
    missingFields.push("yesterday price");
  }
  if (!Number.isFinite(payload.lag7_price) || payload.lag7_price <= 0) {
    missingFields.push("last week price");
  }

  if (missingFields.length > 0) {
    statusText.textContent = `Please check: ${missingFields.join(", ")}.`;
    return;
  }

  result.textContent = "...";
  statusText.textContent = "Generating prediction...";

  try {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Prediction failed.");
    }

    result.textContent = `Rs ${data.predicted_price_per_kg.toFixed(2)} / kg`;
    statusText.textContent = data.message;
  } catch (error) {
    result.textContent = "--";
    statusText.textContent = error.message;
  }
}

predictBtn.addEventListener("click", predictPrice);
refreshHistoryBtn.addEventListener("click", loadHistory);
window.addEventListener("DOMContentLoaded", () => {
  const today = new Date();
  if (!monthInput.value) monthInput.value = String(today.getMonth() + 1);
  if (!dayInput.value) dayInput.value = String(today.getDate());
  loadHistory();
});
