# backend/polygon_client.py

from polygon import RESTClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
stocks_client = RESTClient("2OLjrA2D9B53VeTFvoZGfLvYWH1LJ5N0")



def get_daily_closes(symbol, start_date, end_date):
    """
    Returns a list of daily close prices for a stock between start_date and end_date.
    Dates must be in YYYY-MM-DD format.
    """
    try:
        aggs = stocks_client.get_aggs(
            ticker=symbol,
            multiplier=1,
            timespan="day",
            from_=start_date,
            to=end_date,
            adjusted=True,
            limit=5000
        )
        # Extract closes from aggregate bars
        return [bar.close for bar in aggs]
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return []


