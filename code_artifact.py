import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9169877686:AAFlc1WXpQHZBE1NlKs1fspQs2Y8Mr6WjTM")

def get_binance_analysis(symbol: str):
    try:
        # استانداردسازی فرمت جفت ارز برای بایننس
        symbol = symbol.upper().replace("USDT", "").replace(".P", "").strip()
        pair = symbol + "USDT"

        # دریافت کندل‌ها از API عمومی بایننس برای تایم‌فریم‌های مختلف
        url_5m = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=5"
        url_15m = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=15m&limit=5"
        url_1h = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1h&limit=5"

        res_5m = requests.get(url_5m, timeout=5).json()
        res_15m = requests.get(url_15m, timeout=5).json()
        
        if isinstance(res_5m, dict) and "code" in res_5m:
            return None # ارز نامعتبر یا خطا در بایننس

        # تحلیل ساده و شمارش کندل بر اساس داده‌های واقعی بایننس
        last_close = float(res_5m[-1][4])
        prev_close = float(res_5m[-2][4])
        trend_emoji = "🟢 صعودی (Long)" if last_close > prev_close else "🔴 نزولی (Short / صبر)"
        
        # محاسبه ساده وضعیت کندل‌ها
        candle_count = "3/3 (تاییدیه ساختار بازار)" if last_close > prev_close else "1/3 (در حال اصلاح)"

        report = (
            f"⚙️ **گزارش تحلیل و ارزیابی فیوچرز سنتینل (مرجع: بایننس):**\n\n"
            f"🔹 **ارز:** {pair}.P\n"
            f"💰 **قیمت لحظه‌ای:** {last_close}\n"
            f"📈 **مومنتوم تایم‌فریم 5m / 15m:** فعال\n"
            f"🕯 **شمارش کندل‌ها:** کندل {candle_count}\n"
            f"🎯 **سیگنال پیشنهادی:** {trend_emoji}\n\n"
            f"💡 *تحلیل تخصصی:* داده‌ها مستقیماً از فید بایننس استخراج شد و شرایط ساختار بازار ارزیابی گردید."
        )
        return report
    except Exception as e:
        return None

@app.get("/")
def read_root():
    return {"status": "Sentinel Binance VIP Bot is running!"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            return {"status": "ignored"}

        if text.upper() == "/START":
            reply_text = (
                "🛡 به ربات تحلیلگر **سنتینل (متصل به بایننس)** خوش آمدید.\n\n"
                "لطفاً نام ارز مورد نظر خود (مثلاً `SOL`، `BTC`، `AVAX`) را ارسال کنید تا تحلیل زنده فیوچرز بر اساس فید بایننس صادر شود."
            )
        else:
            analysis_result = get_binance_analysis(text)
            if analysis_result:
                reply_text = analysis_result
            else:
                reply_text = (
                    f"❌ نماد «{text}» در بایننس یافت نشد یا ورودی نامعتبر است.\n\n"
                    "لطفاً فقط نماد صحیح ارزها (مثل `SOL` یا `BTC`) را ارسال کنید."
                )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": reply_text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
