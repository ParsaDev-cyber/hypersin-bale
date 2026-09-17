# ═══════════════════════════════════════
# 🤖 هایپرسین بله - نسخه کامل
# ═══════════════════════════════════════
import requests, json, time, random, string, os, threading, gc, re
from datetime import datetime, timedelta
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor

# ═══ تنظیمات ═══
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
START_GIFT = 25
DB_FILE = "hypersin_bale.json"
RENDER_URL = "https://hypersin-bale.onrender.com"
# ═══ پایان بخش ۱ ═══
# ═══ Cache ═══
CACHE = {}; CACHE_TIME = {}; CACHE_TTL = 300
JOIN_CACHE = {}; JOIN_CACHE_TIME = {}
SAVE_PENDING = False
SAVE_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=500)


def default_db():
    return {
        "users": {}, "orders": {}, "member_orders": {}, "gift_codes": {},
        "seen_records": {}, "member_records": {}, "invited_users": {},
        "order_counter": 0, "member_counter": 0,
        "stats": {"total_orders":0,"completed_orders":0,"deleted_messages":0,
                  "total_members":0,"completed_members":0,"total_transfers":0,
                  "owner_earnings":0,"ban_count":0,"unban_count":0},
        "pending_orders":{}, "pending_members":{}, "pending_gift":{},
        "pending_broadcast":{}, "pending_add_coins":{}, "pending_transfer":{},
        "pending_coin_setting":{}, "pending_join_channel":{},
        "pending_remove_join":{}, "pending_packet":{}, "pending_ban":{},
        "pending_unban":{}, "pending_admin":{}, "pending_remove_admin":{},
        "pending_vip":{}, "pending_pm":{}, "pending_execute":{},
        "pending_utility":{}, "pending_support":{}, "pending_packet_user":{},
        "pending_gift_make":{},
        "coin_packets":{}, "banned":[], "admins":[],
        "join_channels":[], "rewarded_users":[], "restored_users":[],
        "settings": {
            "seen_reward":1, "seen_reward_vip":3, "sin_cost":1,
            "member_cost":5, "member_cost_vip":2,
            "member_cost_guaranteed":10, "member_cost_guaranteed_vip":5,
            "member_normal_reward":3, "member_normal_reward_vip":10,
            "member_guaranteed_reward":7, "member_guaranteed_reward_vip":15,
            "transfer_fee":2, "daily_gift":5, "invite_reward":15,
            "start_gift":25, "restore_max":700,
            "normal_penalty":3, "normal_back":2,
            "guaranteed_penalty":7, "guaranteed_back":5
        },
        "recovery_enabled": True,
        "vip_expiry": {}
    }


def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return default_db()


db = load_db()
for k, v in default_db().items():
    if k not in db: db[k] = v


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
# ═══ پایان بخش ۲ ═══
# ═══ توابع کاربر ═══
def get_user(user_id):
    uid = str(user_id)
    now = time.time()
    if uid in CACHE and now - CACHE_TIME.get(uid, 0) < CACHE_TTL:
        return CACHE[uid]
    if uid not in db["users"]:
        db["users"][uid] = {
            "coins": 0, "joined": False, "got_start_gift": False,
            "invite_count": 0, "invited_by": None, "username": "",
            "first_name": "", "last_daily": None, "msg_count": 0,
            "restored": False, "wheel_today": "", "wheel_count": 0
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


def remove_coins_force(user_id, amount):
    user = get_user(user_id)
    user["coins"] -= amount
    save_db_async()
    return True


def get_coins(user_id):
    return get_user(user_id)["coins"]


def is_banned(user_id):
    return str(user_id) in db.get("banned", [])


def is_admin(user_id):
    return str(user_id) == str(OWNER_ID) or str(user_id) in db.get("admins", [])


def is_vip(user_id):
    uid = str(user_id)
    if uid in db.get("vip_expiry", {}):
        try:
            exp = datetime.fromisoformat(db["vip_expiry"][uid])
            if datetime.now() < exp:
                return True
            else:
                del db["vip_expiry"][uid]
                save_db_async()
        except: pass
    return False


def get_setting(key, default=0):
    return db.get("settings", {}).get(key, default)


def convert_number(text):
    for p, e in zip("۰۱۲۳۴۵۶۷۸۹", "0123456789"):
        text = text.replace(p, e)
    return text


def get_shamsi_date():
    now = datetime.now()
    return f"{now.year}/{now.month:02d}/{now.day:02d}"


def cache_cleanup():
    while True:
        try:
            now = time.time()
            for k in [k for k, t in CACHE_TIME.items() if now - t > CACHE_TTL * 2]:
                CACHE.pop(k, None); CACHE_TIME.pop(k, None)
            for k in [k for k, t in JOIN_CACHE_TIME.items() if now - t > 300]:
                JOIN_CACHE.pop(k, None); JOIN_CACHE_TIME.pop(k, None)
            gc.collect()
        except: pass
        time.sleep(600)
# ═══ پایان بخش ۳ ═══
# ═══ API Session ═══
session = requests.Session()
session.headers.update({'Connection': 'keep-alive', 'Accept-Encoding': 'gzip, deflate'})
adapter = requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200)
session.mount('https://', adapter)


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
# ═══ پایان بخش ۴ ═══
# ═══ چک عضویت ═══
def check_joined_single(user_id, channel):
    try:
        r = get_chat_member(channel, user_id)
        if r.get("ok"):
            return r["result"]["status"] in ["member", "administrator", "creator"]
    except: pass
    return False


def check_joined(user_id):
    uid = str(user_id); now = time.time()
    if uid in JOIN_CACHE and now - JOIN_CACHE_TIME.get(uid, 0) < 120:
        return JOIN_CACHE[uid]
    ok = check_joined_single(user_id, CHANNEL_ID)
    if ok:
        get_user(user_id)["joined"] = True
        save_db_async()
    JOIN_CACHE[uid] = ok; JOIN_CACHE_TIME[uid] = now
    return ok


def check_all_joins(user_id):
    if not check_joined(user_id): return False
    for ch in db.get("join_channels", []):
        if not check_joined_single(user_id, ch):
            return False
    return True


def must_join(user_id):
    kb_rows = [[{"text": "🔗 عضویت در کانال", "url": CHANNEL_LINK}]]
    for ch in db.get("join_channels", []):
        if ch.startswith("@"):
            kb_rows.append([{"text": f"🔗 {ch}", "url": f"https://ble.ir/{ch[1:]}"}])
        else:
            kb_rows.append([{"text": f"🔗 {ch}", "url": ch}])
    kb_rows.append([{"text": "✅ عضو شدم", "callback_data": "check_join"}])
    keyboard = {"inline_keyboard": kb_rows}
    send_message(user_id, "🔒 برای استفاده از ربات باید عضو کانال بشی!\n\nلطفاً عضو شو بعد روی «عضو شدم» بزن.", keyboard)
    return False
# ═══ پایان بخش ۵ ═══
# ═══ چک ترک معمولی ═══
def check_normal_leave(uid, order):
    try:
        join_time_str = order.get("join_times", {}).get(str(uid))
        if not join_time_str: return
        jt = datetime.fromisoformat(join_time_str)
        passed = (datetime.now() - jt).total_seconds()
        if passed >= 300: return
        if str(uid) in order.get("penalized", {}): return
        penalty = get_setting("normal_penalty", 3)
        back = get_setting("normal_back", 2)
        u_coins = get_coins(uid)
        actual_penalty = min(penalty, u_coins)
        if actual_penalty > 0:
            remove_coins_force(uid, actual_penalty)
        add_coins(order["user_id"], back)
        order.setdefault("penalized", {})[str(uid)] = True
        save_db_async()
        try:
            send_message(int(uid), f"⚠️ ترک سفارش معمولی!\n\n🚫 زودتر از ۵ دقیقه ترک کردی!\n\n⏰ زمان: {int(passed)} ثانیه\n💰 جریمه: {actual_penalty} سکه کم شد")
        except: pass
    except: pass
# ═══ پایان بخش ۶ ═══
# ═══ چک ترک تضمینی ═══
def check_guaranteed_leave(uid, order):
    try:
        join_time_str = order.get("join_times", {}).get(str(uid))
        if not join_time_str: return
        jt = datetime.fromisoformat(join_time_str)
        passed = (datetime.now() - jt).total_seconds()
        if passed >= 172800: return
        if str(uid) in order.get("penalized", {}): return
        penalty = get_setting("guaranteed_penalty", 7)
        back = get_setting("guaranteed_back", 5)
        u_coins = get_coins(uid)
        actual_penalty = min(penalty, u_coins)
        if actual_penalty > 0:
            remove_coins_force(uid, actual_penalty)
        add_coins(order["user_id"], back)
        order.setdefault("penalized", {})[str(uid)] = True
        save_db_async()
        try:
            send_message(int(uid),
                f"⚠️ شما کانال رو قبل از ۴۸ ساعت ترک کردید!\n\n"
                f"📢 کانال: {order.get('link', '?')}\n"
                f"📋 نوع سفارش: تضمینی\n"
                f"⏰ باید ۴۸ ساعت عضو می‌ماندید!\n\n"
                f"💰 {actual_penalty} سکه از موجودی شما کم شد.\n"
                f"💳 موجودی: {get_coins(uid):,} سکه"
            )
        except: pass
        try:
            owner_order_id = order.get("user_id")
            send_message(int(owner_order_id),
                f"🔔 یه کاربر کانال رو قبل از ۴۸ ساعت ترک کرد!\n\n"
                f"📢 کانال: {order.get('link', '?')}\n"
                f"📋 نوع سفارش: تضمینی\n\n"
                f"💰 {back} سکه به موجودی شما برگشت داده شد.\n"
                f"💳 موجودی: {get_coins(owner_order_id):,} سکه"
            )
        except: pass
    except: pass


def check_members_leaves():
    while True:
        try:
            time.sleep(10)
            for mid, order in list(db.get("member_orders", {}).items()):
                if order.get("status") != "active": continue
                tcid = order.get("chat_id")
                if not tcid: continue
                records = db.get("member_records", {}).get(mid, [])
                for uid in list(records):
                    try:
                        ms = get_chat_member(tcid, int(uid))
                        is_member = ms.get("ok") and ms["result"]["status"] in ["member", "administrator", "creator"]
                        if not is_member:
                            otype = order.get("order_type", "normal")
                            if otype == "guaranteed":
                                check_guaranteed_leave(uid, order)
                            elif otype == "normal":
                                check_normal_leave(uid, order)
                            if uid in records:
                                records.remove(uid)
                            save_db_async()
                    except: pass
        except: pass
        time.sleep(10)
# ═══ پایان بخش ۷ ═══
# ═══ کیبورد اصلی ═══
def main_keyboard(user_id=None):
    rows = [
        [{"text": "🪙 کسب سکه"}],
        [{"text": "👁️ ثبت سفارش سین"}, {"text": "👥 ثبت سفارش عضو"}],
        [{"text": "💰 سکه‌های من"}, {"text": "🎁 زدن کد هدیه"}],
        [{"text": "👥 دعوت دوستان"}, {"text": "👤 حساب کاربری"}],
        [{"text": "💰 انتقال سکه"}],
        [{"text": "📖 راهنما"}]
    ]
    if user_id and str(user_id) == str(OWNER_ID):
        rows.append([{"text": "👑 پنل مالک"}])
    return {"keyboard": rows, "resize_keyboard": True}
# ═══ پایان بخش ۸ ═══
# ═══ کیبورد مالک ═══
def owner_keyboard():
    return {"keyboard": [
        [{"text": "⚙️ تنظیم سکه"}, {"text": "🔗 کاربردی‌ها"}],
        [{"text": "🚫 مسدود کردن"}, {"text": "✅ رفع مسدودیت"}],
        [{"text": "👑 افزودن ادمین"}, {"text": "🗑️ حذف ادمین"}],
        [{"text": "📨 پیام به کاربر"}, {"text": "💻 اجرای کد"}],
        [{"text": "🎁 سکه پاکت"}, {"text": "🎁 پاکت به کاربر"}],
        [{"text": "⭐ کاربر ویژه"}, {"text": "🛡️ ضدتقلب"}],
        [{"text": "📊 آمار پیشرفته"}, {"text": "📊 آمار کل"}],
        [{"text": "🔒 جوین اجباری"}, {"text": "🎁 ساخت کد هدیه"}],
        [{"text": "💰 افزودن سکه به همه"}, {"text": "🎁 تغییر سکه دعوت"}],
        [{"text": "🎮 شروع بازی"}, {"text": "📢 پیام همگانی"}],
        [{"text": "🏆 رتبه‌بندی"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}


# ═══ کیبورد تنظیم سکه ═══
def settings_keyboard():
    return {"keyboard": [
        [{"text": "👁️ سکه دیدم (عادی)"}, {"text": "👁️ سکه دیدم (ویژه)"}],
        [{"text": "📝 سکه سفارش سین"}],
        [{"text": "👥 هزینه عضو (عادی)"}, {"text": "👥 هزینه عضو (ویژه)"}],
        [{"text": "🛡️ هزینه تضمینی (عادی)"}, {"text": "🛡️ هزینه تضمینی (ویژه)"}],
        [{"text": "🪙 پاداش معمولی (عادی)"}, {"text": "🪙 پاداش معمولی (ویژه)"}],
        [{"text": "🛡️ پاداش تضمینی (عادی)"}, {"text": "🛡️ پاداش تضمینی (ویژه)"}],
        [{"text": "💸 کارمزد انتقال"}],
        [{"text": "🎁 هدیه روزانه"}, {"text": "👥 سکه دعوت"}],
        [{"text": "🎁 هدیه استارت"}, {"text": "🔄 سقف بازیابی"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}


def cancel_keyboard():
    return {"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}
# ═══ پایان بخش ۹ ═══
# ═══ پیام همگانی سریع ═══
def broadcast_worker(user_id, text):
    sent = 0; failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    send_message(user_id, f"📢 شروع ارسال پیام همگانی...\n\n👥 کل: {total:,} نفر\n⏳ صبر کن...")
    batch = []
    for i, uid in enumerate(all_users, 1):
        batch.append(uid)
        if len(batch) >= 30:
            for u in batch:
                try:
                    r = send_message(int(u), text)
                    if r.get("ok"): sent += 1
                    else: failed += 1
                except: failed += 1
            batch = []
            time.sleep(1)
            try: send_message(user_id, f"📊 پیشرفت:\n\n✅ موفق: {sent:,}\n❌ ناموفق: {failed:,}\n📈 {i:,}/{total:,}")
            except: pass
    for u in batch:
        try:
            r = send_message(int(u), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
    send_message(user_id, f"📢 ارسال کامل شد!\n\n✅ موفق: {sent:,}\n❌ ناموفق: {failed:,}\n📊 کل: {total:,}", owner_keyboard())
# ═══ پایان بخش ۱۰ ═══
# ═══ شروع handle_message ═══
def handle_message(message):
    global MIN_SIN, MIN_MEMBER
    try:
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]

        if chat_type in ["group", "supergroup"]:
            if "new_chat_member" in message:
                nm = message["new_chat_member"]
                nn = nm.get("first_name", "کاربر")
                gn = message["chat"].get("title", "این گروه")
                send_message(chat_id, f"👋 {nn} به {gn} خوش اومدی! 🎉\n\n🤖 من ربات عضوگیر و سین‌زن هستم!\n\n👥 می‌تونم برات عضو واقعی بیارم\n👁️ می‌تونم برات سین بزنم\n\n🚀 اگه خواستی کانال یا گروهت رو رشد بدی، بیا توی پیوی من:\n\n🤖 @Idnueobot\n\n💚 تیم DeepParse")
            return

        if chat_type == "channel": return

        user_id = str(message["from"]["id"])
        text = message.get("text", "").strip()
        name = message["from"].get("first_name", "داداش")

        if is_banned(user_id):
            send_message(chat_id, "🚫 دسترسی شما مسدود شده!\n\n⏳ نگران نباش، ممکنه به‌زودی رفع بشه.\n📩 اگه فکر می‌کنی اشتباه شده، به پشتیبانی پیام بده.")
            return

        username = message["from"].get("username", "")
        if username:
            get_user(user_id)["username"] = username
            save_db_async()
        get_user(user_id)["first_name"] = name
        get_user(user_id)["msg_count"] = get_user(user_id).get("msg_count", 0) + 1

        # ═══ پشتیبانی ═══
        if db.get("pending_support", {}).get(user_id, {}).get("step") == "waiting":
            if text in ["🔙 بازگشت", "❌ لغو"]:
                db["pending_support"].pop(user_id, None); save_db_async()
                send_message(chat_id, "🔙 برگشتی به منوی اصلی!", main_keyboard(user_id)); return
            try:
                send_message(int(OWNER_ID), f"💬 پیام پشتیبانی جدید\n\n👤 نام: {name}\n🆔 آیدی: {user_id}\n📛 یوزرنیم: @{username if username else 'ندارد'}\n\n📝 پیام:\n{text}")
                send_message(chat_id, "✅ پیامت برای پشتیبانی ارسال شد!\n\n💚 به زودی جواب می‌گیری.", main_keyboard(user_id))
            except: send_message(chat_id, "❌ خطا در ارسال! دوباره تلاش کن.", main_keyboard(user_id))
            db["pending_support"].pop(user_id, None); save_db_async(); return
# ═══ پایان بخش ۱۱ ═══
        # ═══ /start ═══
        if text.startswith("/start"):
            parts = text.split(" ")
            if len(parts) > 1:
                inviter_id = parts[1]
                if inviter_id != user_id and user_id not in db["invited_users"]:
                    db["invited_users"][user_id] = inviter_id
                    get_user(user_id)["invited_by"] = inviter_id
                    save_db_async()
                    try:
                        send_message(int(inviter_id), f"🔔 کاربر با لینک دعوت تو اومد!\n\n👤 نام: {name}\n\n⏳ منتظر عضویت تو کانال...\n\n🎁 وقتی عضو کانال بشه، {get_setting('invite_reward', 15)} سکه بهت اهدا میشه!\n\n💡 پس زودتر دعوتش کن!")
                    except: pass
            if not check_all_joins(user_id):
                must_join(user_id); return
            user = get_user(user_id)
            if not user.get("got_start_gift"):
                add_coins(user_id, get_setting("start_gift", 25))
                user["got_start_gift"] = True
                inviter_id = user.get("invited_by")
                if inviter_id and user_id in db["invited_users"] and user_id not in db.get("rewarded_users", []):
                    reward = get_setting("invite_reward", 15)
                    add_coins(inviter_id, reward)
                    inviter = get_user(inviter_id)
                    inviter["invite_count"] = inviter.get("invite_count", 0) + 1
                    db.setdefault("rewarded_users", []).append(user_id)
                    save_db_async()
                    try:
                        send_message(int(inviter_id), f"🎉 کاربر عضو کانال شد! آفرین! 🎊\n\n👤 کاربر: {name}\n\n🎁 {reward} سکه بهت اهدا شد! 💰\n💰 موجودی جدید: {get_coins(inviter_id):,} سکه\n\n👥 تعداد کل دعوتات: {inviter['invite_count']} نفر\n\n🔥 ادامه بده، جایزه بیشتر بگیر!")
                    except: pass
                save_db_async()
                send_message(chat_id, f"👋 سلام {name} جان! 😎\n\n⚡ به هایپرسین خوش اومدی!\n\n🎁 {get_setting('start_gift', 25)} سکه هدیه بهت دادیم!\n💰 موجودی تو: {get_coins(user_id):,} سکه 🪙\n\n━━━━━━━━━━━━━━━━\n📌 هایپرسین چیکار می‌کنه؟\n━━━━━━━━━━━━━━━━\n👁️ سین‌زن — بازدید پیام‌های کانالت\n👥 عضوگیر — عضو واقعی برای کانالت\n🪙 سکه — با دعوت و فعالیت جمع کن\n🎁 جایزه — روزانه، گردونه، کد هدیه\n\n━━━━━━━━━━━━━━━━\n💡 برای شروع:\n━━━━━━━━━━━━━━━━\n• 🪙 کسب سکه → بفهم چطور سکه بگیری\n• 📖 راهنما → همه چیز رو توضیح دادیم\n• 👤 حساب کاربری → آیدی و موجودیت\n\n👇 از دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
            else:
                send_message(chat_id, f"👋 سلام {name} جان! 😎\n\nخوش برگشتی!\n💰 موجودی تو: {get_coins(user_id):,} سکه 🪙\n\n👇 از دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
            return
# ═══ پایان بخش ۱۲ ═══
        # ═══ چک عضویت دکمه‌ها ═══
        main_buttons = ["🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو", "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان", "👤 حساب کاربری", "💰 انتقال سکه", "📖 راهنما"]
        if text in main_buttons:
            if not check_all_joins(user_id):
                must_join(user_id); return

        if text in ["❌ لغو", "🔙 بازگشت"]:
            for key in ["pending_orders","pending_members","pending_gift","pending_transfer","pending_packet","pending_coin_setting","pending_ban","pending_unban","pending_admin","pending_remove_admin","pending_vip","pending_pm","pending_execute","pending_utility","pending_join_channel","pending_remove_join","pending_support","pending_gift_make"]:
                db.get(key, {}).pop(user_id, None)
            save_db_async()
            send_message(chat_id, "🔙 برگشتی به منوی اصلی!", main_keyboard(user_id)); return

        if text == OWNER_PASSWORD and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 پنل مالک باز شد! 🚀\n\nهمه امکانات ربات تو دستته. یکی رو انتخاب کن:", owner_keyboard()); return
        if text == COIN_PASSWORD:
            add_coins(user_id, INFINITE_COINS)
            send_message(chat_id, f"💰 {INFINITE_COINS:,} سکه بهت اضافه شد! 🎉\n\n💳 موجودی جدید: {get_coins(user_id):,} سکه 🪙\n\n🔥 حالا هرچی خواستی بخر!"); return
        if text == "👑 پنل مالک" and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 پنل مالک 🚀\n\nیکی رو انتخاب کن:", owner_keyboard()); return
# ═══ پایان بخش ۱۳ ═══
        # ═══ سکه‌های من ═══
        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 موجودی تو: {get_coins(user_id):,} سکه 🪙")
            return

        # ═══ کسب سکه ═══
        if text == "🪙 کسب سکه":
            kb = {"inline_keyboard": [[{"text": "🔗 برو به کانال", "url": CHANNEL_LINK}]]}
            send_message(chat_id,
                f"🔗 برو توی کانال و روی دکمه «دیدم» زیر پیام‌ها بزن تا سکه بگیری! 💰\n\n"
                f"{CHANNEL_LINK}",
                kb
            )
            return

        # ═══ راهنما ═══
        if text == "📖 راهنما":
            send_message(chat_id,
                f"📖 راهنمای ربات هایپرسین ⚡\n\n"
                f"🤖 هایپرسین ترکیبی از ربات سین‌زن و عضوگیر است.\n\n"
                f"👁️ بخش سین‌زن\n"
                f"• هر سین = 🪙 {get_setting('sin_cost',1)} سکه\n"
                f"• حداقل سفارش: {MIN_SIN} سین\n\n"
                f"👥 بخش عضوگیر\n"
                f"• هر عضو = 🪙 {get_setting('member_cost',5)} سکه\n"
                f"• حداقل سفارش: {MIN_MEMBER} عضو\n\n"
                f"💰 روش‌های کسب سکه:\n"
                f"• 👁️ دکمه «دیدم» → +{get_setting('seen_reward',1)} سکه\n"
                f"• 🎁 هدیه روزانه → +{get_setting('daily_gift',5)} سکه\n"
                f"• 👥 دعوت دوستان → +{get_setting('invite_reward',15)} سکه\n"
                f"• 🎡 گردونه شانس → جایزه\n\n"
                f"✨ از استفاده از هایپرسین سپاسگزاریم."
            )
            return

        # ═══ حساب کاربری ═══
        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            send_message(chat_id,
                f"👤 حساب کاربری:\n\n"
                f"👤 نام: {name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"📛 یوزرنیم: @{u['username'] if u['username'] else 'ندارد'}\n"
                f"🪙 موجودی: {get_coins(user_id):,} سکه\n"
                f"👥 دعوت کرده: {u.get('invite_count', 0)} نفر",
                {"inline_keyboard": [
                    [{"text": "📋 کپی آیدی عددی", "callback_data": "copy_id"}],
                    [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]
                ]}
            )
            return
# ═══ پایان بخش ۱۴ ═══
        # ═══ دعوت دوستان ═══
        if text == "👥 دعوت دوستان":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            reward = get_setting("invite_reward", 15)
            u = get_user(user_id)
            result = send_message(chat_id,
                f"🔥 هایپرسین\n\n"
                f"👁️ سین بزن | 👥 عضو بگیر\n"
                f"ترکیبی حرفه‌ای بله\n\n"
                f"🎁 همه‌چی رایگان!\n\n"
                f"📈 همین الان بیا و کانالتو رشد بده 😎👇\n"
                f"بدون پول\n\n"
                f"🔗 داش لینک دعوتت:\n{link}"
            )
            if result.get("ok"):
                msg_id = result["result"]["message_id"]
                send_reply(chat_id, msg_id, f"🪙 با هر دعوت {reward} سکه هدیه بگیر! 🎁🔥")
            return

        # ═══ پشتیبانی ═══
        if text == "💬 پشتیبانی":
            db["pending_support"][user_id] = {"step": "waiting"}; save_db_async()
            send_message(chat_id,
                "سلام! مشکلی پیش اومده؟ 🤔\n\n"
                "لطفاً پیامت رو ارسال کن تا کمکت کنیم!",
                cancel_keyboard()
            )
            return
# ═══ پایان بخش ۱۵ ═══
        # ═══ گردونه شانس ═══
        if text == "🎡 گردونه شانس":
            user = get_user(user_id); today = str(datetime.now().date())
            if user.get("wheel_today") != today:
                user["wheel_today"] = today; user["wheel_count"] = 0; save_db_async()
            if user["wheel_count"] >= 2:
                send_message(chat_id, f"❌ امروز شانست تموم شده!\n\n━━━━━━━━━━━━━━━━\n📊 شانس امروز: {user['wheel_count']}/2\n━━━━━━━━━━━━━━━━\n\n🔒 فردا دوباره بیا\n🎁 جایزه بزرگ‌تر می‌گیری!"); return
            send_message(chat_id, "🎰 گردونه داره می‌چرخه...\n\n⏳ صبر کن...\n💫 شانست رو امتحان کن...")
            time.sleep(2)
            user["wheel_count"] = user.get("wheel_count", 0) + 1; save_db_async()
            prizes = [(0, 30), (1, 25), (5, 20), (10, 12), (15, 6), (20, 3), (40, 2), (50, 1), (70, 0.5), (100, 0.5)]
            total_w = sum(w for _, w in prizes)
            r = random.uniform(0, total_w); cum = 0; prize = 0
            for p, w in prizes:
                cum += w
                if r <= cum: prize = p; break
            if prize == 0:
                send_message(chat_id, "🎡 گردونه چرخید!\n\n━━━━━━━━━━━━━━━━\n😢 امروز شانست یار نبود!\n❌ پوچ!\n━━━━━━━━━━━━━━━━\n\n💡 بعداً دوباره امتحان کن\n🍀 انشاءالله دفعه بعد!")
            elif prize == 100:
                add_coins(user_id, 100)
                send_message(chat_id, f"🎡 گردونه چرخید!\n\n━━━━━━━━━━━━━━━━\n🏆🏆🏆 جکپات! 🏆🏆🏆\n━━━━━━━━━━━━━━━━\n🪙 100 سکه گرفتی!\n💰 موجودی: {get_coins(user_id):,} سکه\n━━━━━━━━━━━━━━━━\n\n🎊 امروز شانست عالیه!\n🔥 برو یه سفارش بزن!")
            elif prize >= 40:
                add_coins(user_id, prize)
                send_message(chat_id, f"🎡 گردونه چرخید!\n\n━━━━━━━━━━━━━━━━\n🔥 فوق‌العاده!\n━━━━━━━━━━━━━━━━\n🪙 {prize} سکه گرفتی!\n💰 موجودی: {get_coins(user_id):,} سکه\n━━━━━━━━━━━━━━━━\n\n🎉 آفرین، شانست خوبه!")
            else:
                add_coins(user_id, prize)
                send_message(chat_id, f"🎡 گردونه چرخید!\n\n━━━━━━━━━━━━━━━━\n🎉 آفرین!\n━━━━━━━━━━━━━━━━\n🪙 {prize} سکه گرفتی!\n💰 موجودی: {get_coins(user_id):,} سکه\n━━━━━━━━━━━━━━━━\n\n💡 دوباره امتحان کن!")
            return

        # ═══ هدیه روزانه ═══
        if text == "🎁 هدیه روزانه":
            user = get_user(user_id); now = datetime.now()
            last = user.get("last_daily")
            if last:
                try:
                    lt = datetime.fromisoformat(last)
                    if now - lt < timedelta(hours=24):
                        rem = timedelta(hours=24) - (now - lt)
                        h = rem.seconds // 3600; m = (rem.seconds % 3600) // 60
                        send_message(chat_id, f"⏰ صبر کن داداش!\n\nهنوز {h} ساعت و {m} دقیقه مونده تا بتونی هدیه روزانه بگیری."); return
                except: pass
            gift = get_setting("daily_gift", 5)
            add_coins(user_id, gift)
            user["last_daily"] = str(now); save_db_async()
            send_message(chat_id, f"🎁 هدیه روزانه گرفتی! 🎉\n\n💰 +{gift} سکه بهت اضافه شد!\n💰 موجودی جدید: {get_coins(user_id):,} سکه")
            return

        # ═══ انتقال سکه ═══
        if text == "💰 انتقال سکه":
            fee = get_setting("transfer_fee", 2)
            db["pending_transfer"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🆔 آیدی عددی کاربر مقصد رو بفرست:", cancel_keyboard())
            return

        # ═══ زدن کد هدیه ═══
        if text == "🎁 زدن کد هدیه":
            db["pending_orders"][user_id] = {"step": "waiting_gift_code"}; save_db_async()
            send_message(chat_id, "🎁 لطفاً کد هدیه رو وارد کن:", cancel_keyboard())
            return

        # ═══ ثبت سفارش سین ═══
        if text == "👁️ ثبت سفارش سین":
            db["pending_orders"][user_id] = {"step": "waiting_forward"}; save_db_async()
            send_message(chat_id,
                "📩 لطفاً پیام مورد نظر را از کانال فوروارد کنید.\n\n"
                "⚠️ حتماً باید از کانال فوروارد شود!\n"
                "📢 از هر کانالی می‌تونی فوروارد کنی.",
                cancel_keyboard()
            )
            return

        # ═══ ثبت سفارش عضو ═══
        if text == "👥 ثبت سفارش عضو":
            db["pending_members"][user_id] = {"step": "waiting_link"}; save_db_async()
            send_message(chat_id,
                "📩 لطفاً لینک کانال مورد نظر را بفرستید.\n\n"
                "⚠️ حتماً باید کانال باشد!\n"
                "🚫 گروه قبول نمیشود!",
                cancel_keyboard()
            )
            return
# ═══ پایان بخش ۱۶ ═══
        # ═══ پردازش pending ═══
        pending = db["pending_orders"].get(user_id, {})
        pt = db["pending_transfer"].get(user_id, {})

        # ── کد هدیه ──
        if pending.get("step") == "waiting_gift_code":
            code = text.upper().strip()
            if code in db["gift_codes"]:
                g = db["gift_codes"][code]; u = get_user(user_id)
                if code in u.get("used_gift_codes", []):
                    send_message(chat_id, "❌ تو قبلاً این کد رو زدی!\n\n🔒 هر کد فقط ۱ بار قابل استفاده‌ست.", main_keyboard(user_id))
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ این کد تموم شده!\n\n👥 ظرفیت پر شده.", main_keyboard(user_id))
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    u.setdefault("used_gift_codes", []).append(code)
                    save_db_async()
                    send_message(chat_id, f"🎉 کد هدیه قبول شد!\n\n🪙 {g['coins']:,} سکه گرفتی!\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            else:
                send_message(chat_id, "❌ کد نامعتبر!\n\n💡 دوباره چک کن.", main_keyboard(user_id))
            del db["pending_orders"][user_id]; save_db_async(); return

        # ── انتقال سکه ──
        if pt.get("step") == "waiting_id":
            target = text.strip()
            if target in db["users"] and target != user_id:
                db["pending_transfer"][user_id] = {"step": "waiting_amount", "target": target}; save_db_async()
                send_message(chat_id,
                    f"💰 چند سکه میخوای به {target} بدی؟\n"
                    f"💰 موجودی: {get_coins(user_id):,} سکه",
                    cancel_keyboard()
                )
            else:
                send_message(chat_id, "❌ کاربر یافت نشد!\n\n💡 آیدی رو از حساب کاربری طرف بگیر.", main_keyboard(user_id))
                db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        if pt.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                target = pt["target"]; fee = get_setting("transfer_fee", 2)
                if amount <= fee:
                    send_message(chat_id, f"❌ مبلغ باید بیشتر از کارمزد ({fee}) باشه!", main_keyboard(user_id))
                    db["pending_transfer"].pop(user_id, None); save_db_async(); return
                if get_coins(user_id) < amount:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n\n💰 موجودی: {get_coins(user_id):,} سکه", main_keyboard(user_id))
                    db["pending_transfer"].pop(user_id, None); save_db_async(); return
                receiver_gets = amount - fee
                db["pending_transfer"][user_id] = {"step": "waiting_confirm", "target": target, "amount": amount, "receiver_gets": receiver_gets}
                save_db_async()
                kb = {"inline_keyboard": [[{"text": "✅ تأیید", "callback_data": "transfer_confirm"}], [{"text": "❌ لغو", "callback_data": "transfer_cancel"}]]}
                send_message(chat_id, f"📋 تأیید انتقال\n\n👤 گیرنده: {target}\n💰 فرستنده: {amount:,} سکه\n💸 کارمزد: {fee} سکه\n🎁 گیرنده: {receiver_gets:,} سکه\n\n⚠️ تأیید می‌کنی؟", kb)
            except: send_message(chat_id, "❌ عدد معتبر!", cancel_keyboard())
            return

        # ── ثبت سین ──
        if pending.get("step") == "waiting_forward":
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db["pending_orders"][user_id] = {"step": "waiting_count", "message_id": message["message_id"], "from_chat_id": message["forward_from_chat"]["id"]}
                save_db_async()
                send_message(chat_id,
                    f"🔢 چند سین نیاز داری؟\n\n"
                    f"💰 هر سین = {get_setting('sin_cost', 1)} سکه\n"
                    f"💳 موجودی: {get_coins(user_id):,} سکه\n"
                    f"⚠️ حداقل: {MIN_SIN} سین",
                    cancel_keyboard()
                )
            else:
                send_message(chat_id, "❌ این پیام از کانال نیست!\n\n💡 لطفاً پیام رو از یه کانال فوروارد کن.", cancel_keyboard())
            return

        if pending.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_SIN:
                    send_message(chat_id, f"❌ حداقل {MIN_SIN} سین!", cancel_keyboard()); return
                cost = get_setting('sin_cost', 1); total_cost = count * cost
                if get_coins(user_id) < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n\n💰 نیاز: {total_cost:,} ({count} × {cost})", cancel_keyboard())
                    del db["pending_orders"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                fwd = forward_message(CHANNEL_ID, chat_id, pending["message_id"])
                if fwd.get("ok"):
                    fwd_msg_id = fwd["result"]["message_id"]
                    db["order_counter"] = db.get("order_counter", 0) + 1
                    onum = db["order_counter"]; oid = str(int(time.time() * 1000))
                    db["orders"][oid] = {"user_id": user_id, "count": count, "message_id": fwd_msg_id, "reply_message_id": None, "seen_count": 0, "status": "active", "order_number": onum}
                    db["seen_records"][oid] = []
                    db["stats"]["total_orders"] = db["stats"].get("total_orders", 0) + 1
                    kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                    rr = send_reply(CHANNEL_ID, fwd_msg_id, f"📋 سفارش سین\n\n👤 تعداد سین درخواستی: {count}\n👁️ تعداد سین شده: 0\n#{onum}", kb)
                    if rr.get("ok"): db["orders"][oid]["reply_message_id"] = rr["result"]["message_id"]
                    del db["pending_orders"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ سفارش ثبت شد! 🎉\n\n🔢 تعداد سین: {count}\n💰 هزینه: {total_cost:,} سکه\n📝 #{onum}", main_keyboard(user_id))
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ خطا! سکه‌ها برگشت.", main_keyboard(user_id))
                    del db["pending_orders"][user_id]; save_db_async()
            except: send_message(chat_id, "❌ عدد معتبر!", cancel_keyboard())
            return
# ═══ پایان بخش ۱۷ ═══
        # ── ثبت عضو ──
        pmem = db["pending_members"].get(user_id, {})
        if pmem.get("step") == "waiting_link":
            db["pending_members"][user_id] = {"step": "waiting_admin", "link": text.strip()}; save_db_async()
            send_message(chat_id,
                f"🔗 لطفاً منو توی اون کانال ادمین کن!\n\n"
                f"⚠️ با تمام دسترسی‌ها\n"
                f"✅ بعد بنویس: ادمین کردم",
                cancel_keyboard()
            ); return
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
                            db["pending_members"][user_id] = {"step": "waiting_type", "link": link, "chat_id": tcid}; save_db_async()
                            send_message(chat_id,
                                f"📥 لطفاً نوع عضویت را انتخاب کنید:\n\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥉 ۱. نوع معمولی\n"
                                f"💰 هزینه هر عضو: {get_setting('member_cost',5)} سکه\n"
                                f"👤 کاربر میتونه هر وقت ترک کنه\n"
                                f"⭐ بستگی به جذابیت کانالت داره\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥇 ۲. نوع تضمینی\n"
                                f"💰 هزینه هر عضو: {get_setting('member_cost_guaranteed',10)} سکه\n"
                                f"🛡️ کاربر ۴۸ ساعت بمونه\n"
                                f"❌ اگه زودتر ترک کنه\n"
                                f"→ کاربر جریمه میشه\n"
                                f"→ سکه به شما برگشت\n"
                                f"━━━━━━━━━━━━━━━━\n\n"
                                f"🔢 لطفاً عدد ۱ یا ۲ را وارد کنید:",
                                cancel_keyboard()
                            )
                        else: send_message(chat_id, "❌ هنوز ادمین نشدم!", cancel_keyboard())
                    else: send_message(chat_id, "❌ لینک نامعتبر!", cancel_keyboard())
                except: send_message(chat_id, "❌ خطا!", cancel_keyboard())
            else: send_message(chat_id, "⚠️ بنویس: ادمین کردم", cancel_keyboard())
            return
        if pmem.get("step") == "waiting_type":
            choice = text.strip()
            if choice in ["1","2","۱","۲"]:
                otype = "normal" if choice in ["1","۱"] else "guaranteed"
                db["pending_members"][user_id]["order_type"] = otype
                db["pending_members"][user_id]["step"] = "waiting_count"; save_db_async()
                cost = get_setting('member_cost', 5) if otype == "normal" else get_setting('member_cost_guaranteed', 10)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                send_message(chat_id,
                    f"📥 ثبت سفارش عضو - {tname}\n\n"
                    f"👥 تعداد عضو موردنیاز را وارد کن داداش\n"
                    f"💰 هزینه هر عضو: {cost} سکه\n"
                    f"📌 حداقل سفارش: {MIN_MEMBER} عضو\n\n"
                    f"⌨️ لطفاً فقط عدد بفرست!",
                    cancel_keyboard()
                )
            else: send_message(chat_id, "❌ فقط ۱ یا ۲!", cancel_keyboard())
            return
# ═══ پایان بخش ۱۸ ═══
        if pmem.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_MEMBER:
                    send_message(chat_id, f"❌ حداقل {MIN_MEMBER} عضو!", cancel_keyboard()); return
                link = pmem["link"]; tcid = pmem["chat_id"]; otype = pmem.get("order_type", "normal")
                cost = get_setting('member_cost', 5) if otype == "normal" else get_setting('member_cost_guaranteed', 10)
                total_cost = count * cost
                if get_coins(user_id) < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n\n💰 نیاز: {total_cost:,} ({count} × {cost})", cancel_keyboard())
                    del db["pending_members"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                db["member_counter"] = db.get("member_counter", 0) + 1
                mnum = db["member_counter"]; mid = str(int(time.time() * 1000))
                reward = get_setting('member_normal_reward', 3) if otype == "normal" else get_setting('member_guaranteed_reward', 7)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                db["member_orders"][mid] = {"user_id": user_id, "count": count, "link": link, "chat_id": tcid, "message_id": None, "seen_count": 0, "status": "active", "order_number": mnum, "order_type": otype, "reward": reward, "join_times": {}, "penalized": {}}
                db["member_records"][mid] = []
                db["stats"]["total_members"] = db["stats"].get("total_members", 0) + 1
                kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت در کانال", "url": link}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}]]}
                sent = send_message(CHANNEL_ID, f"📋 سفارش عضو - {tname}\n\n🔗 لینک کانال: {link}\n👥 تعداد درخواستی: {count}\n✅ تعداد عضو شده: 0\n#{mnum}\n\n🪙 {reward} سکه میگیری!", kb)
                if sent.get("ok"): db["member_orders"][mid]["message_id"] = sent["result"]["message_id"]
                del db["pending_members"][user_id]; save_db_async()
                send_message(chat_id, f"✅ سفارش ثبت شد! 🎉\n\n👥 تعداد: {count} عضو\n💰 هزینه: {total_cost:,} سکه\n📝 #{mnum}", main_keyboard(user_id))
            except: send_message(chat_id, "❌ عدد معتبر!", cancel_keyboard())
            return
# ═══ پایان بخش ۱۹ ═══
        # ═══ پنل مالک ═══
        if is_admin(user_id):
            if text == "⚙️ تنظیم سکه":
                send_message(chat_id, "⚙️ تنظیم سکه:", settings_keyboard()); return
            coin_settings = {
                "👁️ سکه دیدم (عادی)": ("seen_reward", "سکه دیدم عادی"),
                "👁️ سکه دیدم (ویژه)": ("seen_reward_vip", "سکه دیدم ویژه"),
                "📝 سکه سفارش سین": ("sin_cost", "سکه سین"),
                "👥 هزینه عضو (عادی)": ("member_cost", "هزینه عضو عادی"),
                "👥 هزینه عضو (ویژه)": ("member_cost_vip", "هزینه عضو ویژه"),
                "🛡️ هزینه تضمینی (عادی)": ("member_cost_guaranteed", "هزینه تضمینی عادی"),
                "🛡️ هزینه تضمینی (ویژه)": ("member_cost_guaranteed_vip", "هزینه تضمینی ویژه"),
                "🪙 پاداش معمولی (عادی)": ("member_normal_reward", "پاداش معمولی عادی"),
                "🪙 پاداش معمولی (ویژه)": ("member_normal_reward_vip", "پاداش معمولی ویژه"),
                "🛡️ پاداش تضمینی (عادی)": ("member_guaranteed_reward", "پاداش تضمینی عادی"),
                "🛡️ پاداش تضمینی (ویژه)": ("member_guaranteed_reward_vip", "پاداش تضمینی ویژه"),
                "💸 کارمزد انتقال": ("transfer_fee", "کارمزد انتقال"),
                "🎁 هدیه روزانه": ("daily_gift", "هدیه روزانه"),
                "👥 سکه دعوت": ("invite_reward", "سکه دعوت"),
                "🎁 هدیه استارت": ("start_gift", "هدیه استارت"),
                "🔄 سقف بازیابی": ("restore_max", "سقف بازیابی")
            }
            if text in coin_settings:
                key, label = coin_settings[text]
                db["pending_coin_setting"][user_id] = {"key": key}; save_db_async()
                send_message(chat_id, f"{label}\n\nفعلی: {get_setting(key, 0)}\n\nجدید:", settings_keyboard()); return
            pcs = db["pending_coin_setting"].get(user_id, {})
            if pcs.get("key"):
                try:
                    val = int(convert_number(text))
                    db["settings"][pcs["key"]] = val
                    del db["pending_coin_setting"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ {val}", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", settings_keyboard())
                return
            if text == "🚫 مسدود کردن":
                db["pending_ban"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "🚫 آیدی:", cancel_keyboard()); return
            if text == "✅ رفع مسدودیت":
                db["pending_unban"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "✅ آیدی:", cancel_keyboard()); return
            if text == "👑 افزودن ادمین" and user_id == str(OWNER_ID):
                db["pending_admin"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "👑 آیدی:", cancel_keyboard()); return
            if text == "🗑️ حذف ادمین" and user_id == str(OWNER_ID):
                db["pending_remove_admin"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "🗑️ آیدی:", cancel_keyboard()); return
            if text == "📨 پیام به کاربر":
                db["pending_pm"][user_id] = {"step": "waiting_id"}; save_db_async()
                send_message(chat_id, "📨 آیدی:", cancel_keyboard()); return
            if text == "💻 اجرای کد":
                db["pending_execute"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "💻 کد:", cancel_keyboard()); return
            if text == "🎁 سکه پاکت":
                db["pending_packet"][user_id] = {"step": "waiting_coins"}; save_db_async()
                send_message(chat_id, "💰 هر نفر چند سکه؟", owner_keyboard()); return
            if text == "🎁 پاکت به کاربر":
                db["pending_packet_user"][user_id] = {"step": "waiting_id"}; save_db_async()
                send_message(chat_id, "🆔 آیدی:", cancel_keyboard()); return
            if text == "⭐ کاربر ویژه":
                db["pending_vip"][user_id] = {"step": "waiting_id"}; save_db_async()
                send_message(chat_id, "🆔 آیدی:", cancel_keyboard()); return
            if text == "📊 آمار کل":
                stats = db["stats"]
                send_message(chat_id, f"📊 آمار کل\n\n👥 کاربران: {len(db['users']):,}\n📝 سفارشات سین: {stats.get('total_orders', 0):,}\n✅ تکمیل سین: {stats.get('completed_orders', 0):,}\n👥 سفارشات عضو: {stats.get('total_members', 0):,}\n✅ تکمیل عضو: {stats.get('completed_members', 0):,}\n💸 کارمزد: {stats.get('owner_earnings', 0):,}\n📊 انتقال: {stats.get('total_transfers', 0):,}", owner_keyboard()); return
            if text == "📊 آمار پیشرفته":
                stats = db["stats"]
                total_coins = sum(u.get("coins", 0) for u in db["users"].values())
                active = sum(1 for u in db["users"].values() if u.get("msg_count", 0) > 0)
                inactive = len(db["users"]) - active
                send_message(chat_id, f"📊 آمار پیشرفته\n\n💰 سکه جمع: {total_coins:,}\n💳 موجودی: {total_coins:,}\n💵 کارمزد: {stats.get('owner_earnings', 0):,}\n🔄 انتقالات: {stats.get('total_transfers', 0):,}\n\n👥 فعال: {active:,}\n😴 غیرفعال: {inactive:,}\n\n🚫 مسدود: {stats.get('ban_count', 0):,}\n✅ رفع: {stats.get('unban_count', 0):,}", owner_keyboard()); return
            if text == "🔒 جوین اجباری":
                chs = db.get("join_channels", [])
                msg = "🔒 جوین اجباری\n\n📊 لیست:\n"
                if chs:
                    for i, ch in enumerate(chs, 1): msg += f"{i}. {ch}\n"
                else: msg += "(خالی)\n"
                msg += "\n📌 افزودن: add @channel\n📌 حذف: del 1"
                send_message(chat_id, msg, cancel_keyboard()); return
            if text.startswith("add ") and is_admin(user_id):
                ch = text[4:].strip()
                if ch not in db.get("join_channels", []):
                    db.setdefault("join_channels", []).append(ch); save_db_async()
                send_message(chat_id, f"✅ {ch}", owner_keyboard()); return
            if text.startswith("del ") and is_admin(user_id):
                try:
                    idx = int(text[4:].strip()) - 1
                    chs = db.get("join_channels", [])
                    if 0 <= idx < len(chs):
                        removed = chs.pop(idx); save_db_async()
                        send_message(chat_id, f"✅ {removed} حذف شد!", owner_keyboard())
                    else: send_message(chat_id, "❌ شماره اشتباه!", owner_keyboard())
                except: send_message(chat_id, "❌ فرمت: del 1", owner_keyboard())
                return
            if text == "🏆 رتبه‌بندی":
                us = sorted(db["users"].items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:15]
                msg = "🏆 ۱۵ نفر اول\n\n"
                for i, (uid, d) in enumerate(us, 1):
                    un = d.get("username", "")
                    msg += f"{i}. {d.get('first_name', 'کاربر')}\n   🆔 {uid}\n   📛 @{un if un else 'ندارد'}\n   🪙 {d.get('coins', 0):,}\n   👥 {d.get('invite_count', 0)}\n\n"
                send_message(chat_id, msg, owner_keyboard()); return
            if text == "🔄 حذف بازیابی" and user_id == str(OWNER_ID):
                current = db.get("recovery_enabled", True)
                db["recovery_enabled"] = not current; save_db_async()
                send_message(chat_id, "✅ حذف شد!" if current else "✅ فعال شد!", owner_keyboard()); return
            if text == "🎁 ساخت کد هدیه":
                db["pending_gift"][user_id] = {"step": "waiting_coins"}; save_db_async()
                send_message(chat_id, "💰 چند سکه؟", owner_keyboard()); return
            if text == "💰 افزودن سکه به همه":
                db["pending_add_coins"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "💰 چند سکه؟", owner_keyboard()); return
            if text == "🎁 تغییر سکه دعوت":
                db["pending_gift"][user_id] = {"step": "waiting_invite_reward"}; save_db_async()
                send_message(chat_id, f"🎁 فعلی: {get_setting('invite_reward', 15)}\n\nجدید:", owner_keyboard()); return
            if text == "📢 پیام همگانی":
                db["pending_broadcast"][user_id] = {"step": "waiting"}; save_db_async()
                send_message(chat_id, "📢 متن:", owner_keyboard()); return
            if text == "🎮 شروع بازی":
                db["pending_utility"][user_id] = {"step": "game_winners"}; save_db_async()
                send_message(chat_id, "1️⃣ چند نفر برنده؟", owner_keyboard()); return
            if text == "🔗 کاربردی‌ها":
                db["pending_utility"][user_id] = {"step": "utility_text"}; save_db_async()
                send_message(chat_id, "🔗 متن:", cancel_keyboard()); return
# ═══ پایان بخش ۲۰ ═══
            # ═══ pending مالک ═══
            pb = db["pending_ban"].get(user_id, {})
            if pb.get("step") == "waiting":
                uid = text.strip()
                if uid not in db["banned"]: db["banned"].append(uid)
                db["stats"]["ban_count"] = db["stats"].get("ban_count", 0) + 1
                del db["pending_ban"][user_id]; save_db_async()
                send_message(chat_id, f"🚫 {uid} مسدود شد!", owner_keyboard())
                try: send_message(int(uid), "🚫 مسدود شدی!")
                except: pass
                return
            pu2 = db["pending_unban"].get(user_id, {})
            if pu2.get("step") == "waiting":
                uid = text.strip()
                if uid in db["banned"]:
                    db["banned"].remove(uid)
                    db["stats"]["unban_count"] = db["stats"].get("unban_count", 0) + 1
                    del db["pending_unban"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ {uid} آزاد شد!", owner_keyboard())
                    try: send_message(int(uid), "🎉 مسدودی برداشته شد.")
                    except: pass
                else: send_message(chat_id, "❌ نبود!", owner_keyboard())
                return
            pa = db["pending_admin"].get(user_id, {})
            if pa.get("step") == "waiting":
                uid = text.strip()
                if uid not in db["admins"]: db["admins"].append(uid)
                del db["pending_admin"][user_id]; save_db_async()
                send_message(chat_id, "👑 ادمین شد!", owner_keyboard())
                try: send_message(int(uid), "👑 ادمین شدی!", owner_keyboard())
                except: pass
                return
            pra = db["pending_remove_admin"].get(user_id, {})
            if pra.get("step") == "waiting":
                uid = text.strip()
                if uid in db["admins"]:
                    db["admins"].remove(uid); save_db_async()
                    send_message(chat_id, "🗑️ حذف شد!", owner_keyboard())
                    try: send_message(int(uid), "🗑️ پنل گرفته شد!", main_keyboard())
                    except: pass
                else: send_message(chat_id, "❌ نبود!", owner_keyboard())
                del db["pending_remove_admin"][user_id]; save_db_async()
                return
            ppm = db["pending_pm"].get(user_id, {})
            if ppm.get("step") == "waiting_id":
                db["pending_pm"][user_id] = {"step": "waiting_text", "id": text.strip()}; save_db_async()
                send_message(chat_id, "📝 متن:", cancel_keyboard()); return
            if ppm.get("step") == "waiting_text":
                try:
                    send_message(int(ppm["id"]), text)
                    send_message(chat_id, "✅ شد!", owner_keyboard())
                except: send_message(chat_id, "❌ خطا!", owner_keyboard())
                del db["pending_pm"][user_id]; save_db_async(); return
            pe = db["pending_execute"].get(user_id, {})
            if pe.get("step") == "waiting":
                try:
                    eg = {'db': db, 'send_message': send_message, 'get_user': get_user, 'add_coins': add_coins, 'get_coins': get_coins, 'OWNER_ID': OWNER_ID, 'time': time, 'datetime': datetime}
                    result = eval(text.strip(), eg)
                    send_message(chat_id, f"✅ {result}", owner_keyboard())
                except Exception as e:
                    send_message(chat_id, f"❌ {str(e)[:200]}", owner_keyboard())
                del db["pending_execute"][user_id]; save_db_async(); return
            pac = db["pending_add_coins"].get(user_id, {})
            if pac.get("step") == "waiting":
                try:
                    amount = int(convert_number(text)); count = 0
                    for uid in db["users"]: add_coins(uid, amount); count += 1
                    del db["pending_add_coins"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ {amount} به {count} نفر!", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            pbc = db["pending_broadcast"].get(user_id, {})
            if pbc.get("step") == "waiting":
                del db["pending_broadcast"][user_id]; save_db_async()
                executor.submit(broadcast_worker, user_id, text)
                return
            pv = db["pending_vip"].get(user_id, {})
            if pv.get("step") == "waiting_id":
                db["pending_vip"][user_id] = {"step": "waiting_seconds", "target": text.strip()}; save_db_async()
                send_message(chat_id, "⏰ ثانیه:", cancel_keyboard()); return
            if pv.get("step") == "waiting_seconds":
                try:
                    sec = int(convert_number(text)); target = pv["target"]
                    exp = datetime.now() + timedelta(seconds=sec)
                    db["vip_expiry"][target] = str(exp)
                    del db["pending_vip"][user_id]; save_db_async()
                    send_message(chat_id, f"⭐ {target} تا {exp.strftime('%Y-%m-%d %H:%M')}", owner_keyboard())
                    try: send_message(int(target), f"⭐ VIP شدی تا {exp.strftime('%Y-%m-%d %H:%M')}")
                    except: pass
                except: send_message(chat_id, "❌ عدد!", cancel_keyboard())
                return
            pg = db["pending_gift"].get(user_id, {})
            if pg.get("step") == "waiting_coins":
                try:
                    db["pending_gift"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}; save_db_async()
                    send_message(chat_id, "👥 ظرفیت؟", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pg.get("step") == "waiting_capacity":
                try:
                    cap = int(convert_number(text))
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    db["gift_codes"][code] = {"coins": pg["coins"], "capacity": cap, "used_by": []}
                    del db["pending_gift"][user_id]; save_db_async()
                    send_message(chat_id, f"🎁 {code}\n💰 {pg['coins']}\n👥 {cap}", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pg.get("step") == "waiting_invite_reward":
                try:
                    val = int(convert_number(text))
                    db["settings"]["invite_reward"] = val
                    del db["pending_gift"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ {val}", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            pu = db["pending_utility"].get(user_id, {})
            if pu.get("step") == "game_winners":
                try:
                    db["pending_utility"][user_id] = {"step": "game_prize", "winners": int(convert_number(text))}; save_db_async()
                    send_message(chat_id, "2️⃣ سکه؟", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pu.get("step") == "game_prize":
                try:
                    db["pending_utility"][user_id] = {"step": "game_target", "winners": pu["winners"], "prize": int(convert_number(text))}; save_db_async()
                    send_message(chat_id, "3️⃣ چند دعوت؟", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pu.get("step") == "game_target":
                try:
                    target = int(convert_number(text))
                    w = pu["winners"]; p = pu["prize"]
                    kb = {"inline_keyboard": [[{"text": "🎯 ثبت‌نام تو بازی", "callback_data": "game_join"}]]}
                    send_message(CHANNEL_ID, f"🎮 بازی شروع شد!\n\n🏆 {w} نفر اول که {target} دعوت کنن → {p} سکه!\n\n⚡ سریع باش!\n👥 0/{w}", kb)
                    del db["pending_utility"][user_id]; save_db_async()
                    send_message(chat_id, "✅ شروع شد!", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pu.get("step") == "utility_text":
                db["pending_utility"][user_id] = {"step": "utility_link", "text": text}; save_db_async()
                send_message(chat_id, "🔗 لینک:", cancel_keyboard()); return
            if pu.get("step") == "utility_link":
                kb = {"inline_keyboard": [[{"text": pu["text"], "url": text}]]}
                send_message(CHANNEL_ID, f"🔗 {pu['text']}", kb)
                del db["pending_utility"][user_id]; save_db_async()
                send_message(chat_id, "✅ گذاشته شد!", owner_keyboard()); return
            pp = db["pending_packet"].get(user_id, {})
            if pp.get("step") == "waiting_coins":
                try:
                    db["pending_packet"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}; save_db_async()
                    send_message(chat_id, "👥 ظرفیت؟", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pp.get("step") == "waiting_capacity":
                try:
                    db["pending_packet"][user_id] = {"step": "waiting_text", "coins": pp["coins"], "capacity": int(convert_number(text))}; save_db_async()
                    send_message(chat_id, "📝 متن:", owner_keyboard())
                except: send_message(chat_id, "❌ عدد!", owner_keyboard())
                return
            if pp.get("step") == "waiting_text":
                pid = str(int(time.time() * 1000))
                db["coin_packets"][pid] = {"coins": pp["coins"], "capacity": pp["capacity"], "text": text, "used_by": []}
                kb = {"inline_keyboard": [[{"text": "🎁 باز کردن", "callback_data": f"packet_{pid}"}]]}
                send_message(CHANNEL_ID, f"🎁 سکه پاکت\n\n{text}\n\n💰 هر نفر: {pp['coins']:,}\n👥 {pp['capacity']}", kb)
                db["pending_packet"].pop(user_id, None); save_db_async()
                send_message(chat_id, "✅ شد!", owner_keyboard()); return
            ppu = db["pending_packet_user"].get(user_id, {})
            if ppu.get("step") == "waiting_id":
                db["pending_packet_user"][user_id] = {"step": "waiting_coins", "id": text.strip()}; save_db_async()
                send_message(chat_id, "💰 چند سکه؟", cancel_keyboard()); return
            if ppu.get("step") == "waiting_coins":
                try:
                    amount = int(convert_number(text)); target = ppu["id"]
                    add_coins(target, amount)
                    del db["pending_packet_user"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ {amount} به {target}", owner_keyboard())
                    try: send_message(int(target), f"🎁 {amount} سکه هدیه!")
                    except: pass
                except: send_message(chat_id, "❌ عدد!", cancel_keyboard())
                return

        send_message(chat_id, f"👋 سلام {name} جان! 😎\n\nاز دکمه‌ها استفاده کن:", main_keyboard(user_id))

    except Exception as e:
        print(f"⚠️ خطا handle_message: {e}")
# ═══ پایان بخش ۲۱ ═══
# ═══ Callback ═══
def handle_callback(callback):
    try:
        callback_id = callback["id"]
        data = callback["data"]
        user_id = str(callback["from"]["id"])
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id", CHANNEL_ID)

        if is_banned(user_id):
            answer_callback(callback_id, "🚫 مسدود شدی!", show_alert=True); return

        if data == "check_join":
            JOIN_CACHE.pop(str(user_id), None)
            if check_joined(user_id):
                u = get_user(user_id)
                if not u.get("got_start_gift"):
                    add_coins(user_id, get_setting("start_gift", 25))
                    u["got_start_gift"] = True; save_db_async()
                    answer_callback(callback_id, f"✅ عضو شدی!")
                    send_message(user_id, f"✅ عضو شدی! 🎉\n🎁 25 سکه هدیه!\n💰 {get_coins(user_id):,}", main_keyboard(user_id))
                else:
                    answer_callback(callback_id, "✅ عضو شدی!")
                    send_message(user_id, "✅ استفاده کن!", main_keyboard(user_id))
            else: answer_callback(callback_id, "❌ هنوز عضو نشدی!", show_alert=True)
            return
# ═══ پایان بخش ۲۲ ═══
        if data == "back_to_main":
            send_message(user_id, "🏠 منوی اصلی:", main_keyboard(user_id))
            answer_callback(callback_id); return

        if data == "copy_id":
            answer_callback(callback_id, f"✅ {user_id}", show_alert=True); return

        if data == "transfer_confirm":
            pt = db["pending_transfer"].get(user_id, {})
            if pt.get("step") != "waiting_confirm":
                answer_callback(callback_id, "❌ منقضی!", show_alert=True); return
            target = pt["target"]; amount = pt["amount"]; fee = get_setting("transfer_fee", 2); recv = pt["receiver_gets"]
            if remove_coins(user_id, amount):
                add_coins(target, recv)
                add_coins(OWNER_ID, fee)
                db["stats"]["total_transfers"] = db["stats"].get("total_transfers", 0) + 1
                db["stats"]["owner_earnings"] = db["stats"].get("owner_earnings", 0) + fee
                save_db_async()
                answer_callback(callback_id, "✅ شد!")
                send_message(user_id, f"✅ انتقال شد!\n\n👤 {target}\n💰 {amount:,}\n💸 {fee}\n🎁 {recv:,}\n💰 {get_coins(user_id):,}", main_keyboard(user_id))
                try: send_message(int(target), f"🎉 سکه گرفتی!\n\n👤 از: {user_id}\n🪙 {recv:,}\n💰 {get_coins(target):,}")
                except: pass
            else:
                answer_callback(callback_id, "❌ سکه کافی نداری!", show_alert=True)
            del db["pending_transfer"][user_id]; save_db_async(); return

        if data == "transfer_cancel":
            db["pending_transfer"].pop(user_id, None); save_db_async()
            answer_callback(callback_id, "❌ لغو!")
            send_message(user_id, "❌ لغو شد!", main_keyboard(user_id)); return

        if data == "game_join":
            answer_callback(callback_id, "✅ ثبت‌نام شدی!", show_alert=True)
            try: send_message(int(user_id), f"✅ تو بازی ثبت‌نام شدی!\n\n🔗 لینکت:\nhttps://ble.ir/{BOT_USERNAME}?start={user_id}")
            except: pass
            return

        if data.startswith("packet_"):
            pid = data.replace("packet_", "")
            if pid not in db.get("coin_packets", {}):
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            p = db["coin_packets"][pid]
            if str(user_id) in p["used_by"]:
                answer_callback(callback_id, "⚠️ قبلاً!", show_alert=True); return
            if len(p["used_by"]) >= p["capacity"]:
                answer_callback(callback_id, "😢 دیر رسیدی!", show_alert=True); return
            p["used_by"].append(str(user_id))
            add_coins(user_id, p["coins"]); save_db_async()
            answer_callback(callback_id, f"🎉 {p['coins']:,} سکه!", show_alert=True); return
# ═══ پایان بخش ۲۳ ═══
        # ═══ دیدم (سین) ═══
        if data.startswith("seen_"):
            oid = data.replace("seen_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌!"); return
            order = db["orders"][oid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تموم!"); return
            if str(user_id) in db["seen_records"].get(oid, []):
                answer_callback(callback_id, "⚠️ قبلاً!"); return
            db["seen_records"][oid].append(str(user_id))
            order["seen_count"] += 1
            reward = get_setting('seen_reward', 1)
            add_coins(user_id, reward)
            ns = order["seen_count"]; count = order["count"]; onum = order.get("order_number", "?")
            
            # ✅ نوتیفیکیشن واضح برای دیدم
            answer_callback(
                callback_id,
                f"👁️ دیدم زدی!\n\n"
                f"🎁 +{reward} سکه گرفتی\n"
                f"💰 موجودی جدید: {get_coins(user_id):,} سکه",
                show_alert=True
            )
            
            if order.get("reply_message_id"):
                kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                try: edit_message_text(CHANNEL_ID, order["reply_message_id"], f"📋 سفارش سین\n\n👤 تعداد سین درخواستی: {count}\n👁️ تعداد سین شده: {ns}\n#{onum}", kb)
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
                        f"🎉 تبریک داداش!\n\n"
                        f"🔢 {count} سین درخواستی تو کامل خورد!\n"
                        f"📩 پیام از کانال حذف شد.\n\n"
                        f"💡 حالا می‌تونی:\n"
                        f"• 🪙 بری کسب سکه کنی\n"
                        f"• 👁️ سفارش جدید ثبت کنی\n"
                        f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                        main_keyboard(order["user_id"])
                    )
                except: pass
            save_db_async(); return

        if data.startswith("report_"):
            oid = data.replace("report_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌!", show_alert=True); return
            order = db["orders"][oid]
            rn = callback["from"].get("username", "?")
            answer_callback(callback_id, "🚨 شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 گزارش سین\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔢 {order['count']}\n👁️ {order['seen_count']}")
            except: pass
            return

        if data.startswith("info_"):
            mid = data.replace("info_", "")
            o = db["member_orders"].get(mid, {})
            reward = o.get("reward", 3); otype = o.get("order_type", "normal")
            if otype == "guaranteed":
                answer_callback(callback_id, f"🪙 {reward}!\n⚠️ ۴۸ ساعت بمون!", show_alert=True)
            else:
                answer_callback(callback_id, f"🪙 {reward} سکه!", show_alert=True)
            return

        # ═══ عضو شدم (عضوگیر) ═══
        if data.startswith("mjoin_"):
            mid = data.replace("mjoin_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌!", show_alert=True); return
            order = db["member_orders"][mid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تموم!", show_alert=True); return
            if str(user_id) in db["member_records"].get(mid, []):
                answer_callback(callback_id, "⚠️ قبلاً!", show_alert=True); return
            if order.get("user_id") == str(user_id):
                answer_callback(callback_id, "❌ تو سفارش خودت!", show_alert=True); return
            tcid = order["chat_id"]
            ms = get_chat_member(tcid, user_id)
            if ms.get("ok") and ms["result"]["status"] in ["member", "administrator", "creator"]:
                db["member_records"][mid].append(str(user_id))
                order["seen_count"] += 1
                reward = order.get("reward", 3)
                add_coins(user_id, reward)
                order.setdefault("join_times", {})[str(user_id)] = str(datetime.now())
                ns = order["seen_count"]; count = order["count"]; mnum = order.get("order_number", "?")
                tname = "معمولی" if order.get("order_type") == "normal" else "تضمینی"
                
                # ✅ نوتیفیکیشن واضح برای عضو شدم
                answer_callback(
                    callback_id,
                    f"✅ عضو شدی!\n\n"
                    f"🎁 +{reward} سکه گرفتی\n"
                    f"💰 موجودی جدید: {get_coins(user_id):,} سکه",
                    show_alert=True
                )
                
                if order.get("message_id"):
                    kb = {"inline_keyboard": [
                        [{"text": f"🪙 {reward} سکه!", "callback_data": f"info_{mid}"}],
                        [{"text": "🔗 عضویت در کانال", "url": order["link"]}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}],
                        [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}]
                    ]}
                    try: edit_message_text(CHANNEL_ID, order["message_id"], f"📋 سفارش عضو - {tname}\n\n🔗 لینک کانال: {order['link']}\n👥 تعداد درخواستی: {count}\n✅ تعداد عضو شده: {ns}\n#{mnum}\n\n🪙 {reward} سکه میگیری!", kb)
                    except: pass
                if ns >= count:
                    order["status"] = "completed"
                    db["stats"]["completed_members"] = db["stats"].get("completed_members", 0) + 1
                    try: delete_message(CHANNEL_ID, order["message_id"])
                    except: pass
                    try:
                        send_message(int(order["user_id"]),
                            f"🎉 تبریک داداش!\n\n"
                            f"👥 {count} عضو درخواستی تو کامل شد!\n"
                            f"📩 پیام از کانال حذف شد.\n\n"
                            f"💡 حالا می‌تونی:\n"
                            f"• 🪙 بری کسب سکه کنی\n"
                            f"• 👥 سفارش عضو جدید ثبت کنی\n"
                            f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                            main_keyboard(order["user_id"])
                        )
                    except: pass
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی!", show_alert=True)
            save_db_async(); return
# ═══ پایان بخش ۲۴ ══
        if data.startswith("mreport_"):
            mid = data.replace("mreport_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌!", show_alert=True); return
            order = db["member_orders"][mid]
            rn = callback["from"].get("username", "?")
            answer_callback(callback_id, "🚨 شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 گزارش عضو\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔗 {order['link']}")
            except: pass
            return

    except Exception as e:
        print(f"⚠️ خطا callback: {e}")
# ═══ پایان بخش ۲۵ ═══


# ═══ حلقه اصلی ═══
last_update_id = 0


def main_loop():
    global last_update_id
    print("⚡ هایپرسین بله")
    print(f"🤖 @{BOT_USERNAME}")
    print("-" * 40)
    while True:
        try:
            updates = api_call("getUpdates", {"offset": last_update_id + 1, "limit": 100, "timeout": 3})
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update:
                        executor.submit(handle_message, update["message"])
                    elif "callback_query" in update:
                        executor.submit(handle_callback, update["callback_query"])
            time.sleep(0.01)
        except KeyboardInterrupt: break
        except Exception as e:
            print(f"⚠️ خطا: {e}"); time.sleep(0.3)


def self_ping():
    while True:
        try:
            time.sleep(180)
            send_message(OWNER_ID, "ping")
        except: time.sleep(60)


app = Flask(__name__)


@app.route('/')
def home(): return "🤖 Hypersin Bale Bot!"


@app.route('/ping')
def ping(): return "pong ✅"


@app.route('/health')
def health():
    return jsonify({"status": "online", "users": len(db.get("users", {})), "cache": len(CACHE)})


if __name__ == "__main__":
    threading.Thread(target=save_worker, daemon=True).start()
    threading.Thread(target=cache_cleanup, daemon=True).start()
    threading.Thread(target=self_ping, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    threading.Thread(target=check_members_leaves, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
# ═══ پایان کد ═══
