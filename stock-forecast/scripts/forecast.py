#!/usr/bin/env python3
"""Run regression forecasting on weekly stock price data.

Supports linear and polynomial (degree 2 and 3) regression. The "all" mode
runs every model so they can be compared on the same chart.

Usage:
    python forecast.py --data /tmp/stock_data.csv --horizon 26 --model all \
        --out /tmp/forecast.csv
"""
import argparse
import json
import sys
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures


MODELS = {
    "linear": {"degree": 1, "label": "Linear"},
    "poly2": {"degree": 2, "label": "Polynomial (degree 2)"},
    "poly3": {"degree": 3, "label": "Polynomial (degree 3)"},
}


def fit_and_forecast(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_future: np.ndarray,
    degree: int,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Fit a polynomial regression of the given degree and project forward.

    Returns (fitted_on_train, predicted_on_future, metrics_dict).
    """
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_train_poly = poly.fit_transform(X_train)
    X_future_poly = poly.transform(X_future)

    model = LinearRegression()
    model.fit(X_train_poly, y_train)

    y_fit = model.predict(X_train_poly)
    y_future = model.predict(X_future_poly)

    metrics = {
        "r2": float(r2_score(y_train, y_fit)),
        "rmse": float(np.sqrt(mean_squared_error(y_train, y_fit))),
    }
    return y_fit, y_future, metrics


def resolve_models(selection: str) -> list[str]:
    selection = selection.lower().strip()
    if selection == "all":
        return ["linear", "poly2", "poly3"]
    if selection in ("polynomial", "poly"):
        # User-facing "polynomial" → default to degree 2
        return ["poly2"]
    if selection in MODELS:
        return [selection]
    raise ValueError(
        f"Unknown model '{selection}'. Choose from: linear, polynomial, all "
        "(or specifically poly2, poly3)."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run regression forecast on price data.")
    parser.add_argument("--data", required=True, help="Input CSV from fetch_data.py")
    parser.add_argument("--horizon", type=int, required=True, help="Weeks to forecast forward")
    parser.add_argument(
        "--model",
        default="all",
        help="Model to run: linear, polynomial, poly2, poly3, or all (default: all)",
    )
    parser.add_argument("--out", required=True, help="Output CSV path")
    args = parser.parse_args()

    try:
        models_to_run = resolve_models(args.model)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.horizon < 1 or args.horizon > 260:
        print(
            f"ERROR: Horizon {args.horizon} is outside reasonable range (1–260 weeks).",
            file=sys.stderr,
        )
        return 1

    df = pd.read_csv(args.data, parse_dates=["date"])
    if len(df) < 10:
        print("ERROR: Not enough data points to fit a regression.", file=sys.stderr)
        return 1

    X = df["week_index"].values.reshape(-1, 1).astype(float)
    y = df["close"].values.astype(float)

    last_week = int(df["week_index"].max())
    last_date = df["date"].max()
    future_weeks = np.arange(last_week + 1, last_week + 1 + args.horizon).reshape(-1, 1).astype(float)
    future_dates = [last_date + timedelta(weeks=int(i + 1)) for i in range(args.horizon)]

    # Build long-format output: one row per (date, series) where series is
    # "actual", "<model>_fit", or "<model>_forecast".
    rows = []
    for _, row in df.iterrows():
        rows.append({"date": row["date"], "series": "actual", "value": row["close"]})

    metrics_out = {}
    for model_key in models_to_run:
        cfg = MODELS[model_key]
        y_fit, y_future, metrics = fit_and_forecast(X, y, future_weeks, cfg["degree"])
        metrics_out[model_key] = {"label": cfg["label"], **metrics}

        for dt, val in zip(df["date"], y_fit):
            rows.append({"date": dt, "series": f"{model_key}_fit", "value": float(val)})
        for dt, val in zip(future_dates, y_future):
            rows.append({"date": dt, "series": f"{model_key}_forecast", "value": float(val)})

    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.out, index=False)

    metrics_path = args.out.replace(".csv", "_metrics.json")
    if metrics_path == args.out:
        metrics_path = args.out + ".metrics.json"
    # Use the expected canonical path if the caller passed the conventional name
    if args.out.endswith("forecast.csv"):
        metrics_path = args.out.replace("forecast.csv", "forecast_metrics.json")

    with open(metrics_path, "w") as f:
        json.dump(metrics_out, f, indent=2)

    print(f"Ran models: {', '.join(models_to_run)}")
    print(f"Forecast horizon: {args.horizon} weeks (through {future_dates[-1].date()})")
    for k, m in metrics_out.items():
        print(f"  {m['label']}: R²={m['r2']:.3f}  RMSE=${m['rmse']:.2f}")
    print(f"Wrote: {args.out}")
    print(f"Wrote: {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
