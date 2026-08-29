from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import ta

app = Flask(__name__)
CORS(app)

ASSETS = {
    # Real Forex Pairs
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "USD/CHF": "USDCHF=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "NZD/USD": "NZDUSD=X",
    # Crypto Assets
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "XRP/USD": "XRP-USD",
    "LTC/USD": "LTC-USD"
}

@app.route('/api/generate-signal', methods=['GET'])
def generate_signal():
    asset_param = request.args.get('asset', 'EUR/USD')
    tf_param = request.args.get('timeframe', '5m')

    ticker_symbol = ASSETS.get(asset_param, "EURUSD=X")
    
    try:
        period = "1d" if tf_param == "1m" else "5d"
        df = yf.download(tickers=ticker_symbol, period=period, interval=tf_param, progress=False)
        
        if df.empty or len(df) < 30:
            return jsonify({"status": "error", "message": "Insufficient market data. Try another pair."})

        # Fix Series/DataFrame Extraction Issue
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df['Close'][ticker_symbol]
        else:
            close_series = df['Close']

        close_series = close_series.dropna().astype(float)
        
        # Calculate Technical Indicators
        rsi_series = ta.momentum.rsi(close_series, window=14)
        ema9_series = ta.trend.ema_indicator(close_series, window=9)
        ema21_series = ta.trend.ema_indicator(close_series, window=21)
        ema50_series = ta.trend.ema_indicator(close_series, window=50)
        
        # Safely Extract Latest Single Values as Pure Python Floats
        current_price = float(close_series.iloc[-1])
        rsi_val = float(rsi_series.iloc[-1])
        ema9 = float(ema9_series.iloc[-1])
        ema21 = float(ema21_series.iloc[-1])
        ema50 = float(ema50_series.iloc[-1])
        
        direction = "WAIT"
        confidence = "60%"
        reason = "Market consolidating. No strong breakout confirmation."
        
        tf_label = "1 MIN" if tf_param == "1m" else "5 MIN"
        
        # Strategy Logic
        if tf_param == "5m":
            if rsi_val < 38 and ema9 > ema21 and current_price > ema50:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "88%"
                reason = f"Bullish Reversal: RSI Oversold ({round(rsi_val, 2)}) + 9 EMA crossed above 21 EMA."
            elif rsi_val > 62 and ema9 < ema21 and current_price < ema50:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "88%"
                reason = f"Bearish Reversal: RSI Overbought ({round(rsi_val, 2)}) + 9 EMA crossed below 21 EMA."
            elif rsi_val < 42 and ema9 > ema21:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "75%"
                reason = f"Short-term Bullish Momentum on 5M timeframe."
            elif rsi_val > 58 and ema9 < ema21:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "75%"
                reason = f"Short-term Bearish Momentum on 5M timeframe."
        else:
            if rsi_val < 30 and ema9 > ema21:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "70%"
                reason = "Oversold RSI + 1M Scalping EMA Crossover."
            elif rsi_val > 70 and ema9 < ema21:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "70%"
                reason = "Overbought RSI + 1M Scalping EMA Crossover."

        return jsonify({
            "status": "success",
            "asset": asset_param,
            "timeframe": tf_label,
            "price": round(current_price, 5),
            "direction": direction,
            "confidence": confidence,
            "rsi": round(rsi_val, 2),
            "reason": reason,
            "time": pd.Timestamp.now().strftime('%H:%M:%S')
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
