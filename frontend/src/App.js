import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [symbols, setSymbols] = useState("AAPL,MSFT,NVDA");
  const [start, setStart] = useState("2023-01-01");
  const [end, setEnd] = useState("2023-12-31");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runBacktest = async () => {
  setLoading(true);
  try {
    const response = await axios.get("http://localhost:8000/backtest", {
      params: {
        symbols: symbols, // send as string, e.g. "AAPL,MSFT,NVDA"
        start,
        end,
      },
    });
    setResult(response.data);
  } catch (err) {
    alert("Error fetching data");
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="App">
      <h1 style={{ fontSize: "3rem", marginBottom: "2rem" }}>
        Dispersion Options Strategy Backtester
      </h1>
      <div style={{ padding: "1rem" }}>
        <label>
          Symbols (comma separated):{" "}
          <input
            type="text"
            value={symbols}
            onChange={(e) => setSymbols(e.target.value)}
            style={{ width: "300px" }}
          />
        </label>
      </div>
      <div style={{ padding: "1rem" }}>
        <label>
          Start Date:{" "}
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
      </div>
      <div style={{ padding: "1rem" }}>
        <label>
          End Date:{" "}
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
      </div>
      <button onClick={runBacktest} disabled={loading} style={{ marginTop: 20 }}>
        {loading ? "Running Backtest..." : "Run Backtest"}
      </button>

      {result && (
        <div style={{ marginTop: 30 }}>
          <h3>Results:</h3>
          <p>Index Volatility: {result.index_vol.toFixed(4)}</p>
          <p>
            Component Volatilities:{" "}
            {result.component_vols.map((v, i) => (
              <span key={i}>{v.toFixed(4)} </span>
            ))}
          </p>
          <p>Dispersion: {result.dispersion.toFixed(4)}</p>
        </div>
      )}
    </div>
  );
}

export default App;
