import numpy as np
from scipy.stats import norm
import yfinance as yf


class QuantMathEngine:
    def __init__(self):
        pass

    def calculate_var(self, ticker: str, portfolio_value: float, confidence_level: float = 0.95) -> dict:
        """
        Calculates the parametric Value at Risk (VaR) for a single asset.
        Estimates the maximum loss over a 1-day period with the given confidence.
        """
        try:
            df = yf.download(ticker, period="1y", progress=False)
            if df.empty:
                return {"error": "No data"}
            df['Returns'] = df['Close'].pct_change()
            df = df.dropna()
            mu = float(np.mean(df['Returns'].values))
            sigma = float(np.std(df['Returns'].values))
            z_score = norm.ppf(1 - confidence_level)
            var_pct = abs(mu + z_score * sigma)
            var_dollar = portfolio_value * var_pct
            return {
                "var_pct": round(var_pct, 5),
                "var_dollar": round(float(var_dollar), 2),
                "confidence": confidence_level * 100,
                "sigma": round(sigma, 5)
            }
        except Exception as e:
            return {"error": str(e)}

    def monte_carlo_simulation(self, ticker: str, days: int = 30, simulations: int = 500) -> dict:
        """
        Runs a Monte Carlo simulation projecting future price paths.
        Returns percentile bands for fan chart visualization.
        """
        try:
            df = yf.download(ticker, period="1y", progress=False, auto_adjust=True)
            if df.empty:
                return {"error": "No data"}

            close = df['Close'].squeeze().values.astype(float)
            daily_returns = np.diff(close) / close[:-1]
            mu = np.mean(daily_returns)
            sigma = np.std(daily_returns)
            last_price = close[-1]

            # Run simulations
            all_paths = np.zeros((simulations, days))
            for i in range(simulations):
                rand_returns = np.random.normal(mu, sigma, days)
                prices = [last_price]
                for r in rand_returns:
                    prices.append(prices[-1] * (1 + r))
                all_paths[i] = prices[1:]

            # Compute percentile bands for fan chart
            fan_chart = []
            for day in range(days):
                day_vals = all_paths[:, day]
                fan_chart.append({
                    "day": day + 1,
                    "p5": round(float(np.percentile(day_vals, 5)), 2),
                    "p25": round(float(np.percentile(day_vals, 25)), 2),
                    "p50": round(float(np.percentile(day_vals, 50)), 2),
                    "p75": round(float(np.percentile(day_vals, 75)), 2),
                    "p95": round(float(np.percentile(day_vals, 95)), 2),
                })

            final_prices = all_paths[:, -1]
            return {
                "start_price": round(float(last_price), 2),
                "simulations": simulations,
                "days": days,
                "prob_profit": round(float(np.mean(final_prices > last_price) * 100), 1),
                "expected_return_pct": round(float((np.mean(final_prices) - last_price) / last_price * 100), 2),
                "fan_chart": fan_chart
            }
        except Exception as e:
            return {"error": str(e)}

    def calculate_optimal_weights(self, tickers: list) -> dict:
        """
        Risk-parity portfolio optimization using inverse-volatility weighting.
        """
        weights = {}
        total_inv_vol = 0
        vols = {}
        try:
            for ticker in tickers:
                df = yf.download(ticker, period="1y", progress=False)
                if not df.empty:
                    vol = float(np.std(df['Close'].pct_change().dropna().values))
                    vols[ticker] = vol
                    total_inv_vol += (1 / vol) if vol > 0 else 0
            for ticker in vols:
                weights[ticker] = round(float((1 / vols[ticker]) / total_inv_vol * 100), 1) if total_inv_vol > 0 else 0
            return {"weights": weights, "method": "Inverse Volatility (Risk Parity)"}
        except Exception as e:
            return {"error": str(e)}
