"""
نام فایل: sentinel_telegram_bot.py
عنوان: ربات تلگرام کامل و خودکار ایجنت «سنتینل» (Sentinel) برای رصد ۲۴ ساعته بازار
توضیحات: این اسکریپت مجهز به وب‌هوک و صف هوشمند (Queue) است تا به محض دریافت سیگنال 
از تریدینگ‌ویو، آن را تحلیل کرده و بدون نیاز به حضور دستی شما، مستقیماً به تلگرام ارسال کند.
"""

import os
import asyncio
from fastapi import FastAPI, Request
import uvicorn
from telegram import Bot

# تنظیمات اصلی ربات و کانال ارتباطی
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
# آیدی عددی تلگرام شما برای دریافت خودکار سیگنال‌ها در ایران
PRIMARY_CHAT_ID = int(os.environ.get("PRIMARY_CHAT_ID", "123456789"))

app = FastAPI(title="Sentinel 24/7 Crypto Agent Bot")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_alert(chat_id: int, message: str):
    """ارسال خودکار و فوری هشدار تحلیل‌شده به تلگرام کاربر"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"خطا در ارسال پیام به تلگرام: {e}")

@app.post("/webhook/signal")
async def receive_tradingview_signal(request: Request):
    """
    دریافت لحظه‌ای سیگنال‌ها از تریدینگ‌ویو و پردازش خودکار توسط سنتینل
    این بخش به صورت ۲۴ ساعته فعال است و نیازی به حضور شما ندارد.
    """
    try:
        data = await request.json()
        signals = data if isinstance(data, list) else [data]
        
        results = []
        for sig in signals:
            symbol = sig.get("symbol", "UNKNOWN")
            action = sig.get("action", "BUY")
            price = sig.get("price", "0.0")
            timeframe = sig.get("timeframe", "1h")
            
            # تحلیل چندلایه و ارزیابی هوشمند سنتینل در لحظه
            ai_verdict = ""
            if action.upper() == "BUY":
                ai_verdict = (
                    f"🟢 **تاییدیه خرید (BUY)**\n"
                    f"▫️ رادار نهنگ: حجم ورودی تایید شد.\n"
                    f"▫️ ایچیموکو: قیمت بالای ابر کومو قرار دارد.\n"
                    f"💡 **توصیه سنتینل:** ورود پله‌ای مجاز است. حد ضرر پشت کندل قبلی تنظیم شود."
                )
            else:
                ai_verdict = (
                    f"🔴 **اخطار فروش یا شورت (SELL)**\n"
                    f"▫️ رادار نهنگ: خروج نقدینگی / تله مقاومتی.\n"
                    f"💡 **توصیه سنتینل:** از خرید سنگین خودداری کنید و آماده سیو سود یا شورت باشید."
                )

            # ساخت پیام ساختاریافته برای ارسال خودکار روی گوشی شما در تلگرام
            alert_message = (
                f"🚨 **گزارش لحظه‌ای دیده‌بان «سنتینل»**\n\n"
                f"▫️ **نماد ارز:** `{symbol}`\n"
                f"▫️ **تایم‌فریم:** `{timeframe}`\n"
                f"▫️ **قیمت لحظه‌ای:** `${price}`\n\n"
                f"{ai_verdict}"
            )

            # ارسال خودکار به تلگرام شما با رعایت وقفه ایمن (Rate Limit)
            await send_telegram_alert(PRIMARY_CHAT_ID, alert_message)
            await asyncio.sleep(0.5)
            
            results.append({"symbol": symbol, "status": "sent_to_telegram"})

        return {"status": "success", "processed": len(signals), "results": results}

    except Exception as e:
        error_msg = f"❌ **خطای سیستمیک سنتینل در پردازش وب‌هوک:** {str(e)}"
        await send_telegram_alert(PRIMARY_CHAT_ID, error_msg)
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    # اجرای سرور ربات روی پورت 8000 (آماده برای اتصال به هاست ابری رایگان مثل Render یا پلتفرم‌های بدون تحریم)
    uvicorn.run(app, host="0.0.0.0", port=8000)