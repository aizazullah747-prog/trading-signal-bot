import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yfinance as yf
import pandas as pd
import ta

# Dummy Web Server (Render ke Free tier ke liye)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Telegram Bot
TOKEN = "8762578164:AAHwvVDhgVnGBIaezBd4G889euvjDd1EO6g"
bot = telebot.TeleBot(TOKEN)

ASSETS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD"
}

@bot.message_handler(commands=['start', 'signal'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for pair in ASSETS.keys():
        markup.add(InlineKeyboardButton(pair, callback_data=f"sig_{pair}"))
    bot.reply_to(message, "📊 *Aizaz Trading Signal Bot*\n\nSelect Market Asset:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('sig_'))
def callback_signal(call):
    asset_name = call.data.replace('sig_', '')
    ticker_symbol = ASSETS.get(asset_name, "EURUSD=X")
    bot.answer_callback_query(call.id, text=f"Analyzing {asset_name}...")
    try:
        df = yf.download(tickers=ticker_symbol, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30:
            bot.send_message(call.message.chat.id, "⚠️ Insufficient data.")
            return

        close_series = df['Close'][ticker_symbol] if isinstance(df.columns, pd.MultiIndex) else df['Close']
        close_series = close_series.dropna().astype(float)
        rsi_val = float(ta.momentum.rsi(close_series, window=14).iloc[-1])
        ema9 = float(ta.trend.ema_indicator(close_series, window=9).iloc[-1])
        ema21 = float(ta.trend.ema_indicator(close_series, window=21).iloc[-1])
        current_price = float(close_series.iloc[-1])

        direction = "🟢 *CALL (UP)*" if ema9 > ema21 else "🔴 *PUT (DOWN)*"
        local_time = (pd.Timestamp.now() + pd.Timedelta(hours=5, minutes=30)).strftime('%H:%M:%S')

        response = (
            f"🎯 *SIGNAL GENERATED*\n\n"
            f"📈 *Asset:* {asset_name}\n"
            f"📊 *Signal:* {direction}\n"
            f"💡 *Price:* {round(current_price, 5)}\n"
            f"📉 *RSI:* {round(rsi_val, 2)}\n"
            f"🕒 *Time:* {local_time}"
        )
        bot.send_message(call.message.chat.id, response, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error: {str(e)}")

def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
