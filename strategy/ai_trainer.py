import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The same watchlist from our signals tab
WATCHLIST = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "V", "MA", "ADBE"]
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "xgboost_brain.pkl")

def get_data_and_features(ticker: str, period="5y"):
    print(f"Fetching data for {ticker}...")
    df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
    if df.empty or len(df) < 250:
        return pd.DataFrame()
    
    # We must squeeze to ensure it's a Series, not a DataFrame, if auto_adjust is True
    # In recent yfinance, df['Close'] might be a DataFrame if multiple tickers, but we pass one
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    volume = df['Volume'].squeeze()
    
    # --- Feature Engineering (Same as technical_engine.py) ---
    
    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    
    # MACD
    macd = ta.trend.MACD(close=close)
    df['macd_hist'] = macd.macd_diff()
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mid'] = bb.bollinger_mavg()
    
    # Moving Averages
    df['sma50'] = ta.trend.SMAIndicator(close=close, window=50).sma_indicator()
    df['sma200'] = ta.trend.SMAIndicator(close=close, window=200).sma_indicator()
    
    # Relative Distances (Normalized features)
    df['dist_to_sma50'] = (close - df['sma50']) / df['sma50']
    df['dist_to_sma200'] = (close - df['sma200']) / df['sma200']
    df['dist_to_bb_lower'] = (close - df['bb_lower']) / close
    df['dist_to_bb_upper'] = (df['bb_upper'] - close) / close
    
    # Volume Change
    df['vol_change_1d'] = volume.pct_change()
    
    # --- Target Variable Creation ---
    # We want to predict if the price will go UP by > 2% in the NEXT 5 days
    future_5d_return = close.shift(-5) / close - 1
    
    # Target: 1 if future return > 0.02 (Buy), else 0 (Hold/Sell)
    df['target'] = (future_5d_return > 0.02).astype(int)
    
    # Drop rows with NaN (from indicators and shifting)
    df = df.dropna()
    
    return df

def train_model():
    print("Starting AI Training Pipeline...")
    all_data = []
    
    for ticker in WATCHLIST:
        df = get_data_and_features(ticker)
        if not df.empty:
            all_data.append(df)
            
    if not all_data:
        print("Error: No data fetched.")
        return
        
    master_df = pd.concat(all_data)
    print(f"Total training rows generated: {len(master_df)}")
    
    # Features we will use for the AI
    feature_cols = [
        'rsi', 'macd_hist', 'dist_to_sma50', 'dist_to_sma200', 
        'dist_to_bb_lower', 'dist_to_bb_upper', 'vol_change_1d'
    ]
    
    X = master_df[feature_cols]
    y = master_df['target']
    
    # Split 80% train, 20% test (to validate out-of-sample)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    print("Training XGBoost Classifier...")
    model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    print("\n--- Model Evaluation ---")
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Out-of-Sample Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=["Not Buy", "Buy"]))
    
    # Save Model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model saved successfully at: {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
