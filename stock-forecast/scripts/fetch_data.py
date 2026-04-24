#!/usr/bin/env python3
"""Fetch weekly historical stock price data from Yahoo Finance.

Usage:
    python fetch_data.py --ticker AAPL --years 5 --out /tmp/stock_data.csv

Outputs a CSV with columns: date, close, week_index
"""
import argparse
import sys
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


def fetch_weekly(ticker: str, years: int) -> pd.DataFrame:
    """Fetch weekly close prices for the given ticker and lookback window."""
    end = datetime.now()
    start = end - timedelta(days=int(years * 365.25))

    # interval="1wk" gives weekly bars ending Friday
    df = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval="1wk",
        auto_adjust=True,
        progress=False,
    )

    if df is None or df.empty:
        raise ValueError(
            f"No data returned for ticker '{ticker}'. "
            "Check the symbol is correct and that it has trading history "
            f"over the past {years} year(s)."
        )

    # yfinance sometimes returns a MultiIndex on columns when ticker is a list;
    # flatten it defensively.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    # Standardize column names across yfinance versions
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    close_col = "Close" if "Close" in df.columns else "Adj Close"

    out = pd.DataFrame({
        "date": pd.to_datetime(df[date_col]),
        "close": df[close_col].astype(float),
    })
    out = out.dropna().reset_index(drop=True)
    out["week_index"] = range(len(out))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch weekly stock prices.")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument("--years", type=float, required=True, help="Years of history to fetch")
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()

    ticker = args.ticker.upper().strip()

    try:
        df = fetch_weekly(ticker, args.years)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if len(df) < 10:
        print(
            f"ERROR: Only {len(df)} weekly data points found for {ticker}. "
            "Need at least 10 for a meaningful forecast.",
            file=sys.stderr,
        )
        return 1

    df.to_csv(args.out, index=False)
    print(f"Fetched {len(df)} weekly bars for {ticker}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
    print(f"Wrote: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
