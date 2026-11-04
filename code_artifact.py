import os
import time
import json
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# توکن ربات تلگرام خود را اینجا وارد کنید (یا از متغیر محیطی بخوانید)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# تنظیمات مدیریت کاربران (حداکثر ۱۲ نفر برای خانواده و دوستان)
MAX_USERS = 12
USERS_FILE = "authorized_users.json"
ENV_ALLOWED_USERS = os.getenv("ALLOWED_USERS", "")

# تنظیمات پایه اندیکاتور
SENSITIVITY = 5.5
ATR_PERIOD = 10
VOL_MULT = 1.8

# تایم‌فریم‌های مورد بررسی برای اسکن مولتی‌تایم
TIMEFRAMES = ["5m", "15m", "1h"]

def load_users() -> list:
    users = set()
    if ENV_ALLOWED_USERS:
        for u in ENV_ALLOWED_USERS.split(","):
            if u.strip().lstrip("-").isdigit():
                users.add(int(u.strip()))
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                for u in data:
                    users.add(int(u))
        except Exception:
            pass
    return list(users)

def save_user(chat_id: int) -> tuple[bool, str]:
    users = load_users()
    if chat_id in users:
        return True, "شما در لیست اعضای VIP سنتینل قرار دارید."
    if len(users) >= MAX_USERS:
        return False, "⛔ ظرفیت ۱۰ کاربر اختصاصی (خانواده و دوستان) تکمیل شده است."
    users.append(chat_id)
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    except Exception:
        pass
    return True, f"✅ حساب شما به عنوان کاربر شماره `{len(users)}` از `{MAX_USERS}` در رادار سنتینل ثبت شد!"

def send_telegram_message(chat_id: int, text: str):
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Send Error: {e}")

def fetch_futures_klines(symbol: str, interval: str, limit: int = 120):
    clean_sym = symbol.upper().replace("USDT.P", "").replace(".P", "").replace("/", "").replace("-", "").strip()
    if not clean_sym.endswith("USDT"):
        clean_sym += "USDT"

    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={clean_sym}&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 50:
                klines = []
                for k in data:
                    klines.append({
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                    })
                return klines, clean_sym
    except Exception:
        pass
    return None, clean_sym

def calc_ema(values: list, period: int) -> list:
    ema = [values[0]]
    k = 2 / (period + 1)
    for val in values[1:]:
        ema.append(val * k + ema[-1] * (1 - k))
    return ema

def calc_sma(values: list, period: int) -> list:
    sma = []
    for i in range(len(values)):
        if i < period - 1:
            sma.append(sum(values[: i + 1]) / (i + 1))
        else:
            sma.append(sum(values[i - period + 1 : i + 1]) / period)
    return sma

def calc_rsi(closes: list, period: int = 14) -> list:
    rsis = [50.0] * len(closes)
    if len(closes) <= period:
        return rsis
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(closes)):
        if i > period:
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        if avg_loss == 0:
            rsis[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsis[i] = 100.0 - (100.0 / (1.0 + rs))
    return rsis

def calc_atr(klines: list, period: int) -> list:
    trs = []
    for i in range(len(klines)):
        h, l = klines[i]["high"], klines[i]["low"]
        if i == 0:
            trs.append(h - l)
        else:
            pc = klines[i - 1]["close"]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = [sum(trs[:period]) / period]
    for i in range(1, len(klines)):
        if i < period:
            atr.append(sum(trs[: i + 1]) / (i + 1))
        else:
            atr.append((atr[-1] * (period - 1) + trs[i]) / period)
    return atr

def calc_ichimoku_last(klines: list):
    def donchian_at(idx, length):
        start = max(0, idx - length + 1)
        hs = [k["high"] for k in klines[start : idx + 1]]
        ls = [k["low"] for k in klines[start : idx + 1]]
        return (max(hs) + min(ls)) / 2.0

    idx = len(klines) - 2
    tenkan = donchian_at(idx, 9)
    kijun = donchian_at(idx, 26)
    disp_idx = max(0, idx - 25)
    t_past = donchian_at(disp_idx, 9)
    k_past = donchian_at(disp_idx, 26)
    span_a = (t_past + k_past) / 2.0
    span_b = donchian_at(disp_idx, 52)
    return {
        "cloud_top": max(span_a, span_b),
        "cloud_bottom": min(span_a, span_b),
    }

def analyze_single_timeframe(klines: list):
    closes = [k["close"] for k in klines]
    volumes = [k["volume"] for k in klines]
    ema20 = calc_ema(closes, 20)
    ema55 = calc_ema(closes, 55)
    vol_avg = calc_sma(volumes, 20)
    atrs = calc_atr(klines, ATR_PERIOD)
    rsis = calc_rsi(closes, 14)

    trail = [0.0] * len(klines)
    trend = [1] * len(klines)
    for i in range(1, len(klines)):
        c, pc = closes[i], closes[i - 1]
        prev_t = trail[i - 1]
        n_loss = SENSITIVITY * atrs[i]
        if c > prev_t and pc > prev_t:
            trail[i] = max(prev_t, c - n_loss)
        elif c < prev_t and pc < prev_t:
            trail[i] = min(prev_t, c + n_loss)
        elif c > prev_t:
            trail[i] = c - n_loss
        else:
            trail[i] = c + n_loss

        if c > trail[i] and ema20[i] > ema55[i]:
            trend[i] = 1
        elif c < trail[i] and ema20[i] < ema55[i]:
            trend[i] = -1
        else:
            trend[i] = trend[i - 1]

    last_idx = len(klines) - 2
    buy_sig = trend[last_idx] == 1 and trend[last_idx - 1] != 1
    sell_sig = trend[last_idx] == -1 and trend[last_idx - 1] != -1

    b_count, s_count = 999, 999
    for i in range(20, last_idx + 1):
        if trend[i] == 1 and trend[i-1] != 1:
            b_count = 0
        else:
            b_count += 1
        if trend[i] == -1 and trend[i-1] != -1:
            s_count = 0
        else:
            s_count += 1

    c = closes[last_idx]
    h, l = klines[last_idx]["high"], klines[last_idx]["low"]
    o = klines[last_idx]["open"]
    c_range = max(h - l, 1e-8)
    u_wick = h - max(o, c)
    l_wick = min(o, c) - l
    v = klines[last_idx]["volume"]
    v_avg = max(vol_avg[last_idx], 1e-8)

    is_bull_trap = (u_wick / c_range > 0.55) and (v > v_avg * 1.3)
    is_bear_trap = (l_wick / c_range > 0.55) and (v > v_avg * 1.3)
    ichi = calc_ichimoku_last(klines)
    in_cloud = ichi["cloud_bottom"] <= c <= ichi["cloud_top"]

    is_bull = trend[last_idx] == 1
    is_fake = is_bull_trap or is_bear_trap or in_cloud or (rsis[last_idx] > 78) or (rsis[last_idx] < 22)

    return {
        "is_bull": is_bull,
        "b_count": b_count,
        "s_count": s_count,
        "is_fake": is_fake,
        "reason": "تله فیک / ابر کومو" if is_fake else "حجم و روند تاییدشده"
    }

def evaluate_multi_timeframe(symbol: str):
    results = {}
    clean_sym = ""
    for tf in TIMEFRAMES:
        klines, clean_sym = fetch_futures_klines(symbol, tf)
        if not klines:
            return None, symbol
        results[tf] = analyze_single_timeframe(klines)
    return results, clean_sym

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return {"ok": True}

    if text.startswith("/start"):
        success, msg = save_user(chat_id)
        send_telegram_message(chat_id, msg + "\n\nسلام! نام هر ارز (مثل `SOL` یا `PEPE`) را بفرست تا سنتینل حکم نهایی را در ۳ تایم‌فریم اعلام کند.")
        return {"ok": True}

    users = load_users()
    if chat_id not in users:
        send_telegram_message(chat_id, "⛔ شما در لیست کاربران مجاز سنتینل نیستید. لطفاً ابتدا /start را بزنید.")
        return {"ok": True}

    if text and not text.startswith("/"):
        multi_res, clean_sym = evaluate_multi_timeframe(text)
        if not multi_res:
            send_telegram_message(chat_id, f"❌ ارز `{text}` در فیوچرز بایننس یافت نشد یا داده کافی نداشت.")
            return {"ok": True}

        msg = f"🛡️ **ارزیابی مولتی‌تایم سنتینل:** `{clean_sym}`\n━━━━━━━━━━━━━━━━━━━━\n"
        for tf, res in multi_res.items():
            is_bull = res["is_bull"]
            is_fake = res["is_fake"]
            qual = "⛔ [فیک / تله - نگیر]" if is_fake else "✅ [معتبر]"

            if is_bull and res["b_count"] <= 2:
                candle_str = f"({res['b_count'] + 1}/3)"
                status_text = f"🟢 معتبر BUY بگیر {candle_str} {qual}"
            elif not is_bull and res["s_count"] <= 2:
                candle_str = f"({res['s_count'] + 1}/3)"
                status_text = f"🔴 معتبر SELL بگیر {candle_str} {qual}"
            elif is_bull:
                status_text = f"⏳ روند صعودی (گذشته از کندل 3/3) {qual}"
            else:
                status_text = f"⏳ روند نزولی (گذشته از کندل 3/3) {qual}"

            msg += f"⏱ **تایم {tf}:**\n   └ {status_text}\n"

        msg += "━━━━━━━━━━━━━━━━━━━━\n💡 به شماره کندل‌ها (1/3 تا 3/3) و وضعیت معتبر/تله دقت کنید."
        send_telegram_message(chat_id, msg)

    return {"ok": True}
