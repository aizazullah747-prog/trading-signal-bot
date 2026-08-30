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

        # Fix Series/DataFrame Extraction
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
        
        # Safely Extract Latest Single Values
        current_price = float(close_series.iloc[-1])
        rsi_val = float(rsi_series.iloc[-1])
        ema9 = float(ema9_series.iloc[-1])
        ema21 = float(ema21_series.iloc[-1])
        
        direction = "WAIT"
        confidence = "60%"
        reason = "Market consolidating."
        
        tf_label = "1 MIN" if tf_param == "1m" else "5 MIN"
        
        # Active Flexible Strategy Rules
        if tf_param == "5m":
            if rsi_val <= 48 and ema9 > ema21:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "80%"
                reason = f"Bullish Trend: RSI ({round(rsi_val, 2)}) + Short-term EMA Crossover."
            elif rsi_val >= 52 and ema9 < ema21:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "80%"
                reason = f"Bearish Trend: RSI ({round(rsi_val, 2)}) + Short-term EMA Crossover."
            elif ema9 > ema21:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "70%"
                reason = "Bullish EMA Crossover."
            elif ema9 < ema21:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "70%"
                reason = "Bearish EMA Crossover."
        else:
            if rsi_val < 50 and ema9 > ema21:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "75%"
                reason = "1M Scalping Bullish Signal."
            else:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "75%"
                reason = "1M Scalping Bearish Signal."

        return jsonify({
            "status": "success",
            "asset": asset_param,
            "timeframe": tf_label,
            "price": round(current_price, 5),
            "direction": direction,
            "confidence": confidence,
            "rsi": round(rsi_val, 2),
            "reason": reason,
           "time": (pd.Timestamp.now() + pd.Timedelta(hours=5, minutes=30)).strftime('%H:%M:%S')
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
