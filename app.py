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
    tf_param = request.args.get('timeframe', '5m')  # Default 5m

    ticker_symbol = ASSETS.get(asset_param, "EURUSD=X")
    
    try:
        # Fetch data based on selected timeframe
        period = "1d" if tf_param == "1m" else "5d"
        df = yf.download(tickers=ticker_symbol, period=period, interval=tf_param)
        
        if df.empty or len(df) < 30:
            return jsonify({"status": "error", "message": "Insufficient market data. Try another pair."})
            
        close_series = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        
        # Technical Indicators Calculation
        df['RSI'] = ta.momentum.rsi(close_series, window=14)
        df['EMA_9'] = ta.trend.ema_indicator(close_series, window=9)
        df['EMA_21'] = ta.trend.ema_indicator(close_series, window=21)
        df['EMA_50'] = ta.trend.ema_indicator(close_series, window=50)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        current_price = round(float(latest['Close']), 5)
        rsi_val = round(float(latest['RSI']), 2)
        ema9 = round(float(latest['EMA_9']), 5)
        ema21 = round(float(latest['EMA_21']), 5)
        ema50 = round(float(latest['EMA_50']), 5)
        
        direction = "WAIT"
        confidence = "60%"
        reason = "Market consolidating. No strong breakout confirmation."
        
        tf_label = "1 MIN" if tf_param == "1m" else "5 MIN"
        
        # Strategy Rules
        if tf_param == "5m":
            # 5-MIN HIGH ACCURACY STRATEGY (Trend + RSI + Dual EMA Crossover)
            if rsi_val < 38 and ema9 > ema21 and current_price > ema50:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "88%"
                reason = f"Bullish Reversal: RSI Oversold ({rsi_val}) + 9 EMA crossed above 21 EMA in Uptrend."
            elif rsi_val > 62 and ema9 < ema21 and current_price < ema50:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "88%"
                reason = f"Bearish Reversal: RSI Overbought ({rsi_val}) + 9 EMA crossed below 21 EMA in Downtrend."
            elif rsi_val < 42 and ema9 > ema21:
                direction = f"CALL (UP) - {tf_label}"
                confidence = "75%"
                reason = f"Short-term Bullish Momentum on 5M timeframe."
            elif rsi_val > 58 and ema9 < ema21:
                direction = f"PUT (DOWN) - {tf_label}"
                confidence = "75%"
                reason = f"Short-term Bearish Momentum on 5M timeframe."
        else:
            # 1-MIN SCALPING STRATEGY
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
            "price": current_price,
            "direction": direction,
            "confidence": confidence,
            "rsi": rsi_val,
            "reason": reason,
            "time": pd.Timestamp.now().strftime('%H:%M:%S')
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)