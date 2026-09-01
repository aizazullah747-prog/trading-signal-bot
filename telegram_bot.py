import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd
import ta
from tvDatafeed import TvDatafeed, Interval

TOKEN = "8762578164:AAHwvVDhgVnGBIaezBd4G889euvjDd1EO6g"
bot = telebot.TeleBot(TOKEN)
tv = TvDatafeed()

# Pair mapping for TradingView
ASSETS = {
    "EUR/USD": ("EURUSD", "FX_IDC"),
    "GBP/USD": ("GBPUSD", "FX_IDC"),
    "USD/JPY": ("USDJPY", "FX_IDC"),
    "AUD/USD": ("AUDUSD", "FX_IDC"),
    "BTC/USD": ("BTCUSD", "BITSTAMP"),
    "ETH/USD": ("ETHUSD", "BITSTAMP")
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
    symbol_info = ASSETS.get(asset_name)
    bot.answer_callback_query(call.id, text=f"Analyzing {asset_name}...")
    
    try:
        symbol, exchange = symbol_info
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_15_minute, n_bars=100)

        if df is None or df.empty:
            bot.send_message(call.message.chat.id, f"⚠️ Data fetch failed for {asset_name}.")
            return

        close_series = df['close'].dropna().astype(float)
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

if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
