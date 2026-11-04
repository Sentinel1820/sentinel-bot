import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9169877686:AAF1c1WxQHZBE1NIKs1fspQs2Y8Mr6WJtm")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# لیست چت‌آیدی‌های مجاز (VIP) - تا سقف ۱۰ نفر
ALLOWED_USERS = [int(uid.strip()) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip().isdigit()]

def send_telegram_message(chat_id: int, text: str):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        
        # بررسی محدودیت لیست مجاز VIP (سقف ۱۰ نفر)
        if ALLOWED_USERS and chat_id not in ALLOWED_USERS:
            if len(ALLOWED_USERS) < 10:
                ALLOWED_USERS.append(chat_id)
            else:
                send_telegram_message(chat_id, "⛔ دسترسی غیرمجاز: این ربات اختصاصی و محدود به لیست VIP است.")
                return {"status": "unauthorized"}
        
        if text.startswith("/start"):
            welcome_text = (
                "🤖 **به دیده‌بان اتوماتیک سنتینل خوش آمدید!**\n\n"
                "این ربات به صورت هوشمند در پس‌زمینه بازار را اسکن کرده و میم‌کوین‌ها و ارزهای داغ دارای حجم مشکوک را بدون نیاز به استعلام دستی، به صورت منظم به شما گزارش می‌دهد."
            )
            send_telegram_message(chat_id, welcome_text)
            
    return {"status": "ok"}
