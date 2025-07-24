from polygon import RESTClient
from .polygon_client import stocks_client
from datetime import datetime, timedelta
import math
import numpy as np

import os
from dotenv import load_dotenv

load_dotenv()
OPTION_API_KEY = os.getenv("OPTION_API_KEY", "2OLjrA2D9B53VeTFvoZGfLvYWH1LJ5N0")

client = RESTClient(OPTION_API_KEY)

expiry = "2025-12-19"
contract_type = "call"
spy_strike = 650

def build_option_symbol(ticker, expiration_date, strike_price, call_put):
    yymmdd = datetime.strptime(expiration_date, "%Y-%m-%d").strftime("%y%m%d")
    strike_formatted = f"{int(strike_price * 1000):08d}"
    return f"O:{ticker.upper()}{yymmdd}{call_put.upper()}{strike_formatted}"

def round_to_nearest_10(x):
    return round(x / 10) * 10

def get_stock_close_price_poly(ticker, date_str):
    """Return close price for specific date using Polygon daily aggs."""
    try:
        aggs = stocks_client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=date_str,
            to=date_str,
            adjusted=True,
            limit=1,
        )
        return aggs[0].close if aggs else None
    except Exception:
        return None

def get_option_close_price(option_symbol, date_str):
    try:
        response = client.get_daily_open_close_agg(option_symbol, date_str, adjusted="true")
        return response.close
    except Exception:
        return None

def calculate_contracts_and_vega(api_key, weightings, total_notional, expiration_date, pricing_date, contract_type="call"):
    client_local = RESTClient(api_key)
    notional_allocations = {k: v / sum(weightings.values()) * total_notional for k, v in weightings.items()}
    results = {}
    for ticker, notional in notional_allocations.items():
        stock_price = get_stock_close_price_poly(ticker, pricing_date)
        if stock_price is None:
            results[ticker] = "No stock price data."
            continue

        strike_price = round_to_nearest_10(float(stock_price))

        options_chain = list(client_local.list_snapshot_options_chain(
            ticker,
            params={
                "strike_price": strike_price,
                "expiration_date": expiration_date,
                "contract_type": contract_type,
                "order": "asc",
                "limit": 100,
                "sort": "strike_price"
            }
        ))
        if not options_chain:
            results[ticker] = "No option data found."
            continue

        o = options_chain[0]
        option_symbol = build_option_symbol(ticker, expiration_date, strike_price, contract_type[0])
        price = get_option_close_price(option_symbol, pricing_date)
        vega = getattr(o.greeks, "vega", None)
        shares_per_contract = getattr(o.details, "shares_per_contract", 100)

        if price is None or price == 0 or vega is None:
            results[ticker] = "Insufficient price or vega data."
            continue

        contracts = math.floor(notional / (price * shares_per_contract))
        total_vega = contracts * vega

        results[ticker] = {
            "notional_allocated": notional,
            "price_per_option": price,
            "contracts": contracts,
            "vega_per_contract": vega,
            "total_vega": total_vega,
            "shares_per_contract": shares_per_contract,
            "option_ticker": o.details.ticker
        }
    return results

def total_vega(results):
    return sum(data["total_vega"] for data in results.values() if isinstance(data, dict))

def portfolio_value(results, date_str):
    val = 0
    for ticker, data in results.items():
        if not isinstance(data, dict):
            continue
        stock_price = get_stock_close_price_poly(ticker, date_str)
        if stock_price is None:
            continue
        strike_price = round_to_nearest_10(float(stock_price))
        option_symbol = build_option_symbol(ticker, expiry, strike_price, contract_type[0])
        price = get_option_close_price(option_symbol, date_str)
        if price is None:
            continue
        val += price * data["shares_per_contract"] * data["contracts"]
    return val

def get_spy_hedge_contracts(vega_needed, date_str, spy_strike_value):
    spy_options = list(client.list_snapshot_options_chain(
        "SPY",
        params={
            "strike_price": spy_strike_value,
            "expiration_date": expiry,
            "contract_type": contract_type,
            "order": "asc",
            "limit": 100,
            "sort": "strike_price"
        }
    ))
    if not spy_options:
        return None
    o = spy_options[0]
    option_symbol = build_option_symbol("SPY", expiry, spy_strike_value, contract_type[0])
    price = get_option_close_price(option_symbol, date_str)
    vega = getattr(o.greeks, "vega", None)
    shares_per_contract = getattr(o.details, "shares_per_contract", 100)
    if price is None or price == 0 or vega is None:
        return None
    contracts = math.ceil(vega_needed / vega) if vega_needed > 0 else 0
    total_vega = contracts * vega
    return {
        "notional_allocated": contracts * price * shares_per_contract,
        "price_per_option": price,
        "contracts": contracts,
        "vega_per_contract": vega,
        "total_vega": total_vega,
        "shares_per_contract": shares_per_contract,
        "option_ticker": o.details.ticker
    }

def run_dispersion_backtest(api_key, weights, total_notional, expiry, contract_type, start_date, end_date, hedge_threshold, spy_strike):
    client_local = RESTClient(api_key)

    # Initial portfolio and hedge
    try:
        portfolio = calculate_contracts_and_vega(api_key, weights, total_notional, expiry, start_date.strftime("%Y-%m-%d"), contract_type)
        spy_hedge = get_spy_hedge_contracts(total_vega(portfolio), start_date.strftime("%Y-%m-%d"), spy_strike)
        if spy_hedge is None:
            raise RuntimeError("Could not get initial SPY hedge data.")
    except Exception as e:
        print(f"[DEBUG] Failed initial portfolio or hedge setup: {e}")
        return None

    prev_hedge_contracts = spy_hedge["contracts"]
    prev_hedge_price = spy_hedge["price_per_option"]
    realized_hedge_pnl = 0.0

    dates = []
    pnls = []
    spy_prices = []
    final_pnl = None

    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        date_str = current_date.strftime("%Y-%m-%d")

        try:
            portfolio = calculate_contracts_and_vega(api_key, weights, total_notional, expiry, date_str, contract_type)
            port_vega = total_vega(portfolio)
            port_value = portfolio_value(portfolio, date_str)
            if port_value is None or port_vega == 0:
                print(f"[DEBUG] Missing portfolio value or zero vega for {date_str}, skipping day")
                current_date += timedelta(days=1)
                continue

            spy_hedge_vega = spy_hedge["contracts"] * spy_hedge["vega_per_contract"]

            option_symbol = build_option_symbol("SPY", expiry, spy_strike, contract_type[0])
            spy_price = get_option_close_price(option_symbol, date_str)
            if spy_price is None:
                print(f"[DEBUG] Missing SPY option price for {date_str}, skipping day")
                current_date += timedelta(days=1)
                continue

            spy_value = spy_price * spy_hedge["shares_per_contract"] * spy_hedge["contracts"]

            vega_ratio = spy_hedge_vega / port_vega if port_vega else 1.0

            if abs(vega_ratio - 1.0) > hedge_threshold:
                new_hedge = get_spy_hedge_contracts(port_vega, date_str, spy_strike)
                if new_hedge is not None:
                    realized_pnl_from_closing = (spy_price - prev_hedge_price) * prev_hedge_contracts * spy_hedge["shares_per_contract"]
                    realized_hedge_pnl += realized_pnl_from_closing

                    spy_hedge = new_hedge
                    prev_hedge_contracts = new_hedge["contracts"]
                    prev_hedge_price = new_hedge["price_per_option"]
                else:
                    print(f"[DEBUG] Could not update SPY hedge for {date_str}")

            final_pnl = (port_value - spy_value) + realized_hedge_pnl

            dates.append(current_date)
            pnls.append(final_pnl)

            spy_option_close_price = get_option_close_price(option_symbol, date_str)
            spy_prices.append(spy_option_close_price if spy_option_close_price is not None else (spy_prices[-1] if spy_prices else None))

        except Exception as e:
            print(f"[DEBUG] Exception on {date_str}: {e}, skipping day")

        current_date += timedelta(days=1)

    return {
        "dates": dates,
        "pnls": pnls,
        "final_pnl": final_pnl,
        "spy_prices": spy_prices
    }
