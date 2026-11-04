import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9169877686:AAF1c1WxQHZBE1NIKs1fspQs2Y8Mr6WJtm")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# لیست چت‌آیدی‌های مجاز (VIP) - تا سقف ۱۰ نفر
ALLOWED_USERS = [int(uid.strip()) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip().isdigit()]

# دیکشنری برای نگهداری وضعیت روشن یا خاموش بودن ربات برای هر کاربر
USER_STATES = {}

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
        text = message.get("text", "").strip().lower()
        
        # بررسی محدودیت لیست مجاز VIP (سقف ۱۰ نفر)
        if ALLOWED_USERS and chat_id not in ALLOWED_USERS:
            if len(ALLOWED_USERS) < 10:
                ALLOWED_USERS.append(chat_id)
            else:
                send_telegram_message(chat_id, "⛔ دسترسی غیرمجاز: این ربات اختصاصی و محدود به لیست VIP است.")
                return {"status": "unauthorized"}
        
        if text.startswith("/start"):
            USER_STATES[chat_id] = "ON"
            welcome_text = (
                "🤖 **به دیده‌بان اتوماتیک سنتینل خوش آمدید!**\n\n"
                "وضعیت ربات در حال حاضر: **🟢 روشن**\n\n"
                "دستورات کنترلی:\n"
                "🔹 برای توقف موقت و استراحت، بفرستید: **خاموش**\n"
                "🔸 برای شروع مجدد و رصد بازار، بفرستید: **روشن**"
            )
            send_telegram_message(chat_id, welcome_text)
            
        elif text == "خاموش":
            USER_STATES[chat_id] = "OFF"
            send_telegram_message(chat_id, "🔴 دیده‌بان سنتینل با موفقیت **خاموش** شد. هر زمان خواستید استراحت تمام شود، کافی است بفرستید **روشن**.")
            
        elif text == "روشن":
            USER_STATES[chat_id] = "ON"
            send_telegram_message(chat_id, "🟢 دیده‌بان سنتینل **روشن** شد و رصد ۲۴ ساعته بازار و میم‌کوین‌ها مجدداً آغاز گشت.")
            
        else:
            current_state = USER_STATES.get(chat_id, "ON")
            if current_state == "OFF":
                send_telegram_message(chat_id, "💤 ربات در حال حاضر در حالت **خاموش** است. برای دریافت گزارش‌ها، لطفاً کلمه **روشن** را ارسال کنید.")
            else:
                send_telegram_message(chat_id, "✅ دیده‌بان فعال است. برای توقف موقت، کلمه **خاموش** را ارسال کنید.")
            
    return {"status": "ok"}
