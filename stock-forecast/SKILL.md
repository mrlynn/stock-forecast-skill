---
name: stock-forecast
description: Weekly stock price regression forecasts (linear/polynomial) with PNG/HTML charts. For ticker-based projections and trend charts—not fundamentals, earnings, or options.
dependencies: python>=3.10, yfinance, pandas, numpy, scikit-learn, matplotlib, plotly
---

# Stock Price Forecasting

This skill fetches weekly historical stock price data and generates regression-based price forecasts with both static and interactive visualizations. It supports multiple model types so users can compare approaches.

**When to use (beyond the short `description` in frontmatter):** The user wants to forecast, predict, or project stock prices; visualize historical price trends with forward projections; run or compare regression on price history; ask where a stock is “headed” in a technical, chart-based sense; or provides a ticker and wants forward-looking price analysis. **Do not** use for fundamental analysis, earnings estimates, or options pricing.

## Critical disclaimer — surface this to the user

Regression on historical price series is **not a reliable predictor of future stock prices**. Markets are driven by information, sentiment, and events that are not encoded in past price trajectories. Before presenting any forecast, tell the user plainly: this is a visualization and educational tool, not investment advice, and the forecast should not be used to make trading decisions. Include this disclaimer in the final chart and in the summary text.

## Workflow

Follow these steps in order. Do not skip the input-gathering phase — missing or invalid inputs produce misleading charts.

### Step 1: Gather inputs

Ask the user for these three inputs. If the user provided some in their initial message, only ask for the missing ones. Use a single consolidated question when possible.

1. **Ticker symbol** — e.g., `AAPL`, `MSFT`, `SPY`. Validate it against Yahoo Finance (the fetch script will error early if the ticker is invalid).
2. **Lookback window in years** — how many years of history to pull. Reasonable range is 2–20. Default suggestion: 5 years.
3. **Forecast horizon in weeks** — how far forward to project. Reasonable range is 4–104 weeks. Default suggestion: 26 weeks (about 6 months).
4. **Model choice** — one of `linear`, `polynomial`, `all` (to compare side by side). Default suggestion: `all`.

If the user says something like "just pick good defaults," use 5 years / 26 weeks / all models and proceed.

### Step 2: Install dependencies if needed

The scripts require Python 3.10+ and: `yfinance`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, and `plotly`. From the `stock-forecast` directory, install with:

```bash
pip install -r requirements.txt
```

Use a virtual environment when possible. In restricted environments, add `--user` or `--break-system-packages` only if your platform requires it to install into a user or system site-packages location.

### Step 3: Fetch data

Run the fetch script:

```bash
python scripts/fetch_data.py --ticker <TICKER> --years <YEARS> --out /tmp/stock_data.csv
```

The script downloads weekly closes from Yahoo Finance and writes a CSV. It will exit with a clear error if the ticker is invalid or has no data for the requested range. If fetch fails, report the error to the user and stop — do not fabricate data or proceed with partial data.

### Step 4: Run forecast

Run the forecast script with the chosen model:

```bash
python scripts/forecast.py \
  --data /tmp/stock_data.csv \
  --horizon <WEEKS> \
  --model <linear|polynomial|all> \
  --out /tmp/forecast.csv
```

This produces a CSV with historical + forecasted prices per model, plus a JSON file with model fit metrics (R², RMSE) at `/tmp/forecast_metrics.json`.

### Step 5: Generate visualizations

Run the visualization script to produce both outputs:

```bash
python scripts/visualize.py \
  --forecast /tmp/forecast.csv \
  --metrics /tmp/forecast_metrics.json \
  --ticker <TICKER> \
  --png /tmp/forecast.png \
  --html /tmp/forecast.html
```

### Step 6: Present results

Present the outputs to the user in this order:

1. A brief summary (2–4 sentences) of what was fetched, which model(s) were run, and the headline forecast (e.g., "Linear model projects $X by <date>; polynomial projects $Y").
2. The model metrics table (R², RMSE per model).
3. Both chart files, using `present_files` if available, or by describing the file paths otherwise. Present the PNG first for a quick view, then the HTML for interactive exploration.
4. **The disclaimer.** Always. Bold it.

If the user asked for only one model, skip the comparison framing and present just that model's output.

## Model reference

For detailed explanation of each regression model, when it's appropriate, and its limitations, see `references/models.md`. Consult it if the user asks "which model should I use" or "why is the polynomial forecast curving up so steeply."

## Common pitfalls to avoid

- **Don't extrapolate polynomial degrees above 3 on long horizons.** High-degree polynomials explode at the edges. The forecast script caps this at degree 3.
- **Don't present R² on training data as "accuracy."** R² here measures fit to historical data, not predictive power. Make this clear in the summary if the user asks about the metrics.
- **Don't silently adjust the user's inputs.** If they ask for 50 years of data on a ticker that only has 10, tell them and ask how to proceed.
- **Don't run forecasts on tickers with gaps or halts** (e.g., delisted stocks, SPACs pre-merger) without flagging the data quality issue.

## Example interaction

**User:** "Can you forecast AAPL for me?"

**Skill response:** "Sure — I'll need a few things: how many years of history should I pull (default 5), how far forward should I project (default 26 weeks / ~6 months), and do you want to compare multiple regression models or just one (default: all)?"

**User:** "Use defaults."

**Skill response:** [Runs fetch → forecast → visualize pipeline. Presents summary, metrics, PNG, HTML, disclaimer.]
