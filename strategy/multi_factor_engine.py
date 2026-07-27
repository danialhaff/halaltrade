from strategy.nlp_engine import NLPEngine
from strategy.technical_engine import TechnicalEngine
import joblib
import pandas as pd
import os
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "xgboost_brain.pkl")

class MultiFactorEngine:
    def __init__(self, provider):
        self.provider = provider
        self.nlp = NLPEngine()
        self.ta_engine = TechnicalEngine()
        self.ai_model = None
        try:
            if os.path.exists(MODEL_PATH):
                self.ai_model = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"Warning: Could not load AI ML Model: {e}")

    def generate_analysis(self, ticker: str, asset_class: str) -> dict:
        """
        Generates analysis using the trained XGBoost ML Brain.
        Combines it with Fundamentals and Sentiment for the final Conviction Score.
        """
        # 1. Real Technical Analysis (Features for AI)
        ta_data = self.ta_engine.analyze(ticker)
        
        # 2. AI ML Prediction
        ml_score = 50
        ai_reason = "Heuristic TA fallback"
        if self.ai_model and ta_data.get('rsi'):
            try:
                # Prepare features as expected by the model
                # ['rsi', 'macd_hist', 'dist_to_sma50', 'dist_to_sma200', 'dist_to_bb_lower', 'dist_to_bb_upper', 'vol_change_1d']
                price = ta_data.get('price', 1)
                
                features = pd.DataFrame([{
                    'rsi': ta_data.get('rsi', 50),
                    'macd_hist': ta_data.get('macd_hist', 0),
                    'dist_to_sma50': (price - ta_data.get('sma50', price)) / ta_data.get('sma50', price),
                    'dist_to_sma200': (price - ta_data.get('sma200', price)) / ta_data.get('sma200', price),
                    'dist_to_bb_lower': (price - ta_data.get('bb_lower', price)) / price,
                    'dist_to_bb_upper': (ta_data.get('bb_upper', price) - price) / price,
                    'vol_change_1d': 0.0 # Approximate if volume not readily available in TA dict
                }])
                
                # Get probability of class 1 (Buy)
                prob = float(self.ai_model.predict_proba(features)[0][1])
                ml_score = int(prob * 100)
                ai_reason = f"XGBoost Prediction: {ml_score}% prob. of uptrend"
            except Exception as e:
                ai_reason = f"ML Error: {e}"

        # 3. Fundamental Analysis & Smart Money
        fund_score = 50
        fund_reason = "No fundamental data"
        smart_money = {"institutional_ownership": 0, "short_ratio": 0, "beta": 1.0}
        
        if asset_class == 'stock':
            try:
                ratios = self.provider.get_financial_ratios(ticker)
                
                # Extract Smart Money data
                smart_money["institutional_ownership"] = ratios.get("institutional_ownership", 0)
                smart_money["short_ratio"] = ratios.get("short_ratio", 0)
                smart_money["beta"] = ratios.get("beta", 1.0)
                
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
                pass

        # 4. Real-Time NLP Sentiment
        sentiment_data = self.nlp.get_news_sentiment(ticker)
        sent_score = sentiment_data['score']
        sent_reason = sentiment_data['reason']
        headlines = sentiment_data.get('headlines', [])

        # Final ML-Weighted Conviction Score (ML=50%, Fundamental=25%, Sentiment=25%)
        conviction_score = int(ml_score * 0.5 + fund_score * 0.25 + sent_score * 0.25)

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

        # Multi-Style Trade Setups (Only Long positions for Shariah compliance)
        price = ta_data.get('price', 1)
        sigma = ta_data.get('sigma', 0.02) if 'sigma' in ta_data else 0.02
        
        trade_setups = {
            "scalping": {
                "entry": round(price, 2),
                "tp": round(price * (1 + sigma * 0.5), 2),
                "sl": round(price * (1 - sigma * 0.5), 2),
                "tp_pct": round(sigma * 0.5 * 100, 1),
                "sl_pct": round(sigma * 0.5 * 100, 1)
            },
            "intraday": {
                "entry": round(price, 2),
                "tp": round(price * (1 + sigma * 1.5), 2),
                "sl": round(price * (1 - sigma * 1.0), 2),
                "tp_pct": round(sigma * 1.5 * 100, 1),
                "sl_pct": round(sigma * 1.0 * 100, 1)
            },
            "swing": {
                "entry": round(ta_data.get('sma50', price), 2), # Wait for pullback to SMA50
                "tp": round(price * (1 + sigma * 4.0), 2),
                "sl": round(price * (1 - sigma * 2.5), 2),
                "tp_pct": round(sigma * 4.0 * 100, 1),
                "sl_pct": round(sigma * 2.5 * 100, 1)
            }
        }

        return {
            "conviction": conviction_score,
            "signal": signal,
            "technical_score": ml_score,
            "technical_reason": ai_reason,
            "fundamental_score": fund_score,
            "fundamental_reason": fund_reason,
            "sentiment_score": sent_score,
            "sentiment_reason": sent_reason,
            "headlines": headlines,
            "smart_money": smart_money,
            "ta_data": ta_data,
            "trade_setups": trade_setups,
        }
