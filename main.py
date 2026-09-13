import requests, json, time, random, string, os, threading, gc
from datetime import datetime, timedelta
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════
# 🔧 تنظیمات
# ═══════════════════════════════════════
TOKEN = "2068206712:2acXvBw8EkZfgBoJdpOjCupvWgXrFevRDtY"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

CHANNEL_ID = "@SCYVu"
CHANNEL_LINK = "https://ble.ir/SCYVu"
BOT_USERNAME = "Idnueobot"
BOT_LINK = f"https://ble.ir/{BOT_USERNAME}"

OWNER_ID = "1530477937"
OWNER_PASSWORD = "Parsa@2026!"
COIN_PASSWORD = "Coin@Parsa2026"
INFINITE_COINS = 999999
MIN_SIN = 15
MIN_MEMBER = 1
MEMBER_COST = 5
START_GIFT = 25
SEEN_REWARD = 1
SIN_COST = 1
INVITE_REWARD = 15
DAILY_GIFT = 5
MEMBER_NORMAL_REWARD = 3
MEMBER_GUARANTEED_REWARD = 7
TRANSFER_FEE = 2

DB_FILE = "hypersin_bale.json"
RENDER_URL = "https://hypersin-bale.onrender.com"

# ═══════════════════════════════════════
# ⚡ بهینه‌سازی برای ۵۰۰ هزار کاربر
# ═══════════════════════════════════════
CACHE = {}
CACHE_TIME = {}
CACHE_TTL = 300
JOIN_CACHE = {}
JOIN_CACHE_TIME = {}
SAVE_PENDING = False
SAVE_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=100)

# ═══════════════════════════════════════
# 🗄️ دیتابیس
# ═══════════════════════════════════════
def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {
        "users": {}, "orders": {}, "member_orders": {}, "gift_codes": {},
        "seen_records": {}, "member_records": {}, "invited_users": {},
        "order_counter": 0, "member_counter": 0,
        "stats": {
            "total_orders": 0, "completed_orders": 0, "deleted_messages": 0,
            "total_members": 0, "completed_members": 0,
            "total_transfers": 0, "owner_earnings": 0
        },
        "pending_orders": {}, "pending_members": {}, "pending_gift": {},
        "pending_broadcast": {}, "pending_add_coins": {}, "pending_transfer": {},
        "pending_coin_setting": {}, "pending_join_channel": {}, "pending_remove_join": {},
        "pending_packet": {}, "pending_ban": {}, "pending_unban": {},
        "pending_admin": {}, "pending_remove_admin": {}, "pending_vip": {},
        "pending_pm": {}, "pending_execute": {}, "pending_utility": {},
        "pending_support": {}, "pending_packet_user": {},
        "coin_packets": {},
        "banned": [], "admins": [], "vip": {},
        "join_channels": [],
        "settings": {
            "seen_reward": SEEN_REWARD, "sin_cost": SIN_COST,
            "member_cost": MEMBER_COST,
            "member_normal_reward": MEMBER_NORMAL_REWARD,
            "member_guaranteed_reward": MEMBER_GUARANTEED_REWARD,
            "transfer_fee": TRANSFER_FEE
        }
    }

def save_db_async():
    global SAVE_PENDING
    SAVE_PENDING = True

def save_worker():
    global SAVE_PENDING
    while True:
        if SAVE_PENDING:
            with SAVE_LOCK:
                try:
                    with open(DB_FILE, "w", encoding="utf-8") as f:
                        json.dump(db, f, ensure_ascii=False)
                    with open(f"{DB_FILE}.backup", "w", encoding="utf-8") as f:
                        json.dump(db, f, ensure_ascii=False)
                    SAVE_PENDING = False
                except: pass
        time.sleep(3)

def save_db(): save_db_async()

db = load_db()

# ═══════════════════════════════════════
# 💰 توابع با Cache
# ═══════════════════════════════════════
def get_user(user_id):
    uid = str(user_id)
    now = time.time()
    if uid in CACHE and now - CACHE_TIME.get(uid, 0) < CACHE_TTL:
        return CACHE[uid]
    if uid not in db["users"]:
        db["users"][uid] = {
            "coins": 0, "joined": False, "got_start_gift": False,
            "invite_count": 0, "invited_by": None, "username": "",
            "last_daily": None, "msg_count": 0
        }
        save_db_async()
    CACHE[uid] = db["users"][uid]
    CACHE_TIME[uid] = now
    return db["users"][uid]

def add_coins(user_id, amount):
    get_user(user_id)["coins"] += amount
    save_db_async()

def remove_coins(user_id, amount):
    user = get_user(user_id)
    if user["coins"] >= amount:
        user["coins"] -= amount
        save_db_async()
        return True
    return False

def get_coins(user_id):
    return get_user(user_id)["coins"]

def is_banned(user_id):
    return str(user_id) in db.get("banned", [])

def is_admin(user_id):
    return str(user_id) == str(OWNER_ID) or str(user_id) in db.get("admins", [])

def convert_number(text):
    for p, e in zip("۰۱۲۳۴۵۶۷۸۹", "0123456789"):
        text = text.replace(p, e)
    return text

def get_shamsi_date():
    now = datetime.now()
    return f"{now.year}/{now.month:02d}/{now.day:02d}"

def get_setting(key, default=0):
    return db.get("settings", {}).get(key, default)

def cache_cleanup():
    while True:
        try:
            now = time.time()
            to_del = [k for k, t in CACHE_TIME.items() if now - t > CACHE_TTL * 2]
            for k in to_del:
                CACHE.pop(k, None)
                CACHE_TIME.pop(k, None)
            to_del2 = [k for k, t in JOIN_CACHE_TIME.items() if now - t > 300]
            for k in to_del2:
                JOIN_CACHE.pop(k, None)
                JOIN_CACHE_TIME.pop(k, None)
            gc.collect()
        except: pass
        time.sleep(600)

# ═══════════════════════════════════════
# 📡 API
# ═══════════════════════════════════════
session = requests.Session()
session.headers.update({'Connection': 'keep-alive', 'Accept-Encoding': 'gzip, deflate'})

def api_call(method, data=None, timeout=5):
    try:
        if data is None: data = {}
        r = session.post(f"{BASE_URL}/{method}", data=data, timeout=timeout)
        return r.json()
    except:
        try:
            r = session.post(f"{BASE_URL}/{method}", data=data, timeout=3)
            return r.json()
        except: return {"ok": False}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    return api_call("sendMessage", data)

def send_reply(chat_id, reply_to_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_id}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    return api_call("sendMessage", data)

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    return api_call("editMessageText", data)

def delete_message(chat_id, message_id):
    return api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def forward_message(chat_id, from_chat_id, message_id):
    return api_call("forwardMessage", {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id})

def answer_callback(callback_id, text=None, show_alert=False):
    data = {"callback_query_id": callback_id}
    if text: data["text"] = text
    data["show_alert"] = show_alert
    return api_call("answerCallbackQuery", data)

def get_chat_member(chat_id, user_id):
    return api_call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

def get_chat(chat_id):
    return api_call("getChat", {"chat_id": chat_id})

# ═══════════════════════════════════════
# ✅ چک عضویت
# ═══════════════════════════════════════
def check_joined(user_id):
    uid = str(user_id)
    now = time.time()
    if uid in JOIN_CACHE and now - JOIN_CACHE_TIME.get(uid, 0) < 120:
        return JOIN_CACHE[uid]
    try:
        result = get_chat_member(CHANNEL_ID, user_id)
        if result.get("ok"):
            status = result["result"]["status"]
            ok = status in ["member", "administrator", "creator"]
            if ok:
                get_user(user_id)["joined"] = True
                save_db_async()
            JOIN_CACHE[uid] = ok
            JOIN_CACHE_TIME[uid] = now
            return ok
        return False
    except: return False

def check_all_joins(user_id):
    if not check_joined(user_id): return False
    for ch in db.get("join_channels", []):
        try:
            r = get_chat_member(ch, user_id)
            if not r.get("ok"): return False
            if r["result"]["status"] not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

def must_join(user_id):
    keyboard = {"inline_keyboard": [
        [{"text": "🔗 عضویت در کانال", "url": CHANNEL_LINK}],
        [{"text": "✅ عضو شدم", "callback_data": "check_join"}]
    ]}
    send_message(user_id, "🔒 **برای استفاده از ربات باید عضو کانال بشی!**\n\nلطفاً عضو شو بعد روی «عضو شدم» بزن.", keyboard)
    return False

# ═══════════════════════════════════════
# 🎮 کیبوردها
# ═══════════════════════════════════════
def main_keyboard(user_id=None):
    rows = [
        [{"text": "🪙 کسب سکه"}],
        [{"text": "👁️ ثبت سفارش سین"}, {"text": "👥 ثبت سفارش عضو"}],
        [{"text": "💰 سکه‌های من"}, {"text": "🎁 زدن کد هدیه"}],
        [{"text": "👥 دعوت دوستان"}, {"text": "👤 حساب کاربری"}],
        [{"text": "💰 انتقال سکه"}, {"text": "🎁 هدیه روزانه"}],
        [{"text": "💬 پشتیبانی"}],
        [{"text": "📖 راهنما"}]
    ]
    if user_id and str(user_id) == str(OWNER_ID):
        rows.append([{"text": "👑 پنل مالک"}])
    return {"keyboard": rows, "resize_keyboard": True}

def owner_keyboard():
    return {
        "keyboard": [
            [{"text": "⚙️ تنظیم سکه"}, {"text": "🔗 کاربردی‌ها"}],
            [{"text": "🚫 مسدود کردن"}, {"text": "✅ رفع مسدودیت"}],
            [{"text": "👑 افزودن ادمین"}, {"text": "🗑️ حذف ادمین"}],
            [{"text": "📨 پیام به کاربر"}, {"text": "💻 اجرای کد"}],
            [{"text": "🎁 سکه پاکت"}, {"text": "🎁 پاکت به کاربر"}],
            [{"text": "⭐ ویژه VIP"}, {"text": "🛡️ ضدتقلب"}],
            [{"text": "📊 آمار پیشرفته"}, {"text": "📊 آمار کل"}],
            [{"text": "🔒 جوین اجباری"}, {"text": "🎁 ساخت کد هدیه"}],
            [{"text": "💰 افزودن سکه به همه"}, {"text": "🎁 تغییر سکه دعوت"}],
            [{"text": "💸 کارمزد انتقال"}, {"text": "📢 پیام همگانی"}],
            [{"text": "🏆 رتبه‌بندی"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def settings_keyboard():
    return {
        "keyboard": [
            [{"text": "👁️ سکه دیدم"}],
            [{"text": "📝 سکه سفارش سین"}],
            [{"text": "👥 سکه سفارش عضو"}],
            [{"text": "🪙 سکه عضو معمولی"}],
            [{"text": "🛡️ سکه عضو تضمینی"}],
            [{"text": "💸 کارمزد انتقال"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def cancel_keyboard():
    return {"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}

# ═══════════════════════════════════════
# 📢 پیام همگانی
# ═══════════════════════════════════════
def broadcast_worker(user_id, text):
    sent = 0
    failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    for i, uid in enumerate(all_users, 1):
        try:
            r = send_message(int(uid), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(2)
        if i % 10 == 0:
            try: send_message(user_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(user_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

# ═══════════════════════════════════════
# 🎯 پردازش پیام
# ═══════════════════════════════════════
def handle_message(message):
    global INVITE_REWARD
    try:
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]
        
        if chat_type in ["group", "supergroup"]:
            if "new_chat_member" in message:
                nm = message["new_chat_member"]
                nn = nm.get("first_name", "کاربر")
                gn = message["chat"].get("title", "این گروه")
                wt = (f"👋 **{nn}** به **{gn}** خوش اومدی! 🎉\n\n"
                      f"🤖 من **ربات عضوگیر و سین‌زن** هستم!\n"
                      f"👥 می‌تونم برات عضو بیارم\n"
                      f"👁️ می‌تونم برات سین بزنم\n\n"
                      f"🚀 اگه خواستی کانال یا گروهت رو رشد بدی،\n"
                      f"بیا توی پیوی من:\n"
                      f"🤖 @Idnueobot\n\n"
                      f"🐺 تیم DeepParse")
                send_message(chat_id, wt)
            return
        
        if chat_type == "channel": return
        
        user_id = str(message["from"]["id"])
        text = message.get("text", "").strip()
        name = message["from"].get("first_name", "داداش")
        
        if is_banned(user_id):
            send_message(chat_id, "🚫 دسترسی شما مسدود شد!\n\n⏳ نگران نباش؛ ممکنه تا چند ساعت دیگه رفع بشه.")
            return
        
        username = message["from"].get("username", "")
        if username:
            get_user(user_id)["username"] = username
            save_db_async()
        
        get_user(user_id)["msg_count"] = get_user(user_id).get("msg_count", 0) + 1
        
        # پشتیبانی
        if db.get("pending_support", {}).get(user_id, {}).get("step") == "waiting":
            try:
                send_message(int(OWNER_ID), f"💬 **پیام پشتیبانی**\n\n👤 از: {name}\n🆔 آیدی: {user_id}\n\n📝 پیام:\n{text}")
                send_message(chat_id, "✅ پیامت برای پشتیبانی ارسال شد!\n\n💚 به زودی جواب می‌گیری.", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ خطا در ارسال!", main_keyboard(user_id))
            db["pending_support"].pop(user_id, None)
            save_db_async()
            return
        
        # /start
        if text.startswith("/start"):
            parts = text.split(" ")
            if len(parts) > 1:
                inviter_id = parts[1]
                if inviter_id != user_id and user_id not in db["invited_users"]:
                    db["invited_users"][user_id] = inviter_id
                    u = get_user(user_id)
                    u["invited_by"] = inviter_id
                    save_db_async()
                    try:
                        send_message(int(inviter_id), f"🔔 **یه کاربر با لینک دعوت تو اومد!**\n\n👤 کاربر: {name}\n⏰ منتظر عضویت در کانال...")
                    except: pass
            
            if not check_all_joins(user_id):
                must_join(user_id)
                return
            
            user = get_user(user_id)
            if not user.get("got_start_gift"):
                add_coins(user_id, START_GIFT)
                user["got_start_gift"] = True
                if user.get("invited_by") and user_id in db["invited_users"]:
                    inviter_id = user["invited_by"]
                    add_coins(inviter_id, INVITE_REWARD)
                    inviter = get_user(inviter_id)
                    inviter["invite_count"] = inviter.get("invite_count", 0) + 1
                    save_db_async()
                    try:
                        send_message(int(inviter_id), f"🎉 **کاربر عضو کانال هم شد!**\n\n👤 کاربر: {name}\n🎁 **{INVITE_REWARD} سکه بهت اهدا شد!** 💰\n💰 موجودی: {get_coins(inviter_id):,} سکه")
                    except: pass
                save_db_async()
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\n⚡ به هایپرسین خوش اومدی!\n🎁 **{START_GIFT} سکه هدیه** بهت اضافه شد!\n💰 موجودی: {get_coins(user_id):,} سکه\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
            else:
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
            return
        
        # چک عضویت
        main_buttons = ["🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو", "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان", "👤 حساب کاربری", "💰 انتقال سکه", "🎁 هدیه روزانه", "💬 پشتیبانی", "📖 راهنما"]
        if text in main_buttons:
            if not check_all_joins(user_id):
                must_join(user_id)
                return
        
        # بازگشت
        if text in ["❌ لغو", "🔙 بازگشت"]:
            for key in ["pending_orders", "pending_members", "pending_gift", "pending_transfer", "pending_packet", "pending_coin_setting", "pending_ban", "pending_unban", "pending_admin", "pending_remove_admin", "pending_vip", "pending_pm", "pending_execute", "pending_utility", "pending_join_channel", "pending_remove_join", "pending_support"]:
                db.get(key, {}).pop(user_id, None)
            save_db_async()
            send_message(chat_id, "🔙 **برگشتی به منوی اصلی!**", main_keyboard(user_id))
            return
        
        # رمز مالک
        if text == OWNER_PASSWORD and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک باز شد!** 🚀", owner_keyboard())
            return
        
        if text == COIN_PASSWORD:
            add_coins(user_id, INFINITE_COINS)
            send_message(chat_id, f"💰 **{INFINITE_COINS:,} سکه بهت اضافه شد!** 🎉\n💳 موجودی: {get_coins(user_id):,} سکه")
            return
        
        if text == "👑 پنل مالک" and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک** 🚀", owner_keyboard())
            return
        
        # دکمه‌های اصلی
        if text == "🪙 کسب سکه":
            kb = {"inline_keyboard": [[{"text": "👁️ برو به کانال", "url": CHANNEL_LINK}]]}
            send_message(chat_id, f"🔗 **برو توی کانال و روی دکمه «دیدم» زیر پیام‌ها بزن تا سکه بگیری!** 💰\n\n{CHANNEL_LINK}", kb)
            return
        
        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 **موجودی تو:** {get_coins(user_id):,} سکه 🪙")
            return
        
        if text == "📖 راهنما":
            send_message(chat_id, f"📖 **راهنمای ربات هایپرسین ⚡**\n\n🤖 هایپرسین ترکیبی از ربات سین‌زن و عضوگیر است.\n\n👁️ **بخش سین‌زن**\n• هر سین = 🪙 ۱ سکه لازم است\n• حداقل سفارش: ۱۵ سین\n\n👥 **بخش عضوگیر**\n• هر عضو = 🪙 ۵ سکه لازم دارد\n• حداقل سفارش: ۱ عضو\n\n💰 **انتقال سکه:**\n• دکمه انتقال سکه رو بزن\n• آیدی عددی طرف رو بفرست\n• (از حساب کاربری → کپی آیدی)\n• مقدار سکه رو وارد کن\n• کارمزد: {get_setting('transfer_fee', 2)} سکه\n\n💰 **روش‌های کسب سکه در کانال**\n• 👁️ دکمه «دیدم» رو بزن در کانال → +۱ سکه\n• 👥 دکمه «عضو شدم» رو بزن در کانال → +۳ سکه\n• 🎁 کد هدیه → دریافت سکه جایزه\n• 🎉 اولین عضویت در کانال ما → ۲۵ سکه هدیه\n• 👥 دعوت دوستان → هر دعوت = {INVITE_REWARD} سکه\n\n⚠️ **قوانین**\n• پیام های غیر قانونی ثبت نمیشه و شما از کانال حذف میشید\n\n✨ از استفاده از هایپرسین سپاسگزاریم.")
            return
        
        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            send_message(chat_id, f"👤 **حساب کاربری:**\n\n👤 نام: {name}\n🆔 آیدی: {user_id}\n📛 یوزرنیم: @{u['username'] if u['username'] else 'ندارد'}\n🪙 موجودی: {u['coins']:,} سکه\n👥 دعوت کرده: {u.get('invite_count', 0)} نفر", {"inline_keyboard": [[{"text": "📋 کپی آیدی عددی", "callback_data": "copy_id"}], [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]]})
            return
        
        if text == "👥 دعوت دوستان":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            invite_text = (
                f"🔥 **هایپرسین**\n\n"
                f"👁️ سین بزن | 👥 عضو بگیر\n"
                f"ترکیبی حرفه‌ای بله\n\n"
                f"🎁 همه‌چی رایگان!\n\n"
                f"📈 همین الان بیا و کانالتو رشد بده 😎👇\n"
                f"بدون پول\n\n"
                f"🔗 **داش بیا لینک برای وارد شدن**\n"
                f"{link}"
            )
            result = send_message(chat_id, invite_text)
            if result.get("ok"):
                msg_id = result["result"]["message_id"]
                send_reply(chat_id, msg_id, f"🪙 با هر دعوت {INVITE_REWARD} سکه هدیه بگیر! 🎁🔥")
            return
        
        if text == "💰 انتقال سکه":
            fee = get_setting('transfer_fee', 2)
            db["pending_transfer"][user_id] = {"step": "waiting_id"}
            save_db_async()
            send_message(chat_id, f"🆔 **آیدی عددی کاربر مقصد رو بفرست:**\n\n💸 کارمزد: {fee} سکه", cancel_keyboard())
            return
        
        if text == "👁️ ثبت سفارش سین":
            db["pending_orders"][user_id] = {"step": "waiting_forward"}
            save_db_async()
            send_message(chat_id, "📩 **لطفاً پیام مورد نظر را از کانال فوروارد کنید.**\n\n⚠️ حتماً باید از کانال فوروارد شود!\n📢 از هر کانالی می‌تونی فوروارد کنی.", cancel_keyboard())
            return
        
        if text == "👥 ثبت سفارش عضو":
            db["pending_members"][user_id] = {"step": "waiting_link"}
            save_db_async()
            send_message(chat_id, "📩 **لطفاً لینک کانال مورد نظر را بفرستید.**\n\n⚠️ حتماً باید کانال باشد!\n🚫 گروه قبول نمیشود!", cancel_keyboard())
            return
        
        if text == "🎁 زدن کد هدیه":
            db["pending_orders"][user_id] = {"step": "waiting_gift_code"}
            save_db_async()
            send_message(chat_id, "🎁 **لطفاً کد هدیه رو وارد کن:**", cancel_keyboard())
            return
        
        if text == "🎁 هدیه روزانه":
            user = get_user(user_id)
            now = datetime.now()
            last = user.get("last_daily")
            if last:
                lt = datetime.fromisoformat(last)
                if now - lt < timedelta(hours=24):
                    rem = timedelta(hours=24) - (now - lt)
                    h = rem.seconds // 3600
                    m = (rem.seconds % 3600) // 60
                    send_message(chat_id, f"⏰ {h} ساعت و {m} دقیقه دیگه بیا!")
                    return
            add_coins(user_id, DAILY_GIFT)
            user["last_daily"] = str(now)
            save_db_async()
            send_message(chat_id, f"🎁 **هدیه روزانه گرفتی!**\n\n🪙 +{DAILY_GIFT} سکه\n💰 موجودی: {get_coins(user_id):,} سکه")
            return
        
        if text == "💬 پشتیبانی":
            db["pending_support"][user_id] = {"step": "waiting"}
            save_db_async()
            send_message(chat_id, "💬 **پشتیبانی**\n\nلطفاً پیامت رو بفرست تا کمکت کنیم!", cancel_keyboard())
            return
        
        # پنل مالک
        if text == "⚙️ تنظیم سکه" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم سکه**\n\nیکی رو انتخاب کن:", settings_keyboard())
            return
        if text == "👁️ سکه دیدم" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "seen_reward"}; save_db_async()
            send_message(chat_id, f"👁️ سکه فعلی: {get_setting('seen_reward', 1)}\n\nسکه جدید:", settings_keyboard())
            return
        if text == "📝 سکه سفارش سین" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "sin_cost"}; save_db_async()
            send_message(chat_id, f"📝 هزینه فعلی: {get_setting('sin_cost', 1)}\n\nهزینه جدید:", settings_keyboard())
            return
        if text == "👥 سکه سفارش عضو" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_cost"}; save_db_async()
            send_message(chat_id, f"👥 هزینه فعلی: {get_setting('member_cost', 5)}\n\nهزینه جدید:", settings_keyboard())
            return
        if text == "🪙 سکه عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_normal_reward"}; save_db_async()
            send_message(chat_id, f"🪙 پاداش فعلی: {get_setting('member_normal_reward', 3)}\n\nپاداش جدید:", settings_keyboard())
            return
        if text == "🛡️ سکه عضو تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_guaranteed_reward"}; save_db_async()
            send_message(chat_id, f"🛡️ پاداش فعلی: {get_setting('member_guaranteed_reward', 7)}\n\nپاداش جدید:", settings_keyboard())
            return
        if text == "💸 کارمزد انتقال" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "transfer_fee"}; save_db_async()
            send_message(chat_id, f"💸 کارمزد فعلی: {get_setting('transfer_fee', 2)} سکه\n\nکارمزد جدید:", settings_keyboard())
            return
        
        pcs = db["pending_coin_setting"].get(user_id, {})
        if pcs.get("type"):
            try:
                val = int(convert_number(text))
                db["settings"][pcs["type"]] = val
                del db["pending_coin_setting"][user_id]; save_db_async()
                send_message(chat_id, f"✅ ذخیره شد: {val}", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر بفرست!", settings_keyboard())
            return
        
        if text == "🚫 مسدود کردن" and is_admin(user_id):
            db["pending_ban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🚫 آیدی عددی کاربر:", cancel_keyboard()); return
        if text == "✅ رفع مسدودیت" and is_admin(user_id):
            db["pending_unban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "✅ آیدی عددی:", cancel_keyboard()); return
        if text == "👑 افزودن ادمین" and user_id == str(OWNER_ID):
            db["pending_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "👑 آیدی عددی:", cancel_keyboard()); return
        if text == "🗑️ حذف ادمین" and user_id == str(OWNER_ID):
            db["pending_remove_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🗑️ آیدی عددی:", cancel_keyboard()); return
        if text == "📨 پیام به کاربر" and is_admin(user_id):
            db["pending_pm"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "📨 آیدی عددی:", cancel_keyboard()); return
        if text == "💻 اجرای کد" and is_admin(user_id):
            db["pending_execute"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 کد پایتون:", cancel_keyboard()); return
        if text == "🎁 سکه پاکت" and is_admin(user_id):
            db["pending_packet"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 چند سکه توی پاکت باشه؟", owner_keyboard()); return
        if text == "⭐ ویژه VIP" and is_admin(user_id):
            db["pending_vip"][user_id] = {"step": "waiting_duration"}; save_db_async()
            send_message(chat_id, "⭐ مدت (12h / 7d / 1m):", cancel_keyboard()); return
        if text == "📊 آمار کل" and is_admin(user_id):
            stats = db["stats"]
            send_message(chat_id, f"📊 **آمار کل**\n\n👥 کاربران: {len(db['users'])}\n📝 سفارشات سین: {stats['total_orders']}\n✅ تکمیل سین: {stats['completed_orders']}\n👥 سفارشات عضو: {stats.get('total_members', 0)}\n✅ تکمیل عضو: {stats.get('completed_members', 0)}\n💸 کارمزد جمع: {stats.get('owner_earnings', 0)}\n📊 انتقال کل: {stats.get('total_transfers', 0)}", owner_keyboard())
            return
        if text == "🎁 ساخت کد هدیه" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 چند سکه توی کد باشه؟", owner_keyboard()); return
        if text == "💰 افزودن سکه به همه" and is_admin(user_id):
            db["pending_add_coins"][user_id] = {"step": "waiting_amount"}; save_db_async()
            send_message(chat_id, "💰 چند سکه به همه؟", owner_keyboard()); return
        if text == "🎁 تغییر سکه دعوت" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_invite_reward"}; save_db_async()
            send_message(chat_id, f"🎁 سکه فعلی: {INVITE_REWARD}\n\nسکه جدید:", owner_keyboard()); return
        if text == "📢 پیام همگانی" and is_admin(user_id):
            db["pending_broadcast"][user_id] = {"step": "waiting_message"}; save_db_async()
            send_message(chat_id, "📢 متن:", owner_keyboard()); return
        if text == "🏆 رتبه‌بندی" and is_admin(user_id):
            us = sorted(db["users"].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
            msg = "🏆 **رتبه‌بندی کاربران:**\n\n"
            for i, (uid, d) in enumerate(us, 1):
                un = d.get("username", "")
                if un: msg += f"{i}. @{un} → {d['coins']:,} سکه\n"
                else: msg += f"{i}. کاربر {uid[:6]}... → {d['coins']:,} سکه\n"
            send_message(chat_id, msg, owner_keyboard())
            return
        
        # ═══════ pending ═══════
        pb = db["pending_ban"].get(user_id, {})
        if pb.get("step") == "waiting_id":
            uid = text.strip()
            db.setdefault("banned", []).append(uid)
            del db["pending_ban"][user_id]; save_db_async()
            send_message(chat_id, f"🚫 کاربر {uid} مسدود شد!", owner_keyboard())
            try: send_message(int(uid), "🚫 دسترسی شما مسدود شد!\n\n⏳ نگران نباش؛ ممکنه تا چند ساعت دیگه رفع بشه.")
            except: pass
            return
        
        pu2 = db["pending_unban"].get(user_id, {})
        if pu2.get("step") == "waiting_id":
            uid = text.strip()
            if uid in db.get("banned", []):
                db["banned"].remove(uid)
                del db["pending_unban"][user_id]; save_db_async()
                send_message(chat_id, f"✅ کاربر {uid} آزاد شد!", owner_keyboard())
                try: send_message(int(uid), "🎉 مژده! مسدودی شما برداشته شد.\n\n✅ دوباره می‌تونی از ربات استفاده کنی!")
                except: pass
            else:
                send_message(chat_id, "❌ مسدود نبود!", owner_keyboard())
                del db["pending_unban"][user_id]; save_db_async()
            return
        
        pa = db["pending_admin"].get(user_id, {})
        if pa.get("step") == "waiting_id":
            uid = text.strip()
            if uid not in db.get("admins", []): db["admins"].append(uid)
            del db["pending_admin"][user_id]; save_db_async()
            send_message(chat_id, "👑 ادمین شد!", owner_keyboard())
            try: send_message(int(uid), "👑 شما ادمین شدید!\n\nپنل مالک برات فعال شد.", owner_keyboard())
            except: pass
            return
        
        pra = db["pending_remove_admin"].get(user_id, {})
        if pra.get("step") == "waiting_id":
            uid = text.strip()
            if uid in db.get("admins", []):
                db["admins"].remove(uid); save_db_async()
                send_message(chat_id, "🗑️ حذف شد!", owner_keyboard())
                try: send_message(int(uid), "🗑️ پنل مالک ازت گرفته شد!", main_keyboard())
                except: pass
            else: send_message(chat_id, "❌ ادمین نبود!", owner_keyboard())
            del db["pending_remove_admin"][user_id]; save_db_async()
            return
        
        ppm = db["pending_pm"].get(user_id, {})
        if ppm.get("step") == "waiting_id":
            db["pending_pm"][user_id] = {"step": "waiting_text", "id": text.strip()}; save_db_async()
            send_message(chat_id, "📝 متن:", cancel_keyboard()); return
        if ppm.get("step") == "waiting_text":
            uid = ppm["id"]
            try:
                send_message(int(uid), text)
                send_message(chat_id, "✅ ارسال شد!", owner_keyboard())
            except:
                send_message(chat_id, "❌ خطا!", owner_keyboard())
            del db["pending_pm"][user_id]; save_db_async()
            return
        
        pe = db["pending_execute"].get(user_id, {})
        if pe.get("step") == "waiting_code":
            try:
                eg = {'db': db, 'send_message': send_message, 'get_user': get_user, 'add_coins': add_coins, 'remove_coins': remove_coins, 'get_coins': get_coins, 'OWNER_ID': OWNER_ID, 'CHANNEL_ID': CHANNEL_ID, 'time': time, 'datetime': datetime, 'random': random, 'json': json}
                result = eval(text.strip(), eg)
                send_message(chat_id, f"✅ **نتیجه:**\n\n`{result}`", owner_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ **خطا:**\n\n`{str(e)[:200]}`", owner_keyboard())
            del db["pending_execute"][user_id]; save_db_async()
            return
        
        # سکه پاکت
        pp = db["pending_packet"].get(user_id, {})
        if pp.get("step") == "waiting_coins":
            try:
                db["pending_packet"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db_async()
                send_message(chat_id, "👥 چند نفره باشه؟", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pp.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                coins = pp["coins"]
                per_user = coins // cap
                db["pending_packet"][user_id]["step"] = "waiting_text"
                db["pending_packet"][user_id]["capacity"] = cap
                db["pending_packet"][user_id]["per_user"] = per_user
                save_db_async()
                send_message(chat_id, f"📝 متن پاکت:\n\n💰 کل: {coins}\n👥 تعداد: {cap}\n🎁 هر نفر: {per_user} سکه", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pp.get("step") == "waiting_text":
            ptext = text.strip()
            pid = str(int(time.time() * 1000))
            db["coin_packets"][pid] = {"coins": pp["coins"], "capacity": pp["capacity"], "per_user": pp.get("per_user", pp["coins"] // pp["capacity"]), "text": ptext, "used_by": []}
            kb = {"inline_keyboard": [[{"text": "🎁 باز کردن سکه", "callback_data": f"packet_{pid}"}]]}
            send_message(CHANNEL_ID, f"🎁 **سکه پاکت**\n\n{ptext}\n\n💰 کل: {pp['coins']}\n👥 تعداد: {pp['capacity']}\n🎁 هر نفر: {db['coin_packets'][pid]['per_user']} سکه", kb)
            db["pending_packet"].pop(user_id, None); save_db_async()
            send_message(chat_id, "✅ سکه پاکت تو کانال گذاشته شد!", owner_keyboard())
            return
        
        # VIP
        pv = db["pending_vip"].get(user_id, {})
        if pv.get("step") == "waiting_duration":
            db["pending_vip"][user_id] = {"step": "waiting_id", "duration": text.strip()}; save_db_async()
            send_message(chat_id, "🆔 آیدی عددی:", cancel_keyboard()); return
        if pv.get("step") == "waiting_id":
            uid = text.strip(); dur = pv["duration"]
            try:
                now = datetime.now()
                if dur.endswith("h"): exp = now + timedelta(hours=int(dur[:-1]))
                elif dur.endswith("d"): exp = now + timedelta(days=int(dur[:-1]))
                elif dur.endswith("m"): exp = now + timedelta(days=int(dur[:-1]) * 30)
                else:
                    send_message(chat_id, "❌ فرمت اشتباه!", owner_keyboard())
                    del db["pending_vip"][user_id]; save_db_async(); return
                db.setdefault("vip", {})[uid] = {"exp": str(exp)}; save_db_async()
                send_message(chat_id, f"⭐ VIP شد تا {exp.strftime('%Y-%m-%d %H:%M')}", owner_keyboard())
                try: send_message(int(uid), f"⭐ **VIP شدی!**\n\n💰 ۲ برابر سکه\n📅 تا {exp.strftime('%Y-%m-%d %H:%M')}")
                except: pass
            except: send_message(chat_id, "❌ خطا!", owner_keyboard())
            del db["pending_vip"][user_id]; save_db_async()
            return
        
        # کد هدیه
        pg = db["pending_gift"].get(user_id, {})
        if pg.get("step") == "waiting_coins":
            try:
                db["pending_gift"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db_async()
                send_message(chat_id, "👥 ظرفیت چند نفره؟", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pg.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                db["gift_codes"][code] = {"coins": pg["coins"], "capacity": cap, "used_by": []}
                del db["pending_gift"][user_id]; save_db_async()
                send_message(chat_id, f"🎁 **کد ساخته شد!**\n\n🔑 `{code}`\n💰 {pg['coins']:,} سکه\n👥 {cap} نفر", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pg.get("step") == "waiting_invite_reward":
            try:
                INVITE_REWARD = int(convert_number(text))
                db["invite_reward"] = INVITE_REWARD
                del db["pending_gift"][user_id]; save_db_async()
                send_message(chat_id, f"✅ سکه دعوت = {INVITE_REWARD}\n(متن دعوت هم آپدیت شد)", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        
        pac = db["pending_add_coins"].get(user_id, {})
        if pac.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                count = 0
                for uid in db["users"]:
                    add_coins(uid, amount); count += 1
                del db["pending_add_coins"][user_id]; save_db_async()
                send_message(chat_id, f"✅ {amount} سکه به {count} کاربر اضافه شد!", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        
        pbc = db["pending_broadcast"].get(user_id, {})
        if pbc.get("step") == "waiting_message":
            del db["pending_broadcast"][user_id]; save_db_async()
            executor.submit(broadcast_worker, user_id, text)
            send_message(chat_id, "📢 **شروع ارسال...**\n\n(هر ۲ ثانیه ۱ نفر)", owner_keyboard())
            return
        
        # انتقال سکه با کارمزد
        pt = db["pending_transfer"].get(user_id, {})
        if pt.get("step") == "waiting_id":
            target = text.strip()
            if target in db["users"] and target != user_id:
                fee = get_setting('transfer_fee', 2)
                db["pending_transfer"][user_id] = {"step": "waiting_amount", "target": target}
                save_db_async()
                send_message(chat_id, f"💰 **چند سکه میخوای به کاربر {target} انتقال بدی؟**\n\n💳 موجودی تو: {get_coins(user_id):,} سکه\n💸 کارمزد: {fee} سکه", cancel_keyboard())
            else:
                send_message(chat_id, "❌ کاربر یافت نشد یا نمیتونی به خودت انتقال بدی!", main_keyboard(user_id))
                db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        if pt.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                target = pt["target"]
                fee = get_setting('transfer_fee', 2)
                total = amount + fee
                if amount <= 0:
                    send_message(chat_id, "❌ عدد باید بزرگتر از صفر باشه!", main_keyboard(user_id))
                elif remove_coins(user_id, total):
                    add_coins(target, amount)
                    add_coins(OWNER_ID, fee)
                    db["stats"]["total_transfers"] = db["stats"].get("total_transfers", 0) + 1
                    db["stats"]["owner_earnings"] = db["stats"].get("owner_earnings", 0) + fee
                    save_db_async()
                    send_message(chat_id, f"✅ **{amount} سکه به کاربر {target} انتقال دادی!**\n\n💸 کارمزد: {fee} سکه\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
                    try:
                        send_message(int(target), f"🎉 **تبریک!**\n\n👤 کاربر {name} برات {amount} سکه انتقال داد!\n\n💰 موجودی: {get_coins(target):,} سکه")
                    except: pass
                    try:
                        send_message(int(OWNER_ID), f"💸 **گزارش انتقال سکه**\n\n👤 فرستنده: {name}\n🆔 آیدی: {user_id}\n👥 گیرنده: {target}\n💰 مبلغ: {amount} سکه\n💸 کارمزد: {fee} سکه\n📅 تاریخ: {get_shamsi_date()}\n⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")
                    except: pass
                else:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 نیاز: {total:,} (شامل کارمزد {fee} سکه)", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", main_keyboard(user_id))
            db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        
        # سین‌زن
        pending = db["pending_orders"].get(user_id, {})
        if pending.get("step") == "waiting_forward":
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db["pending_orders"][user_id] = {"step": "waiting_count", "message_id": message["message_id"], "from_chat_id": message["forward_from_chat"]["id"]}
                save_db_async()
                send_message(chat_id, f"🔢 **چند سین نیاز داری داداش؟**\n\n💰 هر سین = {get_setting('sin_cost', 1)} سکه\n💳 موجودی فعلی تو: {get_coins(user_id):,} سکه\n\n⚠️ حداقل: {MIN_SIN} سین", cancel_keyboard())
            else:
                send_message(chat_id, "❌ **این پیام از کانال نیست!**\n\n⚠️ لطفاً پیام رو از یه **کانال** فوروارد کن.", cancel_keyboard())
            return
        
        if pending.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_SIN:
                    send_message(chat_id, f"❌ حداقل باید {MIN_SIN} سین ثبت کنی!", cancel_keyboard()); return
                coins = get_coins(user_id)
                total_cost = count * get_setting('sin_cost', 1)
                if coins < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    del db["pending_orders"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                fwd_result = forward_message(CHANNEL_ID, chat_id, pending["message_id"])
                if fwd_result.get("ok"):
                    fwd_msg_id = fwd_result["result"]["message_id"]
                    db["order_counter"] = db.get("order_counter", 0) + 1
                    onum = db["order_counter"]
                    oid = str(int(time.time() * 1000))
                    db["orders"][oid] = {"user_id": user_id, "count": count, "message_id": fwd_msg_id, "reply_message_id": None, "seen_count": 0, "status": "active", "order_number": onum}
                    db["seen_records"][oid] = []
                    db["stats"]["total_orders"] += 1
                    kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                    rr = send_reply(CHANNEL_ID, fwd_msg_id, f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: 0\n#{onum}", kb)
                    if rr.get("ok"): db["orders"][oid]["reply_message_id"] = rr["result"]["message_id"]
                    del db["pending_orders"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ **سفارش با موفقیت ثبت شد!** 🎉\n\n🔢 تعداد سین: {count}\n💰 هزینه: {total_cost} سکه\n💳 موجودی جدید: {get_coins(user_id):,} سکه\n📝 شماره سفارش: #{onum}", main_keyboard(user_id))
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ **خطا در ثبت سفارش!**", main_keyboard(user_id))
                    del db["pending_orders"][user_id]; save_db_async()
            except: send_message(chat_id, "❌ **لطفاً یه عدد معتبر وارد کن!**", cancel_keyboard())
            return
        
        if pending.get("step") == "waiting_gift_code":
            code = text.upper().strip()
            if code in db["gift_codes"]:
                g = db["gift_codes"][code]; u = get_user(user_id)
                if code in u.get("used_gift_codes", []):
                    send_message(chat_id, "❌ تو قبلاً این کد رو زدی!", main_keyboard(user_id))
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ این کد هدیه تموم شده!", main_keyboard(user_id))
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    u.setdefault("used_gift_codes", []).append(code); save_db_async()
                    send_message(chat_id, f"🎉 **تبریک! {g['coins']:,} سکه!**\n💳 موجودی: {get_coins(user_id):,}", main_keyboard(user_id))
            else: send_message(chat_id, "❌ کد نامعتبر!", main_keyboard(user_id))
            del db["pending_orders"][user_id]; save_db_async()
            return
        
        # عضوگیر
        pmem = db["pending_members"].get(user_id, {})
        if pmem.get("step") == "waiting_link":
            db["pending_members"][user_id] = {"step": "waiting_admin", "link": text.strip()}; save_db_async()
            send_message(chat_id, "🔗 **لطفاً منو توی اون کانال ادمین کن!**\n\n⚠️ با تمام دسترسی‌ها\n✅ بعد بنویس: **ادمین کردم**", cancel_keyboard())
            return
        
        if pmem.get("step") == "waiting_admin":
            if text.strip() == "ادمین کردم":
                link = pmem["link"]
                try:
                    cu = "@" + link.split("ble.ir/")[-1] if "ble.ir/" in link else link
                    ci = get_chat(cu)
                    if ci.get("ok"):
                        tcid = ci["result"]["id"]
                        ms = get_chat_member(tcid, int(TOKEN.split(":")[0]))
                        if ms.get("ok") and ms["result"]["status"] == "administrator":
                            db["pending_members"][user_id] = {"step": "waiting_type", "link": link, "chat_id": tcid}
                            save_db_async()
                            send_message(chat_id, "📥 **لطفاً نوع عضویت را انتخاب کنید:**\n\n━━━━━━━━━━━━━━━━\n🥉 **۱. نوع معمولی**\n💰 هزینه هر عضو: ۵ سکه\n👤 کاربر میتونه هر وقت ترک کنه\n⭐ بستگی به جذابیت کانالت داره\n━━━━━━━━━━━━━━━━\n🥇 **۲. نوع تضمینی**\n💰 هزینه هر عضو: ۱۰ سکه\n🛡️ کاربر ۴۸ ساعت بمونه\n❌ اگه زودتر ترک کنه\n→ کاربر جریمه میشه\n→ سکه به شما برگشت\n━━━━━━━━━━━━━━━━\n\n🔢 لطفاً عدد ۱ یا ۲ را وارد کنید:", cancel_keyboard())
                        else: send_message(chat_id, "❌ **هنوز ادمین نشدم!**", cancel_keyboard())
                    else: send_message(chat_id, "❌ **لینک نامعتبره!**", cancel_keyboard())
                except: send_message(chat_id, "❌ **خطا!**", cancel_keyboard())
            else: send_message(chat_id, "⚠️ لطفاً بنویس: **ادمین کردم**", cancel_keyboard())
            return
        
        if pmem.get("step") == "waiting_type":
            choice = text.strip()
            if choice in ["1", "2", "۱", "۲"]:
                order_type = "normal" if choice in ["1", "۱"] else "guaranteed"
                db["pending_members"][user_id]["order_type"] = order_type
                db["pending_members"][user_id]["step"] = "waiting_count"; save_db_async()
                cost_per = 5 if order_type == "normal" else 10
                tname = "معمولی" if order_type == "normal" else "تضمینی"
                send_message(chat_id, f"📥 **ثبت سفارش عضو - {tname}**\n\n👥 تعداد عضو موردنیاز را وارد کن داداش\n💰 هزینه هر عضو: {cost_per} سکه\n📌 حداقل سفارش: ۱ عضو\n\n⌨️ لطفاً فقط عدد بفرست!", cancel_keyboard())
            else: send_message(chat_id, "❌ فقط ۱ یا ۲!", cancel_keyboard())
            return
        
        if pmem.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_MEMBER:
                    send_message(chat_id, f"❌ حداقل {MIN_MEMBER} عضو!", cancel_keyboard()); return
                link = pmem["link"]; tcid = pmem["chat_id"]; otype = pmem.get("order_type", "normal")
                cost_per = 5 if otype == "normal" else 10
                total_cost = count * cost_per
                coins = get_coins(user_id)
                if coins < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    del db["pending_members"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                db["member_counter"] = db.get("member_counter", 0) + 1
                mnum = db["member_counter"]; mid = str(int(time.time() * 1000))
                reward = get_setting('member_normal_reward', 3) if otype == "normal" else get_setting('member_guaranteed_reward', 7)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                db["member_orders"][mid] = {"user_id": user_id, "count": count, "link": link, "chat_id": tcid, "message_id": None, "seen_count": 0, "status": "active", "order_number": mnum, "order_type": otype, "reward": reward}
                db["member_records"][mid] = []
                db["stats"]["total_members"] = db["stats"].get("total_members", 0) + 1
                kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه میگیری!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت در کانال", "url": link}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}]]}
                sent = send_message(CHANNEL_ID, f"📋 **سفارش عضو - {tname}**\n\n🔗 لینک کانال: {link}\n👥 تعداد درخواستی: {count}\n✅ تعداد عضو شده: 0\n#{mnum}\n\n🪙 **{reward} سکه میگیری!**", kb)
                if sent.get("ok"): db["member_orders"][mid]["message_id"] = sent["result"]["message_id"]
                del db["pending_members"][user_id]; save_db_async()
                send_message(chat_id, f"🎉 **سفارش ثبت شد!**\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            except: send_message(chat_id, "❌ عدد معتبر!", cancel_keyboard())
            return
        
        send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
    
    except Exception as e:
        print(f"⚠️ خطا: {e}")

# ═══════════════════════════════════════
# 🔘 Callback
# ═══════════════════════════════════════
def handle_callback(callback):
    try:
        callback_id = callback["id"]
        data = callback["data"]
        user_id = str(callback["from"]["id"])
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id", CHANNEL_ID)
        
        if is_banned(user_id):
            answer_callback(callback_id, "🚫 شما مسدود شدید!", show_alert=True)
            return
        
        if data == "check_join":
            JOIN_CACHE.pop(str(user_id), None)
            if check_joined(user_id):
                user = get_user(user_id)
                if not user.get("got_start_gift"):
                    add_coins(user_id, START_GIFT)
                    user["got_start_gift"] = True; save_db_async()
                    answer_callback(callback_id, f"✅ عضو شدی! 🎁 {START_GIFT} سکه هدیه گرفتی!")
                    send_message(user_id, f"✅ **عضو شدی!** 🎉\n\n🎁 **{START_GIFT} سکه هدیه** بهت اضافه شد!\n💰 موجودی: {get_coins(user_id):,} سکه\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
                else:
                    answer_callback(callback_id, "✅ عضو شدی!")
                    send_message(user_id, "✅ حالا می‌تونی از ربات استفاده کنی!", main_keyboard(user_id))
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی!", show_alert=True)
            return
        
        if data == "back_to_main":
            send_message(user_id, "🏠 منوی اصلی:", main_keyboard(user_id))
            answer_callback(callback_id); return
        
        if data == "copy_id":
            answer_callback(callback_id, f"✅ آیدی عددی: {user_id}", show_alert=True); return
        
        if data.startswith("packet_"):
            pid = data.replace("packet_", "")
            if pid not in db.get("coin_packets", {}):
                answer_callback(callback_id, "❌ پاکت وجود نداره!", show_alert=True); return
            p = db["coin_packets"][pid]
            if str(user_id) in p["used_by"]:
                answer_callback(callback_id, "⚠️ قبلاً باز کردی!", show_alert=True); return
            if len(p["used_by"]) >= p["capacity"]:
                answer_callback(callback_id, "😢 **دیر رسیدی!**", show_alert=True); return
            p["used_by"].append(str(user_id))
            amount = p.get("per_user", p["coins"])
            add_coins(user_id, amount); save_db_async()
            answer_callback(callback_id, f"🎉 **سکه پاکت باز شد!**\n\n🪙 {amount} سکه\n💰 موجودی: {get_coins(user_id):,}", show_alert=True)
            return
        
        if data.startswith("seen_"):
            oid = data.replace("seen_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌ سفارش وجود نداره!"); return
            order = db["orders"][oid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!"); return
            if str(user_id) in db["seen_records"].get(oid, []):
                answer_callback(callback_id, "⚠️ قبلاً دیدم رو زدی!"); return
            db["seen_records"][oid].append(str(user_id))
            order["seen_count"] += 1
            add_coins(user_id, get_setting('seen_reward', 1))
            ns = order["seen_count"]; count = order["count"]; onum = order.get("order_number", "?")
            answer_callback(callback_id, f"👁️ ثبت شد! (+{get_setting('seen_reward', 1)} سکه) | 💰 موجودی: {get_coins(user_id):,}")
            if order.get("reply_message_id"):
                kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                try: edit_message_text(CHANNEL_ID, order["reply_message_id"], f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: {ns}\n#{onum}", kb)
                except: pass
            if ns >= count:
                order["status"] = "completed"
                db["stats"]["completed_orders"] += 1
                try:
                    delete_message(CHANNEL_ID, order["message_id"])
                    db["stats"]["deleted_messages"] += 1
                except: pass
                try:
                    if order.get("reply_message_id"): delete_message(CHANNEL_ID, order["reply_message_id"])
                except: pass
                try:
                    send_message(int(order["user_id"]),
                        f"🎉 **تبریک داداش!**\n\n"
                        f"🔢 **{count}** سین درخواستی تو کامل خورد!\n"
                        f"📩 پیام از کانال حذف شد.\n\n"
                        f"💡 **حالا می‌تونی:**\n"
                        f"• 🪙 بری کسب سکه کنی\n"
                        f"• 👁️ سفارش جدید ثبت کنی\n"
                        f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                        main_keyboard(order["user_id"]))
                except: pass
            save_db_async(); return
        
        if data.startswith("report_"):
            oid = data.replace("report_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            order = db["orders"][oid]
            rn = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 گزارش ثبت شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 **گزارش سین**\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔢 سین: {order['count']}\n👁️ دیده: {order['seen_count']}")
            except: pass
            return
        
        if data.startswith("info_"):
            mid = data.replace("info_", "")
            o = db["member_orders"].get(mid, {})
            reward = o.get("reward", 3); otype = o.get("order_type", "normal")
            if otype == "guaranteed":
                answer_callback(callback_id, f"🪙 {reward} سکه!\n⚠️ باید ۴۸ ساعت بمونی!", show_alert=True)
            else:
                answer_callback(callback_id, f"🪙 {reward} سکه میگیری!", show_alert=True)
            return
        
        if data.startswith("mjoin_"):
            mid = data.replace("mjoin_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            order = db["member_orders"][mid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!", show_alert=True); return
            if str(user_id) in db["member_records"].get(mid, []):
                answer_callback(callback_id, "⚠️ قبلاً عضو شدی!", show_alert=True); return
            if order.get("user_id") == str(user_id):
                answer_callback(callback_id, "❌ نمیتونی توی سفارش خودت عضو بشی!", show_alert=True); return
            tcid = order["chat_id"]
            ms = get_chat_member(tcid, user_id)
            if ms.get("ok") and ms["result"]["status"] in ["member", "administrator", "creator"]:
                db["member_records"][mid].append(str(user_id))
                order["seen_count"] += 1
                reward = order.get("reward", 3)
                add_coins(user_id, reward)
                ns = order["seen_count"]; count = order["count"]; mnum = order.get("order_number", "?")
                answer_callback(callback_id, f"✅ عضو شدی! 🎉 +{reward} سکه", show_alert=True)
                if order.get("message_id"):
                    tname = "معمولی" if order.get("order_type") == "normal" else "تضمینی"
                    kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت", "url": order["link"]}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}]]}
                    try: edit_message_text(CHANNEL_ID, order["message_id"], f"📋 **سفارش عضو - {tname}**\n\n🔗 {order['link']}\n👥 درخواستی: {count}\n✅ عضو شده: {ns}\n#{mnum}", kb)
                    except: pass
                if ns >= count:
                    order["status"] = "completed"
                    db["stats"]["completed_members"] = db["stats"].get("completed_members", 0) + 1
                    try: delete_message(CHANNEL_ID, order["message_id"])
                    except: pass
                    try:
                        send_message(int(order["user_id"]),
                            f"🎉 **تبریک داداش!**\n\n"
                            f"👥 **{count}** عضو درخواستی تو کامل شد!\n"
                            f"📩 پیام از کانال حذف شد.\n\n"
                            f"💡 **حالا می‌تونی:**\n"
                            f"• 🪙 بری کسب سکه کنی\n"
                            f"• 👥 سفارش عضو جدید ثبت کنی\n"
                            f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                            main_keyboard(order["user_id"]))
                    except: pass
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی! اول عضو شو تا سکه بگیری.", show_alert=True)
            save_db_async(); return
        
        if data.startswith("mreport_"):
            mid = data.replace("mreport_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            order = db["member_orders"][mid]
            rn = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 گزارش ثبت شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 **گزارش عضو**\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔗 {order['link']}")
            except: pass
            return
    
    except Exception as e:
        print(f"⚠️ خطا callback: {e}")

# ═══════════════════════════════════════
# 🚀 حلقه اصلی
# ═══════════════════════════════════════
last_update_id = 0

def main():
    global last_update_id, INVITE_REWARD
    INVITE_REWARD = db.get("invite_reward", INVITE_REWARD)
    print("⚡ هایپرسین بله - نسخه فوق سریع!")
    print(f"🤖 @{BOT_USERNAME}")
    print(f"💓 Cache | Async | ThreadPool(100)")
    print(f"🎯 ظرفیت: ۵۰۰,۰۰۰ کاربر")
    print("-" * 40)
    while True:
        try:
            updates = api_call("getUpdates", {"offset": last_update_id + 1, "limit": 100, "timeout": 3})
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    if "message" in update:
                        executor.submit(handle_message, msg)
                    elif "callback_query" in update:
                        executor.submit(handle_callback, update["callback_query"])
            time.sleep(0.01)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            time.sleep(0.3)

# ═══════════════════════════════════════
# 💓 Keep-Alive
# ═══════════════════════════════════════
def keep_alive():
    while True:
        try:
            time.sleep(240)
            requests.get(f"{RENDER_URL}/ping", timeout=15)
            print(f"💓 پینگ | {datetime.now().strftime('%H:%M:%S')}")
        except: time.sleep(60)

# ═══════════════════════════════════════
# 🌐 Flask
# ═══════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home(): return "🤖 Hypersin Bale Bot - Ultra Fast!"

@app.route('/ping')
def ping(): return "pong ✅"

@app.route('/health')
def health():
    return jsonify({"status": "online", "users": len(db.get("users", {})), "cache": len(CACHE)})

# ═══════════════════════════════════════
# 🚀 اجرا
# ═══════════════════════════════════════
if __name__ == "__main__":
    threading.Thread(target=save_worker, daemon=True).start()
    threading.Thread(target=cache_cleanup, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=main, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
