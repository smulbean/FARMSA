import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

implied_vol = pd.DataFrame()

# === 1. Fetch SPY underlying data ===
def get_spy_data(start, end):
    df = yf.download("SPY", start=start, end=end)
    df = df[['Close']].dropna()
    df.rename(columns={'Close':'SPY_Close'}, inplace=True)
    df['Return'] = df['SPY_Close'].pct_change()
    return df

# === 2. Fetch option chain and mid-price ===
def get_option_mid(symbol, expiry, contract_symbol):
    tk = yf.Ticker(symbol)
    options = tk.option_chain(expiry)
    combined = pd.concat([options.calls.assign(Type='C'),
                          options.puts.assign(Type='P')],
                          ignore_index=True)
    opt = combined[combined.contractSymbol == contract_symbol].copy()
    if opt.empty:
        raise ValueError("Contract symbol not found in chain")
    return {
        'bid': opt.bid.values[0],
        'ask': opt.ask.values[0],
        'mid': float(opt.bid.values[0] + opt.ask.values[0]) / 2
    }

# === 3. Generate signals ===
def generate_signals(df, window=20, std_dev=2):
    df['Mean'] = df['Return'].rolling(window).mean()
    df['Std'] = df['Return'].rolling(window).std()
    df['Upper'] = df['Mean'] + std_dev * df['Std']
    df['Lower'] = df['Mean'] - std_dev * df['Std']
    df['Signal'] = ((df['Return'] > df['Upper']) | (df['Return'] < df['Lower'])).astype(int)
    return df

# === 4. Backtest option PnL ===
def backtest_option(df, symbol, expiry, contract, hold_days=5):
    df = df.copy()
    df['Opt_Mid'] = np.nan
    df['Entry'] = np.nan
    df['Exit'] = np.nan
    df['PnL'] = 0.0

    for i in range(len(df)):
        if df['Signal'].iloc[i] == 1:
            entry_date = df.index[i]
            try:
                opt = get_option_mid(symbol, expiry, contract)
                df.iloc[i, df.columns.get_loc('Opt_Mid')] = opt['mid']
                df.iloc[i, df.columns.get_loc('Entry')] = opt['mid']
            except Exception as e:
                print(f"Failed fetch at {entry_date.strftime('%Y-%m-%d')}: {e}")
                continue

            # Calculate exit index
            exit_index = i + hold_days
            if exit_index < len(df):
                try:
                    opt_exit = get_option_mid(symbol, expiry, contract)
                    df.iloc[exit_index, df.columns.get_loc('Exit')] = opt_exit['mid']
                    pnl = opt_exit['mid'] - opt['mid']
                    df.iloc[exit_index, df.columns.get_loc('PnL')] += pnl
                except Exception as e:
                    exit_date = df.index[exit_index]
                    print(f"Failed exit fetch at {exit_date.strftime('%Y-%m-%d')}: {e}")

    df['Cumulative_PnL'] = df['PnL'].cumsum()
    return df



# === 5. Plotting ===
def plot_results(df):
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(df.index, df['SPY_Close'], label='SPY Close', color='blue')
    ax1.set_ylabel('SPY Price')
    
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['Cumulative_PnL'], label='Cumulative PnL', color='red')
    ax2.set_ylabel('Cumulative PnL')
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title('Straddle-like Option Backtest PnL')
    plt.show()

# === Main ===
if __name__ == "__main__":
    end = datetime.today() - timedelta(days=1)
    start = end - timedelta(days=365*2)
    df_spy = get_spy_data(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    
    df_spy = generate_signals(df_spy, window=20, std_dev=2)
    
    # SPY option:
    contract_sym = "SPY250613C00600000"
    expiry = "2025-06-13"
    results = backtest_option(df_spy, "SPY", expiry, contract_sym, hold_days=5)
    
    plot_results(results)
    print(results[['SPY_Close','Return','Signal','Entry','Exit','PnL','Cumulative_PnL']].dropna(subset=['PnL']))
