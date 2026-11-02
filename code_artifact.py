import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

@app.get("/")
def read_root():
    return {"status": "Sentinel Bot is running successfully!"}

@app.post("/webhook")
async def tradingview_webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("text", "سیگنال جدید دریافت شد.")
        send_telegram_message(f"🚨 **سیگنال فالکون**\n\n{message}")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
