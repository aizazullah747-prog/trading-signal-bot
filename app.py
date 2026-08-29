from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import ta
import datetime

app = Flask(__name__)
CORS(app)

# Asset mapping for Yahoo Finance
ASSETS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "EUR/GBP": "EURGBP=X"
}

@app.route('/api/generate-signal', methods=['GET'])
def get_real_signal():
    asset_name = request.args.get('asset', 'EUR/USD')
    symbol = ASSETS.get(asset_name, "EURUSD=X")
    
    try:
        # Live 1-minute market data
        data = yf.download(tickers=symbol, period="1d", interval="1m", progress=False)
        
        if data.empty:
            return jsonify({"status": "error", "message": "Market Data Unavailable"})

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        close_prices = data['Close'].squeeze()
        
        # Technical Indicators Calculation
        rsi_series = ta.momentum.rsi(close=close_prices, window=14)
        ema_9_series = ta.trend.ema_indicator(close=close_prices, window=9)
        ema_21_series = ta.trend.ema_indicator(close=close_prices, window=21)
        
        current_rsi = round(float(rsi_series.iloc[-1]), 2)
        current_price = round(float(close_prices.iloc[-1]), 5)
        ema9 = float(ema_9_series.iloc[-1])
        ema21 = float(ema_21_series.iloc[-1])
        prev_ema9 = float(ema_9_series.iloc[-2])
        prev_ema21 = float(ema_21_series.iloc[-2])
        
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Strategy Logic
        if current_rsi <= 35 or (prev_ema9 < prev_ema21 and ema9 > ema21):
            direction = "CALL (UP)"
            confidence = f"{min(95, int(100 - current_rsi))}%"
            reason = "RSI Oversold / Bullish EMA Crossover"
        elif current_rsi >= 65 or (prev_ema9 > prev_ema21 and ema9 < ema21):
            direction = "PUT (DOWN)"
            confidence = f"{min(95, int(current_rsi))}%"
            reason = "RSI Overbought / Bearish EMA Crossover"
        else:
            direction = "WAIT (NO SIGNAL)"
            confidence = "50%"
            reason = "Market in Neutral Range (Risky Zone)"

        return jsonify({
            "status": "success",
            "asset": asset_name,
            "price": current_price,
            "direction": direction,
            "confidence": confidence,
            "rsi": current_rsi,
            "reason": reason,
            "time": current_time
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    print("🚀 Starting Real Live Market Signal Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)