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
          "🛡️ **سنتینل آماده‌باش است.**\n\nفقط کافی است نام ارز مورد نظرتان"
          " (مثل `BTC` یا `IDOL`) را بفرستید تا وضعیت خرید یا عدم خرید آن"
          " در بازار فیوچرز تحلیل شود.",
      )
      return {"status": "ok"}

    # پردازش نام ارز ارسالی توسط کاربر
    if text:
      # پاکسازی و جداسازی نام ارزها و اضافه کردن خودکار پسوند فیوچرز (USDT.P)
      raw_tokens = text.replace("/scan", "").replace(",", " ").split()
      tokens = [t.strip().upper() for t in raw_tokens if t.strip()]

      if not tokens:
        tokens = ["BTC"]

      response_text = (
          "🛡️ **گزارش تحلیل و ارزیابی فیوچرز توسط سنتینل:**\n\n"
      )

      for token in tokens:
        # اگر کاربر پسوند را نگذاشته بود، خودکار USDT.P را اضافه می‌کنیم
        full_symbol = (
            token if "USDT" in token else f"{token}USDT.P"
        )

        # در اینجا منطق تحلیل و تصمیم‌گیری خرید قرار می‌گیرد
        response_text += (
            f"🔹 ارز: **{full_symbol}**\n"
            f"   • وضعیت روند: در حال بررسی مومنتوم...\n"
            f"   • سیگنال پیشنهادی: 🟢 **مناسب برای خرید (Long)** / یا 🔴"
            " **صبر کنید / ورود پرریسک**\n"
            f"   • توضیحات تحلیلی: ساختار بازار بررسی شد. شرایط ورود به پوزیشن"
            " تایید یا رد می‌شود.\n\n"
        )

      response_text += "برای بررسی ارز دیگر، نام آن را ارسال کنید."
      send_telegram_message(chat_id, response_text)

  except Exception as e:
    print(f"Webhook Error: {e}")

  return {"status": "ok"}
