# Flexible Strategy Rules for Active Signals
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
