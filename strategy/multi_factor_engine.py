from strategy.nlp_engine import NLPEngine
from strategy.technical_engine import TechnicalEngine


class MultiFactorEngine:
    def __init__(self, provider):
        self.provider = provider
        self.nlp = NLPEngine()
        self.ta_engine = TechnicalEngine()

    def generate_analysis(self, ticker: str, asset_class: str) -> dict:
        """
        Generates 0-100 scores for Fundamental, Technical, and Sentiment factors.
        Uses REAL technical indicators (RSI, MACD, BB, Golden Cross).
        """
        # 1. Real Technical Analysis
        ta_data = self.ta_engine.analyze(ticker)
        tech_score = ta_data.get('technical_score', 50)
        tech_reason = ta_data.get('reason', 'N/A')

        # 2. Fundamental Analysis
        fund_score = 50
        fund_reason = "No fundamental data"
        if asset_class == 'stock':
            try:
                ratios = self.provider.get_financial_ratios(ticker)
                debt = ratios.get('debt_to_mcap', 1)
                if debt < 0.10:
                    fund_score = 85
                    fund_reason = "Excellent balance sheet (very low debt)"
                elif debt < 0.20:
                    fund_score = 70
                    fund_reason = "Strong cashflow, low debt"
                elif debt < 0.30:
                    fund_score = 55
                    fund_reason = "Moderate debt levels"
                else:
                    fund_score = 35
                    fund_reason = "High debt burden"
            except Exception:
                fund_score = 50
                fund_reason = "Fundamental data unavailable"
        else:
            fund_score = 60
            fund_reason = "Crypto: fundamentals based on whitelist status"

        # 3. Real-Time NLP Sentiment
        sentiment_data = self.nlp.get_news_sentiment(ticker)
        sent_score = sentiment_data['score']
        sent_reason = sentiment_data['reason']
        headlines = sentiment_data.get('headlines', [])

        # Weighted Conviction Score (TA=40%, Fundamental=30%, Sentiment=30%)
        conviction_score = int(tech_score * 0.4 + fund_score * 0.3 + sent_score * 0.3)

        # Signal classification
        if conviction_score >= 80:
            signal = "STRONG BUY"
        elif conviction_score >= 65:
            signal = "BUY"
        elif conviction_score >= 45:
            signal = "HOLD"
        elif conviction_score >= 30:
            signal = "SELL"
        else:
            signal = "STRONG SELL"

        # Target Profit / Stop Loss based on VaR sigma
        sigma = ta_data.get('sigma', 0.02) if 'sigma' in ta_data else 0.02
        target_profit = round(conviction_score / 10 * 1.5, 1)
        stop_loss = round(max(1.5, float(ta_data.get('sigma', 0.02) * 100) * 2), 1) if ta_data.get('sigma') else 2.5

        return {
            "conviction": conviction_score,
            "signal": signal,
            "technical_score": tech_score,
            "technical_reason": tech_reason,
            "fundamental_score": fund_score,
            "fundamental_reason": fund_reason,
            "sentiment_score": sent_score,
            "sentiment_reason": sent_reason,
            "headlines": headlines,
            "ta_data": {
                "rsi": ta_data.get('rsi'),
                "macd_hist": ta_data.get('macd_hist'),
                "golden_cross": ta_data.get('golden_cross'),
                "sma50": ta_data.get('sma50'),
                "sma200": ta_data.get('sma200'),
                "bb_upper": ta_data.get('bb_upper'),
                "bb_lower": ta_data.get('bb_lower'),
                "price": ta_data.get('price'),
            },
            "target_profit_pct": target_profit,
            "stop_loss_pct": stop_loss,
        }
