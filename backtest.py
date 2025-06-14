import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df = df[['Close']]
    df.dropna(inplace=True)
    return df

def generate_signals(df, threshold=0.02):
    """
    Generate signals to enter a straddle.
    Example rule: Enter when daily price change exceeds threshold up or down.
    """
    df['Return'] = df['Close'].pct_change()
    df['Signal'] = 0
    df.loc[df['Return'].abs() >= threshold, 'Signal'] = 1
    return df

def backtest_straddle(df, hold_days=200):
    """
    Backtest a straddle strategy based on signals.
    
    Parameters:
    - df: DataFrame with 'Signal' column
    - hold_days: Number of days to hold the position
    
    Returns:
    - df with 'Position', 'PnL', and 'Cumulative PnL' columns
    """
    df = df.copy()
    df['Position'] = 0
    df['PnL'] = 0.0

    for i in range(len(df)):
        if df['Signal'].iloc[i] == 1:
            entry_price = df['Close'].iloc[i]  # this is a scalar float
            exit_index = i + hold_days

            if exit_index < len(df):
                exit_price = df['Close'].iloc[exit_index]  # scalar float

                # Calculate absolute return as float
                abs_return = float(abs((exit_price - entry_price) / entry_price))
                
                # Assign realized PnL on the exit date
                df.iloc[exit_index, df.columns.get_loc('PnL')] += abs_return

                # Mark holding period as position = 1
                for j in range(i, exit_index):
                    df.iloc[j, df.columns.get_loc('Position')] = 1
                    
    df['Cumulative PnL'] = df['PnL'].cumsum()
    return df




def plot_results(df, ticker):
    fig, ax1 = plt.subplots(figsize=(12,6))
    
    ax1.plot(df.index, df['Close'], label=f'{ticker} Close Price', color='blue')
    ax1.set_ylabel('Price')
    
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['Cumulative PnL'], label='Cumulative PnL', color='green')
    ax2.set_ylabel('Cumulative PnL')
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title(f'Options Straddle Backtest for {ticker}')
    plt.show()


if __name__ == "__main__":
    ticker = "AAPL"
    end_date = datetime.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=5*365)  # approximate 5 years (ignores leap years)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    data = get_data(ticker, start_date_str, end_date_str)
    data = generate_signals(data, threshold=0.03)  # 3% daily move triggers signal
    results = backtest_straddle(data, hold_days=5)
    plot_results(results, ticker)
