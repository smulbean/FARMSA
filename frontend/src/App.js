import React, { useState } from "react";
import axios from "axios";
import "./App.css";

const defaultWeights = [
  { ticker: "LIN", weight: 0.081693 },
  { ticker: "AAPL", weight: 0.080473 },
  { ticker: "MSFT", weight: 0.073996 },
  { ticker: "NVDA", weight: 0.067715 },
  { ticker: "V", weight: 0.056792 },
  { ticker: "BLK", weight: 0.036357 },
  { ticker: "TXT", weight: 0.033638 },
  { ticker: "CSCO", weight: 0.033197 },
  { ticker: "MCO", weight: 0.03317 },
  { ticker: "GS", weight: 0.031993 },
  { ticker: "BSX", weight: 0.031509 },
  { ticker: "SYK", weight: 0.030046 },
  { ticker: "AMZN", weight: 0.025986 },
  { ticker: "GOOG", weight: 0.024412 },
  { ticker: "TSLA", weight: 0.023955 },
  { ticker: "CMI", weight: 0.022742 },
  { ticker: "IT", weight: 0.022477 },
  { ticker: "META", weight: 0.022473 },
  { ticker: "NDAQ", weight: 0.021076 },
  { ticker: "PRU", weight: 0.018877 },
  { ticker: "QCOM", weight: 0.01843 },
  { ticker: "HLT", weight: 0.017915 },
  { ticker: "GEHC", weight: 0.017651 },
  { ticker: "AVGO", weight: 0.016904 },
  { ticker: "TT", weight: 0.016903 },
  { ticker: "DD", weight: 0.015875 },
  { ticker: "BK", weight: 0.01489 },
  { ticker: "PANW", weight: 0.014594 },
  { ticker: "TROW", weight: 0.014045 },
  { ticker: "ORCL", weight: 0.012855 },
  { ticker: "CPAY", weight: 0.010753 },
  { ticker: "AMD", weight: 0.010065 },
  { ticker: "GE", weight: 0.00982 },
  { ticker: "KLAC", weight: 0.008895 },
  { ticker: "PFG", weight: 0.007557 },
  { ticker: "JCI", weight: 0.007214 },
  { ticker: "EMR", weight: 0.007132 },
  { ticker: "PTC", weight: 0.006235 },
  { ticker: "TEL", weight: 0.005727 },
  { ticker: "XYL", weight: 0.005382 },
  { ticker: "ADI", weight: 0.002533 },
  { ticker: "MS", weight: 0.002515 },
  { ticker: "APH", weight: 0.002222 },
  { ticker: "ISRG", weight: 0.001165 },
  { ticker: "DOV", weight: 0.000016 },
  { ticker: "APO", weight: -0.000427 },
  { ticker: "AXP", weight: -0.002341 },
  { ticker: "BX", weight: -0.00242 },
  { ticker: "WAB", weight: -0.003527 },
  { ticker: "PH", weight: -0.011154 }
];

function App() {
  const [symbols, setSymbols] = useState("AAPL,MSFT,NVDA");
  const [start, setStart] = useState("2023-01-01");
  const [end, setEnd] = useState("2023-12-31");
  const [vegaHedge, setVegaHedge] = useState(0);
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
        vega_hedge: parseFloat(vegaHedge) || 0,
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
      <h1 className="title">Dispersion Options Strategy Backtester</h1>

      <div className="main-row">
        {/* --- Form column --- */}
        <div className="form-column">
          <div className="form-group">
            <label htmlFor="startDate">Start Date:</label>
            <input
              id="startDate"
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="endDate">End Date:</label>
            <input
              id="endDate"
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="vegaHedge">Vega Hedge (%):</label>
            <input
              id="vegaHedge"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={vegaHedge}
              onChange={(e) => setVegaHedge(e.target.value)}
              className="input"
            />
          </div>
          <button onClick={runBacktest} disabled={loading} className="primary-button">
            {loading ? "Running Backtest..." : "Run Backtest"}
          </button>
        </div>

        {/* --- Weights table column --- */}
        <div className="weights-container">
          <h3>Selected Stocks & Weights</h3>
          <table className="weights-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Weight</th>
              </tr>
            </thead>
            <tbody>
              {(
                result && result.weights
                  ? Object.entries(result.weights)
                      .sort((a, b) => b[1] - a[1])
                      .map(([ticker, weight]) => ({ ticker, weight }))
                  : defaultWeights
              ).map(({ ticker, weight }) => (
                <tr key={ticker}>
                  <td>{ticker}</td>
                  <td>{(weight * 100).toFixed(4)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Results below */}
      {result && (
        <div className="results results-below">
          <h3>Results:</h3>
          <p>Index Volatility: {result.index_vol.toFixed(4)}</p>
          <p>
            Component Volatilities: {" "}
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
