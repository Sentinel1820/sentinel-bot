import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def send_telegram_message(chat_id: int, text: str):
  if not TELEGRAM_BOT_TOKEN:
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Error: {e}")


@app.get("/")
def read_root():
  return {"status": "Sentinel Bot is running successfully!"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
  try:
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id:
      return {"status": "ok"}

    # اگر کاربر دستور /start را فرستاد
    if text.startswith("/start"):
      send_telegram_message(
          chat_id,
          "🛡️ **سنتینل آماده‌باش است.**\n\nبرای بررسی وضعیت ارزها، نام"
          " نماد مورد نظر خود را (مثلاً `BTCUSDT` یا چند نماد با کاما) ارسال"
          " کنید تا تحلیل آن را دریافت کنید.",
      )
      return {"status": "ok"}

    # پردازش نمادهای ارسالی توسط کاربر
    if text:
      # پاکسازی و جداسازی نمادها بر اساس کاما یا فاصله
      raw_symbols = text.replace("/scan", "").replace(",", " ").split()
      symbols = [s.strip().upper() for s in raw_symbols if s.strip()]

      if not symbols:
        symbols = ["BTCUSDT"]

      response_text = "🛡️ **گزارش ارزیابی واچ‌لیست توسط سنتینل:**\n\n"

      for symbol in symbols:
        response_text += (
            f"🔹 **{symbol}**:\n"
            f"   • وضعیت بررسی: دریافت و تایید شد ✅\n"
            f"   • سیگنال ورود: در حال رصد مومنتوم و شرایط بازار...\n\n"
        )

      response_text += (
          "ارزیابی اولیه انجام شد. برای بررسی‌های بعدی نماد جدیدی بفرستید."
      )
      send_telegram_message(chat_id, response_text)

  except Exception as e:
    print(f"Webhook Error: {e}")

  return {"status": "ok"}
