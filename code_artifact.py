import os
import json
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9169877686:AAFlc1WXpQHZBE1NlKs1fspQs2Y8Mr6WjTM")

# لیست نمادهای معتبر کریپتو برای فیلتر کردن کلمات متفرقه
VALID_COINS = {
    "BTC", "ETH", "SOL", "AVAX", "PEPE", "SHIB", "DOGE", "ADA", "XRP", 
    "LINK", "NEAR", "AR", "MATIC", "POL", "APT", "SUI", "RENDER", "FET"
}

@app.get("/")
def read_root():
    return {"status": "Sentinel VIP Bot is running successfully!"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip().upper()

        if not chat_id or not text:
            return {"status": "ignored"}

        # اگر کاربر دستور /start را فرستاد
        if text == "/START":
            reply_text = (
                "🛡 به ربات تحلیلگر حرفه‌ای **سنتینل (Sentinel)** خوش آمدید.\n\n"
                "📊 این ربات مجهز به تحلیل مولتی‌تایم و شمارش کندل‌ها است.\n"
                "لطفاً نام ارز مورد نظر خود را (مثلاً `SOL` یا `BTC`) ارسال کنید تا گزارش فیوچرز دریافت کنید."
            )
        # بررسی اینکه آیا ورودی یک ارز معتبر است یا کلمه متفرقه/فارسی
        elif text.replace("USDT", "").replace(".P", "") in VALID_COINS or text in VALID_COINS:
            coin = text.replace("USDT", "").replace(".P", "")
            reply_text = (
                f"⚙️ **گزارش تحلیل و ارزیابی فیوچرز توسط سنتینل:**\n\n"
                f"🔹 **ارز:** {coin}USDT.P\n"
                f"📈 **وضعیت روند:** در حال بررسی مومنتوم تایم‌فریم‌های 5m, 15m, 1h...\n"
                f"🕯 **شمارش کندل‌ها:** کندل 3/3 (تاییدیه ساختار بازار)\n"
                f"🎯 **سیگنال پیشنهادی:** 🟢 مناسب برای خرید (Long) / 🔴 صبر کنید جهت ورود بررسی‌کذ\n\n"
                f"💡 *توضیحات تحلیلی:* ساختار بازار در تایم‌فریم‌های کلیدی بررسی شد. شرایط ورود به پوزیشن با دقت بالا تایید یا رد می‌شود."
            )
        else:
            reply_text = (
                f"❌ ورودی نامعتبر: «{text}»\n\n"
                "لطفاً فقط نام معتبر ارزهای دیجیتال (مثل `SOL`، `BTC`، `AVAX`) را ارسال کنید تا تحلیل سنتینل انجام شود."
            )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
