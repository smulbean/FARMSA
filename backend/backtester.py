# backend/backtester.py
import numpy as np
from polygon_client import get_daily_closes



def run_dispersion_strategy(symbols, start_date, end_date):
    component_vols = []

    for symbol in symbols:
        closes = get_daily_closes(symbol, start_date, end_date)
        if closes:
            vol = np.std(closes)
            component_vols.append(vol)
        else:
            component_vols.append(0)

    # Fetch index closes, e.g., SPY
    index_closes = get_daily_closes("SPY", start_date, end_date)
    index_vol = np.std(index_closes) if index_closes else 0

    dispersion = np.mean(component_vols) - index_vol if component_vols else 0

    return {
        "component_vols": component_vols,
        "index_vol": index_vol,
        "dispersion": dispersion
    }


