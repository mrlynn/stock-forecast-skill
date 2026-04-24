#!/usr/bin/env python3
"""Generate static PNG and interactive HTML charts from forecast output.

Usage:
    python visualize.py --forecast /tmp/forecast.csv \
        --metrics /tmp/forecast_metrics.json \
        --ticker AAPL \
        --png /tmp/forecast.png \
        --html /tmp/forecast.html
"""
import argparse
import json
import sys

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go


DISCLAIMER = (
    "Regression forecasts are illustrative only. Past price trajectories do not "
    "predict future returns. Not investment advice."
)

# Consistent colors across both chart types
COLORS = {
    "actual": "#1f2937",       # near-black
    "linear": "#2563eb",       # blue
    "poly2": "#16a34a",        # green
    "poly3": "#dc2626",        # red
}


def render_png(df: pd.DataFrame, metrics: dict, ticker: str, path: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 6.5))

    actual = df[df["series"] == "actual"]
    ax.plot(actual["date"], actual["value"], color=COLORS["actual"], linewidth=1.6, label="Actual")

    # Separator between history and forecast
    if not actual.empty:
        ax.axvline(actual["date"].max(), color="#9ca3af", linestyle="--", linewidth=1, alpha=0.7)

    for model_key, meta in metrics.items():
        color = COLORS.get(model_key, "#6b7280")
        fit = df[df["series"] == f"{model_key}_fit"]
        fc = df[df["series"] == f"{model_key}_forecast"]
        ax.plot(fit["date"], fit["value"], color=color, linewidth=1.2, alpha=0.5, linestyle="-")
        ax.plot(
            fc["date"], fc["value"],
            color=color, linewidth=2.2, linestyle="--",
            label=f"{meta['label']} (R²={meta['r2']:.2f})",
        )

    ax.set_title(f"{ticker} — Weekly Close with Regression Forecast", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", framealpha=0.9)

    fig.text(0.5, 0.01, DISCLAIMER, ha="center", fontsize=8, style="italic", color="#6b7280")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def render_html(df: pd.DataFrame, metrics: dict, ticker: str, path: str) -> None:
    fig = go.Figure()

    actual = df[df["series"] == "actual"]
    fig.add_trace(go.Scatter(
        x=actual["date"], y=actual["value"],
        mode="lines", name="Actual",
        line=dict(color=COLORS["actual"], width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra>Actual</extra>",
    ))

    for model_key, meta in metrics.items():
        color = COLORS.get(model_key, "#6b7280")
        fit = df[df["series"] == f"{model_key}_fit"]
        fc = df[df["series"] == f"{model_key}_forecast"]
        fig.add_trace(go.Scatter(
            x=fit["date"], y=fit["value"],
            mode="lines", name=f"{meta['label']} fit",
            line=dict(color=color, width=1.5, dash="solid"),
            opacity=0.45,
            hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra>" + meta["label"] + " fit</extra>",
            legendgroup=model_key,
        ))
        fig.add_trace(go.Scatter(
            x=fc["date"], y=fc["value"],
            mode="lines",
            name=f"{meta['label']} forecast  (R²={meta['r2']:.2f})",
            line=dict(color=color, width=2.8, dash="dash"),
            hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra>" + meta["label"] + " forecast</extra>",
            legendgroup=model_key,
        ))

    # Vertical separator at the last actual date
    if not actual.empty:
        last_date = actual["date"].max()
        fig.add_vline(x=last_date, line_width=1, line_dash="dot", line_color="#9ca3af")

    fig.update_layout(
        title=dict(
            text=f"<b>{ticker} — Weekly Close with Regression Forecast</b>",
            x=0.02, xanchor="left",
        ),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=30, t=80, b=80),
        annotations=[
            dict(
                text=f"<i>{DISCLAIMER}</i>",
                xref="paper", yref="paper", x=0.5, y=-0.18,
                xanchor="center", showarrow=False,
                font=dict(size=10, color="#6b7280"),
            )
        ],
    )

    fig.write_html(path, include_plotlyjs="cdn", full_html=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render forecast charts.")
    parser.add_argument("--forecast", required=True, help="Forecast CSV from forecast.py")
    parser.add_argument("--metrics", required=True, help="Metrics JSON from forecast.py")
    parser.add_argument("--ticker", required=True, help="Ticker symbol for chart title")
    parser.add_argument("--png", required=True, help="Output PNG path")
    parser.add_argument("--html", required=True, help="Output HTML path")
    args = parser.parse_args()

    df = pd.read_csv(args.forecast, parse_dates=["date"])
    with open(args.metrics) as f:
        metrics = json.load(f)

    render_png(df, metrics, args.ticker.upper(), args.png)
    render_html(df, metrics, args.ticker.upper(), args.html)

    print(f"Wrote: {args.png}")
    print(f"Wrote: {args.html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
