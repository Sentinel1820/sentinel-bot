import os
import time
import json
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9169877686:AAFlc1WXpQHZBE1NlKs1fspQs2Y8Mr6WjTM")

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

        if not chat_id or not text:
            return {"status": "ignored"}

        # پاسخ نمونه برای تست عملکرد ربات
        reply_text = f"⚙️ گزارش تحلیل سنتینل:\n* ارز: {text.upper()}\n* وضعیت: معتبر BUY بگیر ✅"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
