# backend/main.py
from fastapi import FastAPI, Query
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from backtester import run_dispersion_strategy

app = FastAPI()

# Allow CORS from your frontend origin (adjust URL as needed)
origins = [
    "http://localhost:3000",  # React dev server default port]
    "http://localhost:5080",  
    # add your deployed frontend URL here if applicable
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allow origins you want to accept requests from
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods (GET, POST, etc)
    allow_headers=["*"],  # allow all headers
)

@app.get("/backtest")
def backtest(
    symbols: List[str] = Query(..., description="Comma separated symbols"),
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
):
    results = run_dispersion_strategy(symbols, start, end)
    return results
