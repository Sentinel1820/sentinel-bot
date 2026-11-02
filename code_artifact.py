import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# توکن ربات تلگرام که از BotFather گرفته‌اید
BOT_TOKEN = os.environ.get("BOT_TOKEN")


@app.route("/webhook", methods=["POST"])
def webhook():
  data = request.get_json()
  if not data:
    return "OK", 200

  # بررسی پیام‌های دریافتی از تلگرام
  if "message" in data:
    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text.startswith("/start"):
      send_telegram_message(
          chat_id,
          "🛡️ **سنتینل آماده‌باش است.**\n\nبرای بررسی واچ‌لیست، کافی است نماد"
          " ارزها را با کاما (مثلاً: `BTC,ETH,SOL`) یا دستور `/scan` برای من"
          " بفرستید تا وضعیت خرید آن‌ها را تحلیل کنم.",
      )

    elif text:
      # پردازش واچ‌لیست ارسالی از سمت کاربر
      symbols = [
          s.strip().upper() for s in text.replace("/scan", "").split(",") if s
      ]
      if not symbols:
        symbols = ["BTCUSDT", "ETHUSDT"]

      response_text = "🛡️ **گزارش تحلیل واچ‌لیست توسط سنتینل:**\n\n"

      for symbol in symbols:
        # پاکسازی نام ارز برای انطباق با فرمت صرافی
        if not symbol.endswith("USDT") and not symbol.endswith("USDC"):
          symbol += "USDT"

        # اینجا می‌توانید منطق تحلیلی دلخواه (یا اتصال به صرافی) را قرار دهید
        # به عنوان نمونه وضعیت حرکتی بررسی می‌شود:
        response_text += (
            f"🔹 **{symbol}**:\n"
            f"   • وضعیت روند: در حال رصد مومنتوم...\n"
            f"   • سیگنال ورود: بررسی شرایط اسمارت مانی 🟢/🔴\n\n"
        )

      response_text += "ارزیابی انجام شد. برای بررسی مجدد واچ‌لیست جدیدی بفرستید."
      send_telegram_message(chat_id, response_text)

  return "OK", 200


def send_telegram_message(chat_id, text):
  if not BOT_TOKEN:
    return
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  requests.post(url, json=payload)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
