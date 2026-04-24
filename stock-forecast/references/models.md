# Regression Model Reference

This skill supports three regression models. Use this reference to explain choices to users or to decide which model to recommend when they ask.

## Linear regression

**What it does:** Fits a straight line `price = a * week + b` to the full history. The forecast is a simple extrapolation of that line.

**When it's appropriate:**
- You want a baseline "trend continuation" projection.
- The price series has a roughly consistent long-run drift (broad index ETFs over multi-year windows often look like this).
- The user wants the simplest, most interpretable forecast.

**Limitations:**
- Ignores curvature, regime changes, and volatility.
- A stock that had a big run-up followed by a plateau will have a linear forecast that keeps climbing regardless.
- R² on linear fits of stock prices is often deceptively high because prices do drift over long windows — high R² here does not mean the forecast is accurate.

## Polynomial regression, degree 2

**What it does:** Fits `price = a * week² + b * week + c`. Captures a single curve — acceleration or deceleration.

**When it's appropriate:**
- The price series shows clear curvature (e.g., a growth stock that compounded, then flattened).
- The user wants to capture "momentum is slowing/accelerating."

**Limitations:**
- Forces the forecast into a parabolic shape. If the recent trend is down, the forecast will keep curving down — possibly into negative prices within a long horizon.
- Sensitive to the endpoints of the training window.

## Polynomial regression, degree 3

**What it does:** Fits a cubic `price = a*week³ + b*week² + c*week + d`. Can capture an S-curve or reversal.

**When it's appropriate:**
- The series has genuinely complex shape over the lookback window (one inflection point).
- Mainly useful for comparison — it almost always fits training data better than lower-degree models, which is informative but not predictive.

**Limitations:**
- **Extrapolation is dangerous.** Cubic terms explode at the edges. On long horizons, degree-3 forecasts can produce absurd price projections (e.g., $5,000 for a $150 stock within two years).
- High R² here is especially misleading — overfitting is almost guaranteed.
- The skill caps polynomial degree at 3 for this reason; do not add higher degrees.

## Why no ARIMA / Prophet / LSTM?

This skill is scoped to regression models specifically because:
1. Users often want the mental model of "draw a trend line into the future" — regression delivers that directly.
2. Time-series models like ARIMA require stationarity checks, differencing decisions, and order selection that would bloat the skill.
3. Neural approaches add heavy dependencies and don't outperform regression on weekly closes over the horizons this skill targets.

If a user specifically asks for ARIMA or Prophet, tell them this skill doesn't cover those but the Python libraries `statsmodels` and `prophet` are the standard choices.

## How to recommend a model

- User says "keep it simple" → `linear`.
- User says "the stock has been accelerating/decelerating" → `poly2`.
- User says "show me all of them" or "which is best" → `all`, and explain that "best fit" ≠ "best forecast."
- User is going to share the chart publicly → `all`, so the disagreement between models visually communicates forecast uncertainty.
