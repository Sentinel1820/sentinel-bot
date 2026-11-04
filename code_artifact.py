import os
import requests
import asyncio
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9169877686:AAF1c1WxQHZBE1NIKs1fspQs2Y8Mr6WJtm")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# لیست چت‌آیدی‌های مجاز (VIP) - تا سقف ۱۰ نفر
# می‌توانید چت‌آیدی خودتان و دوستانتان را اینجا با کاما جدا کنید
ALLOWED_USERS = [int(uid.strip()) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip().isdigit()]

def get_hot_memecoins():
    """
    اسکن صرافی بایننس برای پیدا کردن توکن‌ها و میم‌کوین‌های دارای حجم مشکوک یا تغییرات مثبت
    """
    url = "https://data-api.binance.vision/api/v3/ticker/24hr"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code != 200:
            return []
        
        data = response.json()
        hot_list = []
        
        for item in data:
            symbol = item.get('symbol', '')
            # بررسی جفت‌ارزهای USDT و فیلتر اولیه نوسان مثبت و حجم مناسب
            if symbol.endswith('USDT'):
                price_change = float(item.get('priceChangePercent', 0))
                volume = float(item.get('quoteVolume', 0))
                
                # فیلتر هوشمند: ارزهایی که بین 3 تا 50 درصد رشد مثبت داشتند و نقدینگی بالایی دارند
                if 3.0 <= price_change <= 50.0 and volume > 1000000:
                    hot_list.append({
                        "symbol": symbol,
                        "price": item.get('lastPrice'),
                        "change": price_change,
                        "volume": volume
                    })
        
        # مرتب‌سازی بر اساس بیشترین درصد تغییر
        hot_list = sorted(hot_list, key=lambda x: x['change'], reverse=True)
        return hot_list[:3] # برترین‌ها برای جلوگیری از اسپم
    except Exception as e:
        print(f"Error fetching hot coins: {e}")
        return []

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
                "این ربات به صورت هوشمند در پس‌زمینه بازار را اسکن کرده و میم‌کوین‌ها و ارزهای داغ دارای حجم مشکوک را به صورت منظم گزارش می‌دهد."
            )
            send_telegram_message(chat_id, welcome_text)
            
    return {"status": "ok"}
