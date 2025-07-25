from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from .backtester import run_dispersion_backtest

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # For dev/testing; restrict in prod for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STOCK_API_KEY = "qKpnAGCOOWHnsxX4ZvZUZCpKFBKllLuO"
OPTION_API_KEY = "2OLjrA2D9B53VeTFvoZGfLvYWH1LJ5N0"
EXPIRY = "2025-12-19"
CONTRACT_TYPE = "call"
SPY_STRIKE = 650

# Use option key for backtester
API_KEY = OPTION_API_KEY

class BacktestRequest(BaseModel):
    weights: Dict[str, float]
    start: str  
    end: str
    total_notional: float = 1_000_000
    vega_hedge: Optional[float] = 0.02  # Add this optional param with default


@app.post("/backtest")
def backtest(req: BacktestRequest):
    try:
        start_date = datetime.strptime(req.start, "%Y-%m-%d")
        end_date = datetime.strptime(req.end, "%Y-%m-%d")
    except Exception as e:
        return {"error": f"Invalid date format: {e}"}

    result = run_dispersion_backtest(
         OPTION_API_KEY,
         req.weights,
         req.total_notional,
         EXPIRY,
         CONTRACT_TYPE,  # unused inside run_dispersion_backtest but kept for positional arg
         start_date,
         end_date,
         req.vega_hedge,  # use vega_hedge from request here
         SPY_STRIKE,
    )

    if result is None:
        return {"error": "Backtest failed or no data."}

    result["weights"] = req.weights
    return result
