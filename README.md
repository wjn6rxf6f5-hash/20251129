# 20251129

Black-Scholes option calculator with customizable payoffs.

## Getting started

### Install dependencies
```
pip install flask
```

### Run the web server
```
python app.py
```
The server listens on [http://localhost:8000](http://localhost:8000).

### Using the calculator
- Open the root page to see the form.
- Fill in the inputs:
  - `Spot (S0)`, `Strike (K)`, `Risk-free rate (r)`, `Volatility (σ)`, `Maturity (T)`.
  - `Simulations` controls the number of Monte Carlo paths (default 20,000).
  - `Payoff expression` accepts Python-style expressions using `ST` (terminal price) and optionally `K`, `r`, `sigma`, `T`.
- Examples:
  - European call: `max(ST - K, 0)`
  - European put: `max(K - ST, 0)`
  - Strangle payoff: `max(abs(ST - K) - 10, 0)`
- Click **Estimate Price** to see the discounted Monte Carlo estimate. Errors from invalid expressions will be shown under the form.
