import requests, json, time, random, string, os, sys, traceback, threading, gc, hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import queue

# ============================================
# 🔧 تنظیمات هایپرسین
# ============================================
TOKEN = "886012408:V6CU51uMQU59W86Dq4MM44wlU6rON5zl39M"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

CHANNEL_ID = "@jensinqpbd"
CHANNEL_LINK = "https://ble.ir/jensinqpbd"
BOT_USERNAME = "Idneobot"
BOT_LINK = f"https://ble.ir/{BOT_USERNAME.replace('@', '')}"

OWNER_ID = "580628965"
OWNER_PASSWORD = "parsa0847"
COIN_PASSWORD = "coin"
INFINITE_COINS = 999999
MIN_SIN = 15
MIN_MEMBER = 1
MEMBER_COST = 5
START_GIFT = 25
SEEN_REWARD = 1
SIN_COST = 1
INVITE_REWARD = 15
DAILY_GIFT = 5

DB_FILE = "sinzen_ultra_strong.json"

# ⚡ سرور فوق قوی
MAX_WORKERS = 500
API_TIMEOUT = 2
BROADCAST_SPEED = 100

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# ============================================
# 🛡️ محافظ ۱: ضد خطا
# ============================================
class ErrorGuard:
    def __init__(self):
        self.fix_count = 0
        self.last_error = None
        self.total_errors = 0
    
    def protect(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.fix_count += 1
            self.total_errors += 1
            self.last_error = str(e)[:100]
            print(f"🛡️ ErrorGuard: رفع خطا #{self.fix_count} | {self.last_error}")
            gc.collect()
            time.sleep(0.001)
            return None
    
    def status(self):
        return f"🛡️ ErrorGuard: {self.total_errors} خطا رفع شده | آخرین: {self.last_error}"

# ============================================
# 🛡️ محافظ ۲: ضد خاموشی
# ============================================
class Watchdog:
    def __init__(self):
        self.restart_count = 0
        self.start_time = datetime.now()
        self.last_restart = None
    
    def run(self, func):
        while True:
            try:
                func()
            except KeyboardInterrupt:
                print("\n👋 خداحافظ!")
                break
            except Exception as e:
                self.restart_count += 1
                self.last_restart = datetime.now()
                print(f"💀 Watchdog: ریستارت #{self.restart_count} | خطا: {str(e)[:100]}")
                gc.collect()
                time.sleep(0.001)
                continue
    
    def status(self):
        uptime = datetime.now() - self.start_time
        return f"🔄 Watchdog: {self.restart_count} ریستارت | زمان اجرا: {uptime}"

# ============================================
# 🛡️ محافظ ۳: ضد VPN
# ============================================
class VPNGuard:
    def __init__(self):
        self.ok = False
        self.retry_count = 0
        self.max_retries = 999999
    
    def safe_call(self, func, *args, **kwargs):
        while True:
            try:
                result = func(*args, **kwargs)
                self.ok = True
                self.retry_count = 0
                return result
            except:
                self.ok = False
                self.retry_count += 1
                wait = min(self.retry_count * 0.5, 10)
                time.sleep(wait)
                continue
    
    def status(self):
        return f"🛡️ VPNGuard: {'✅ وصل' if self.ok else '⚠️ در حال تلاش'} | تلاش: {self.retry_count}"

# ============================================
# 🛡️ محافظ ۴: سرور قوی
# ============================================
class ServerGuard:
    def __init__(self):
        self.backup_count = 0
        self.last_backup = None
        self.power = "۵۰۰ میلیون تومان"
    
    def protect(self):
        gc.collect()
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = f.read()
            with open(f"{DB_FILE}.backup", 'w', encoding='utf-8') as f:
                f.write(data)
            with open(f"{DB_FILE}.backup2", 'w', encoding='utf-8') as f:
                f.write(data)
            self.backup_count += 1
            self.last_backup = datetime.now()
        except:
            pass
        return True
    
    def status(self):
        return f"🖥️ ServerGuard: {self.backup_count} بک‌آپ | قدرت: {self.power}"

# ============================================
# 🛡️ محافظ ۵: ضد قطع نت
# ============================================
class NetGuard:
    def __init__(self):
        self.retry_count = 0
        self.is_connected = False
    
    def safe_call(self, func, *args, **kwargs):
        while True:
            try:
                result = func(*args, **kwargs)
                self.is_connected = True
                self.retry_count = 0
                return result
            except:
                self.is_connected = False
                self.retry_count += 1
                wait = min(self.retry_count * 0.5, 10)
                time.sleep(wait)
                continue
    
    def status(self):
        return f"🌐 NetGuard: {'✅ وصل' if self.is_connected else '⚠️ قطع'} | تلاش: {self.retry_count}"

# ============================================
# 🛡️ محافظ ۶: ضد فیلترشکن
# ============================================
class ProxyGuard:
    def __init__(self):
        self.ok = False
        self.mode = "auto"
    
    def safe_call(self, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            self.ok = True
            return result
        except:
            try:
                result = func(*args, **kwargs)
                self.ok = True
                return result
            except:
                self.ok = False
                time.sleep(0.5)
                return None
    
    def status(self):
        return f"🔌 ProxyGuard: {'✅ فعال' if self.ok else '⚠️ در حال تنظیم'} | حالت: {self.mode}"

# ============================================
# 🛡️ راه‌اندازی همه محافظ‌ها
# ============================================
error_guard = ErrorGuard()
watchdog = Watchdog()
vpn_guard = VPNGuard()
server_guard = ServerGuard()
net_guard = NetGuard()
proxy_guard = ProxyGuard()

# ============================================
# 📅 تابع تاریخ شمسی
# ============================================
def get_shamsi_date():
    now = datetime.now()
    gy = now.year
    gm = now.month
    gd = now.day
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days = days % 12053
    jy = jy + 4 * (days // 1461)
    days = days % 1461
    if days > 365:
        jy = jy + (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return f"{jy}/{jm:02d}/{jd:02d}"

# ============================================
# 🗄️ دیتابیس فوق قوی با ۳ لایه بک‌آپ
# ============================================
def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except:
        pass
    
    try:
        if os.path.exists(f"{DB_FILE}.backup"):
            with open(f"{DB_FILE}.backup", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except:
        pass
    
    try:
        if os.path.exists(f"{DB_FILE}.backup2"):
            with open(f"{DB_FILE}.backup2", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except:
        pass
    
    return {
        "users": {},
        "orders": {},
        "member_orders": {},
        "gift_codes": {},
        "seen_records": {},
        "member_records": {},
        "invited_users": {},
        "rewarded_users": [],
        "used_ips": {},
        "order_counter": 0,
        "member_counter": 0,
        "stats": {
            "total_orders": 0,
            "completed_orders": 0,
            "deleted_messages": 0,
            "total_members": 0,
            "completed_members": 0
        },
        "pending_orders": {},
        "pending_members": {},
        "pending_gift": {},
        "pending_broadcast": {},
        "pending_add_coins": {},
        "pending_transfer": {},
        "pending_coin_setting": {},
        "pending_support": {},
        "pending_support_reply": {},
        "pending_ban": {},
        "pending_unban": {},
        "pending_packet": {},
        "support_messages": {},
        "join_channels": [],
        "banned": [],
        "invite_reward": INVITE_REWARD,
        "guaranteed_members": {},
        "punished_users": [],
        "coin_packets": {},
        "settings": {
            "seen_reward": 1,
            "sin_cost": 1,
            "member_cost": 5,
            "member_normal_reward": 3,
            "member_guaranteed_reward": 7,
            "invite_reward": 15,
            "daily_gift": 5,
            "start_gift": 25
        }
    }

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(f"{DB_FILE}.backup", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(f"{DB_FILE}.backup2", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

db = load_db()
db.setdefault("invited_users", {})
db.setdefault("rewarded_users", [])
db.setdefault("pending_transfer", {})
db.setdefault("invite_reward", INVITE_REWARD)
db.setdefault("used_ips", {})
db.setdefault("guaranteed_members", {})
db.setdefault("punished_users", [])
db.setdefault("coin_packets", {})
db.setdefault("pending_packet", {})
db.setdefault("pending_coin_setting", {})
db.setdefault("pending_support", {})
db.setdefault("pending_support_reply", {})
db.setdefault("pending_ban", {})
db.setdefault("pending_unban", {})
db.setdefault("support_messages", {})
db.setdefault("banned", [])
db.setdefault("join_channels", [])
db.setdefault("settings", {
    "seen_reward": 1,
    "sin_cost": 1,
    "member_cost": 5,
    "member_normal_reward": 3,
    "member_guaranteed_reward": 7,
    "invite_reward": 15,
    "daily_gift": 5,
    "start_gift": 25
})
save_db(db)


def get_setting(key, default=0):
    return db.get("settings", {}).get(key, default)


def get_user(user_id):
    user_id = str(user_id)
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "coins": 0,
            "joined": False,
            "got_start_gift": False,
            "total_orders": 0,
            "completed_orders": 0,
            "used_gift_codes": [],
            "username": "",
            "invite_code": None,
            "invite_count": 0,
            "invited_by": None,
            "first_seen": str(datetime.now()),
            "last_seen": str(datetime.now()),
            "last_daily": None
        }
        save_db(db)
    return db["users"][user_id]


def add_coins(user_id, amount):
    user = get_user(user_id)
    user["coins"] += amount
    save_db(db)


def remove_coins(user_id, amount):
    user = get_user(user_id)
    if user["coins"] >= amount:
        user["coins"] -= amount
        save_db(db)
        return True
    return False


def get_coins(user_id):
    return get_user(user_id)["coins"]


# ============================================
# 🛡️ توابع ضد باگ
# ============================================
def is_punished(user_id, order_id):
    key = f"{user_id}_{order_id}"
    return key in db["punished_users"]

def mark_punished(user_id, order_id):
    key = f"{user_id}_{order_id}"
    if key not in db["punished_users"]:
        db["punished_users"].append(key)
        save_db(db)

def is_already_paid(user_id, order_id):
    return str(user_id) in db["member_records"].get(order_id, [])

def is_order_owner(user_id, order_id):
    order = db["member_orders"].get(order_id, {})
    return order.get("user_id") == str(user_id)

def is_guaranteed(order_id):
    order = db["member_orders"].get(order_id, {})
    return order.get("order_type") == "guaranteed"

def is_48h_passed(join_time_str):
    if not join_time_str:
        return False
    join_time = datetime.fromisoformat(join_time_str)
    return datetime.now() >= join_time + timedelta(hours=48)

def is_2min_passed(join_time_str):
    if not join_time_str:
        return False
    join_time = datetime.fromisoformat(join_time_str)
    return datetime.now() >= join_time + timedelta(minutes=2)

def is_bot_admin(chat_id):
    try:
        result = get_chat_member(chat_id, int(TOKEN.split(":")[0]))
        return result.get("ok") and result["result"]["status"] == "administrator"
    except:
        return False

# ============================================
# 📡 توابع API
# ============================================
session = requests.Session()
session.headers.update({
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate'
})
adapter = requests.adapters.HTTPAdapter(
    pool_connections=500,
    pool_maxsize=500,
    max_retries=0,
    pool_block=False
)
session.mount('https://', adapter)
session.mount('http://', adapter)

def api_call(method, data=None, timeout=API_TIMEOUT):
    try:
        if data is None:
            data = {}
        response = session.post(f"{BASE_URL}/{method}", data=data, timeout=timeout)
        return response.json()
    except:
        try:
            response = session.post(f"{BASE_URL}/{method}", data=data, timeout=2)
            return response.json()
        except:
            return {"ok": False}

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api_call("sendMessage", data)

def send_reply(chat_id, reply_to_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to_id,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api_call("sendMessage", data)

def edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api_call("editMessageText", data)

def delete_message(chat_id, message_id):
    return api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def forward_message(chat_id, from_chat_id, message_id):
    return api_call("forwardMessage", {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    })

def answer_callback(callback_id, text=None, show_alert=False):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    data["show_alert"] = show_alert
    return api_call("answerCallbackQuery", data)

def get_chat_member(chat_id, user_id):
    return api_call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

def get_chat(chat_id):
    return api_call("getChat", {"chat_id": chat_id})

# ============================================
# ✅ بررسی عضویت در کانال (چند کانال)
# ============================================
def check_joined(user_id):
    try:
        result = get_chat_member(CHANNEL_ID, user_id)
        if not result.get("ok"):
            return False
        status = result["result"]["status"]
        if status not in ["member", "administrator", "creator"]:
            return False
        
        for ch in db.get("join_channels", []):
            try:
                r = get_chat_member(ch, user_id)
                if not r.get("ok"):
                    return False
                if r["result"]["status"] not in ["member", "administrator", "creator"]:
                    return False
            except:
                return False
        
        get_user(user_id)["joined"] = True
        save_db(db)
        return True
    except:
        return False


def must_join(user_id):
    rows = []
    rows.append([{"text": "🔗 عضویت در کانال اصلی", "url": CHANNEL_LINK}])
    for ch in db.get("join_channels", []):
        if ch.startswith("@"):
            url = f"https://ble.ir/{ch[1:]}"
        else:
            url = ch
        rows.append([{"text": f"🔗 {ch}", "url": url}])
    rows.append([{"text": "✅ عضو شدم", "callback_data": "check_join"}])
    
    keyboard = {"inline_keyboard": rows}
    send_message(
        user_id,
        "🔒 **برای استفاده از ربات باید عضو کانال‌ها بشی!**\n\n"
        "لطفاً عضو شو، بعد روی «✅ عضو شدم» بزن.",
        keyboard
    )
    return False

# ═══ پایان بخش ۱ ═══
# ============================================
# 🎮 کیبورد اصلی کاربر
# ============================================
def main_keyboard():
    return {
        "keyboard": [
            [{"text": "🪙 کسب سکه"}],
            [{"text": "👁️ ثبت سفارش سین"}, {"text": "👥 ثبت سفارش عضو"}],
            [{"text": "💰 سکه‌های من"}, {"text": "🎁 زدن کد هدیه"}],
            [{"text": "🎁 هدیه روزانه"}],
            [{"text": "👥 دعوت دوستان"}, {"text": "👤 حساب کاربری"}],
            [{"text": "💰 انتقال سکه"}],
            [{"text": "💬 پشتیبانی"}],
            [{"text": "📖 راهنما"}]
        ],
        "resize_keyboard": True
    }


# ============================================
# 🎮 کیبورد پنل مالک
# ============================================
def owner_keyboard():
    return {
        "keyboard": [
            [{"text": "⚙️ تنظیم سکه"}, {"text": "🔒 جوین اجباری"}],
            [{"text": "🎁 ساخت کد هدیه"}, {"text": "🎁 سکه پاکت"}],
            [{"text": "💰 افزودن سکه به همه"}],
            [{"text": "💰 انتقال سکه"}],
            [{"text": "🚫 مسدود کردن"}, {"text": "✅ رفع مسدودیت"}],
            [{"text": "📊 آمار کل"}, {"text": "📢 پیام همگانی"}],
            [{"text": "🏆 رتبه‌بندی"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }


# ============================================
# 🎮 کیبورد تنظیم سکه
# ============================================
def coin_settings_keyboard():
    return {
        "keyboard": [
            [{"text": "👁️ سکه دیدم"}],
            [{"text": "📝 سکه سین"}, {"text": "👥 هزینه عضو"}],
            [{"text": "🪙 پاداش معمولی"}, {"text": "🛡️ پاداش تضمینی"}],
            [{"text": "👥 سکه دعوت"}],
            [{"text": "🎁 هدیه روزانه"}, {"text": "🎁 هدیه استارت"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }


# ============================================
# 🎮 کیبورد لغو
# ============================================
def cancel_keyboard():
    return {
        "keyboard": [
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }


# ============================================
# 🔢 تبدیل اعداد فارسی به انگلیسی
# ============================================
def convert_number(text):
    persian = "۰۱۲۳۴۵۶۷۸۹"
    english = "0123456789"
    for p, e in zip(persian, english):
        text = text.replace(p, e)
    return text


# ============================================
# 📢 پیام همگانی سریع (۱۰۰/ثانیه)
# ============================================
def broadcast_fast(owner_id, text):
    """ارسال سریع - ۱۰۰ نفر در ثانیه"""
    sent = 0
    failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    send_message(owner_id, f"📢 **شروع ارسال...**\n\n👥 کل: {total:,} نفر")
    
    batch = []
    for i, uid in enumerate(all_users, 1):
        batch.append(uid)
        if len(batch) >= BROADCAST_SPEED:
            def send_one(u):
                try:
                    r = send_message(int(u), text)
                    return r.get("ok", False)
                except:
                    return False
            
            results = list(executor.map(send_one, batch))
            sent += sum(1 for r in results if r)
            failed += sum(1 for r in results if not r)
            batch = []
            time.sleep(1)
            
            if (i // BROADCAST_SPEED) % 5 == 0:
                try:
                    send_message(owner_id, f"📊 پیشرفت: {i:,}/{total:,}\n✅ موفق: {sent:,}\n❌ ناموفق: {failed:,}")
                except:
                    pass
    
    if batch:
        for u in batch:
            try:
                r = send_message(int(u), text)
                if r.get("ok"):
                    sent += 1
                else:
                    failed += 1
            except:
                failed += 1
    
    send_message(
        owner_id,
        f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent:,}\n❌ ناموفق: {failed:,}\n📊 کل: {total:,}",
        owner_keyboard()
    )


# ============================================
# 💓 Ping Worker (هر ۳ دقیقه به مالک)
# ============================================
def ping_worker():
    while True:
        try:
            time.sleep(180)
            send_message(OWNER_ID, "ping")
        except:
            time.sleep(60)

# ═══ پایان بخش ۲ ═══
# ============================================
# 🎯 تابع اصلی پردازش پیام‌ها
# ============================================
def handle_message(message):
    global INVITE_REWARD
    
    try:
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]
        
        # ═══ گروه - فقط خوش‌آمد ═══
        if chat_type in ["group", "supergroup"]:
            if "new_chat_member" in message:
                new_member = message["new_chat_member"]
                new_name = new_member.get("first_name", "کاربر")
                group_name = message["chat"].get("title", "این گروه")
                welcome_text = (
                    f"👋 **{new_name}** به **{group_name}** خوش اومدی! 🎉\n\n"
                    f"🤖 من **ربات عضوگیر و سین‌زن** هستم!\n"
                    f"👥 می‌تونم برات عضو بیارم\n"
                    f"👁️ می‌تونم برات سین بزنم\n\n"
                    f"🚀 اگه خواستی کانال یا گروهت رو رشد بدی،\n"
                    f"بیا توی پیوی من:\n"
                    f"🤖 @Idneobot\n\n"
                    f"🐺 تیم DeepParse"
                )
                send_message(chat_id, welcome_text)
            return
        
        if chat_type == "channel":
            return
        
        user_id = str(message["from"]["id"])
        text = message.get("text", "").strip()
        name = message["from"].get("first_name", "داداش")
        
        username = message["from"].get("username", "")
        if username:
            get_user(user_id)["username"] = username
            save_db(db)
        
        # ═══ چک مسدود بودن ═══
        if user_id in db.get("banned", []):
            send_message(chat_id, "🚫 **دسترسی شما مسدود شده!**\n\n📩 اگه فکر می‌کنی اشتباه شده، به پشتیبانی پیام بده.")
            return
        
        # ═══ پردازش پیام پشتیبانی (کاربر) ═══
        if db.get("pending_support", {}).get(user_id, {}).get("step") == "waiting":
            if text in ["🔙 بازگشت", "❌ لغو"]:
                db["pending_support"].pop(user_id, None)
                save_db(db)
                send_message(chat_id, "🔙 برگشتی!", main_keyboard())
                return
            sup_id = str(int(time.time() * 1000))
            db["support_messages"][sup_id] = {
                "user_id": user_id,
                "name": name,
                "username": username,
                "text": text,
                "created_at": str(datetime.now())
            }
            save_db(db)
            kb = {"inline_keyboard": [
                [{"text": "✏️ جواب دادن", "callback_data": f"support_reply_{sup_id}"},
                 {"text": "❌ رد کردن", "callback_data": f"support_reject_{sup_id}"}]
            ]}
            send_message(
                int(OWNER_ID),
                f"💬 **پیام پشتیبانی جدید**\n\n"
                f"👤 نام: {name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"📛 یوزرنیم: @{username if username else 'ندارد'}\n\n"
                f"📝 پیام:\n{text}",
                kb
            )
            send_message(chat_id, "✅ **پیامت برای پشتیبانی ارسال شد!**\n\n💚 به زودی جواب می‌گیری.", main_keyboard())
            db["pending_support"].pop(user_id, None)
            save_db(db)
            return
        
        # ═══ پردازش پاسخ مالک به پشتیبانی ═══
        psr = db.get("pending_support_reply", {}).get(user_id, {})
        if psr.get("step") == "waiting" and user_id == OWNER_ID:
            sup_id = psr.get("sup_id")
            if sup_id in db.get("support_messages", {}):
                target = db["support_messages"][sup_id]["user_id"]
                try:
                    send_message(int(target), f"💬 **پاسخ پشتیبانی:**\n\n{text}")
                    send_message(chat_id, "✅ **جوابت ارسال شد!**", owner_keyboard())
                except:
                    send_message(chat_id, "❌ خطا!", owner_keyboard())
                db["support_messages"][sup_id]["replied"] = True
            db["pending_support_reply"].pop(user_id, None)
            save_db(db)
            return
        
        # ═══ پردازش مسدود کردن (مالک) ═══
        pb = db.get("pending_ban", {}).get(user_id, {})
        if pb.get("step") == "waiting" and user_id == OWNER_ID:
            uid = text.strip()
            if uid not in db["banned"]:
                db["banned"].append(uid)
            db["pending_ban"].pop(user_id, None)
            save_db(db)
            send_message(chat_id, f"🚫 **{uid} مسدود شد!**", owner_keyboard())
            try:
                send_message(int(uid), "🚫 **دسترسی شما مسدود شد!**\n\n⏳ نگران نباش، ممکنه بعداً رفع بشه.")
            except:
                pass
            return
        
        # ═══ پردازش رفع مسدودیت (مالک) ═══
        pu2 = db.get("pending_unban", {}).get(user_id, {})
        if pu2.get("step") == "waiting" and user_id == OWNER_ID:
            uid = text.strip()
            if uid in db.get("banned", []):
                db["banned"].remove(uid)
                save_db(db)
                send_message(chat_id, f"✅ **{uid} آزاد شد!**", owner_keyboard())
                try:
                    send_message(int(uid), "🎉 **مژده! مسدودیتت برداشته شد.**\n\n✅ دوباره می‌تونی از ربات استفاده کنی!")
                except:
                    pass
            else:
                send_message(chat_id, "❌ این کاربر مسدود نبود!", owner_keyboard())
            db["pending_unban"].pop(user_id, None)
            save_db(db)
            return
# ═══ پایان بخش ۳ ═══
        # ============ /start ============
        if text.startswith("/start"):
            parts = text.split(" ")
            if len(parts) > 1:
                inviter_id = parts[1]
                # ✅ ضد تقلب ۱: با لینک خودش نیاد
                if inviter_id != user_id:
                    # ✅ ضد تقلب ۲: قبلاً دعوت نشده
                    if user_id not in db["invited_users"]:
                        # ✅ ضد تقلب ۳: دعوت‌کننده وجود داره
                        if inviter_id in db["users"]:
                            db["invited_users"][user_id] = inviter_id
                            u = get_user(user_id)
                            u["invited_by"] = inviter_id
                            save_db(db)
                            # 📩 پیام مرحله ۱ به دعوت‌کننده
                            try:
                                send_message(
                                    int(inviter_id),
                                    f"🔔 **یه کاربر با لینک دعوت تو اومد!**\n\n"
                                    f"👤 کاربر: {name}\n"
                                    f"⏰ منتظر عضویت در کانال...\n\n"
                                    f"💡 وقتی عضو بشه، **{INVITE_REWARD} سکه** بهت اهدا میشه!"
                                )
                            except:
                                pass
            
            # چک عضویت
            if not check_joined(user_id):
                must_join(user_id)
                return
            
            user = get_user(user_id)
            if not user.get("got_start_gift"):
                add_coins(user_id, START_GIFT)
                user["got_start_gift"] = True
                
                # ✅ پاداش دعوت (مرحله دوم)
                inviter_id = user.get("invited_by")
                if inviter_id and user_id in db["invited_users"]:
                    if user_id not in db.get("rewarded_users", []):
                        add_coins(inviter_id, INVITE_REWARD)
                        inviter = get_user(inviter_id)
                        inviter["invite_count"] = inviter.get("invite_count", 0) + 1
                        db.setdefault("rewarded_users", []).append(user_id)
                        save_db(db)
                        # 📩 پیام مرحله ۲ به دعوت‌کننده
                        try:
                            send_message(
                                int(inviter_id),
                                f"🎉 **کاربر عضو کانال هم شد!**\n\n"
                                f"👤 کاربر: {name}\n"
                                f"✅ با لینک دعوت تو اومد\n"
                                f"✅ عضو کانال هم شد\n\n"
                                f"🎁 **{INVITE_REWARD} سکه بهت اهدا شد!** 💰\n"
                                f"💰 موجودی: {get_coins(inviter_id):,} سکه\n\n"
                                f"👥 تعداد کل دعوتات: {inviter['invite_count']} نفر"
                            )
                        except:
                            pass
                
                save_db(db)
                send_message(
                    chat_id,
                    f"👋 **سلام {name} جان!** 😎\n\n"
                    f"⚡ به هایپرسین خوش اومدی!\n"
                    f"🎁 **{START_GIFT} سکه هدیه** بهت اضافه شد!\n"
                    f"💰 موجودی: {get_coins(user_id):,} سکه\n\n"
                    f"از دکمه‌های زیر استفاده کن:",
                    main_keyboard()
                )
            else:
                send_message(
                    chat_id,
                    f"👋 **سلام {name} جان!** 😎\n\n"
                    f"از دکمه‌های زیر استفاده کن:",
                    main_keyboard()
                )
            return
# ═══ پایان بخش ۴ ═══
        # ═══ چک عضویت دکمه‌های اصلی ═══
        main_buttons = [
            "🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو",
            "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان",
            "👤 حساب کاربری", "💰 انتقال سکه", "📖 راهنما",
            "🎁 هدیه روزانه", "💬 پشتیبانی"
        ]
        if text in main_buttons:
            if not check_joined(user_id):
                must_join(user_id)
                return
        
        # ============ دکمه‌های عمومی ============
        if text in ["❌ لغو", "🔙 بازگشت"]:
            for key in [
                "pending_orders", "pending_members", "pending_gift",
                "pending_transfer", "pending_packet", "pending_coin_setting",
                "pending_support", "pending_support_reply", "pending_ban", "pending_unban"
            ]:
                db.get(key, {}).pop(user_id, None)
            save_db(db)
            send_message(chat_id, "🔙 **برگشتی به منوی اصلی!**", main_keyboard())
            return
        
        if text == OWNER_PASSWORD:
            send_message(chat_id, "👑 **پنل مالک باز شد!** 🚀\nیکی از گزینه‌ها رو انتخاب کن:", owner_keyboard())
            return
        
        if text == COIN_PASSWORD:
            add_coins(user_id, INFINITE_COINS)
            send_message(chat_id, f"💰 **{INFINITE_COINS:,} سکه بهت اضافه شد!** 🎉\n💳 موجودی: {get_coins(user_id):,} سکه")
            return
        
        # ═══ کسب سکه ═══
        if text == "🪙 کسب سکه":
            keyboard = {"inline_keyboard": [[{"text": "👁️ برو به کانال", "url": CHANNEL_LINK}]]}
            send_message(
                chat_id,
                f"🔗 **برو توی کانال و روی دکمه «دیدم» زیر پیام‌ها بزن تا سکه بگیری!** 💰\n\n{CHANNEL_LINK}",
                keyboard
            )
            return
        
        # ═══ سکه‌های من ═══
        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 **موجودی تو:** {get_coins(user_id):,} سکه 🪙")
            return
        
        # ═══ هدیه روزانه ═══
        if text == "🎁 هدیه روزانه":
            user = get_user(user_id)
            now = datetime.now()
            last = user.get("last_daily")
            if last:
                try:
                    lt = datetime.fromisoformat(last)
                    if now - lt < timedelta(hours=24):
                        rem = timedelta(hours=24) - (now - lt)
                        h = rem.seconds // 3600
                        m = (rem.seconds % 3600) // 60
                        send_message(chat_id, f"⏰ **صبر کن!**\n\nهنوز {h} ساعت و {m} دقیقه مونده!")
                        return
                except:
                    pass
            gift = get_setting("daily_gift", DAILY_GIFT)
            add_coins(user_id, gift)
            user["last_daily"] = str(now)
            save_db(db)
            send_message(chat_id, f"🎁 **هدیه روزانه گرفتی!**\n\n💰 +{gift} سکه\n💰 موجودی: {get_coins(user_id):,} سکه")
            return
        
        # ═══ راهنما ═══
        if text == "📖 راهنما":
            help_text = (
                f"📖 **راهنمای ربات هایپرسین ⚡**\n\n"
                f"🤖 هایپرسین ترکیبی از ربات سین‌زن و عضوگیر است.\n\n"
                f"👁️ **بخش سین‌زن**\n"
                f"• هر سین = 🪙 ۱ سکه لازم است\n"
                f"• حداقل سفارش: ۱۵ سین\n\n"
                f"👥 **بخش عضوگیر**\n"
                f"• هر عضو = 🪙 ۵ سکه لازم دارد\n"
                f"• حداقل سفارش: ۱ عضو\n\n"
                f"💰 **انتقال سکه:**\n"
                f"• دکمه انتقال سکه رو بزن\n"
                f"• آیدی عددی طرف رو بفرست\n"
                f"• (از حساب کاربری → کپی آیدی)\n"
                f"• مقدار سکه رو وارد کن\n\n"
                f"💰 **روش‌های کسب سکه در کانال**\n"
                f"• 👁️ دکمه «دیدم» رو بزن در کانال → +۱ سکه\n"
                f"• 👥 دکمه «عضو شدم» رو بزن در کانال → +۳ سکه\n"
                f"• 🎁 کد هدیه → دریافت سکه جایزه\n"
                f"• 🎉 اولین عضویت در کانال ما → ۲۵ سکه هدیه\n"
                f"• 👥 دعوت دوستان → هر دعوت = {INVITE_REWARD} سکه\n\n"
                f"⚠️ **قوانین**\n"
                f"• پیام های غیر قانونی ثبت نمیشه و شما از کانال حذف میشید\n\n"
                f"✨ از استفاده از هایپرسین سپاسگزاریم."
            )
            send_message(chat_id, help_text)
            return
# ═══ پایان بخش ۵ ═══
        # ═══ حساب کاربری ═══
        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            send_message(
                chat_id,
                f"👤 **حساب کاربری:**\n\n"
                f"👤 نام: {name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"📛 یوزرنیم: @{u['username'] if u['username'] else 'ندارد'}\n"
                f"🪙 موجودی: {u['coins']:,} سکه\n"
                f"👥 دعوت کرده: {u.get('invite_count', 0)} نفر",
                {"inline_keyboard": [
                    [{"text": "📋 کپی آیدی عددی", "callback_data": "copy_id"}],
                    [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]
                ]}
            )
            return
        
        # ═══ دعوت دوستان ═══
        if text == "👥 دعوت دوستان":
            send_message(
                chat_id,
                f"👥 **دعوت دوستان:**\n\n"
                f"🔗 لینک اختصاصی تو:\n"
                f"https://ble.ir/{BOT_USERNAME}?start={user_id}\n\n"
                f"🎁 **هر دعوت = {INVITE_REWARD} سکه** 💰\n\n"
                f"👥 تا حالا: {get_user(user_id).get('invite_count', 0)} نفر دعوت کردی"
            )
            return
        
        # ═══ انتقال سکه (فقط مالک) ═══
        if text == "💰 انتقال سکه":
            if user_id != OWNER_ID:
                send_message(chat_id, "❌ این قابلیت فقط برای مالک فعاله!", main_keyboard())
                return
            db["pending_transfer"][user_id] = {"step": "waiting_id"}
            save_db(db)
            send_message(chat_id, "🆔 **آیدی عددی کاربر مقصد رو بفرست:**", cancel_keyboard())
            return
        
        # ═══ ثبت سفارش سین ═══
        if text == "👁️ ثبت سفارش سین":
            db["pending_orders"][user_id] = {"step": "waiting_forward"}
            save_db(db)
            send_message(
                chat_id,
                "📩 **لطفاً پیام مورد نظر را از کانال فوروارد کنید.**\n\n"
                "⚠️ حتماً باید از کانال فوروارد شود!\n"
                "📢 از هر کانالی می‌تونی فوروارد کنی.",
                cancel_keyboard()
            )
            return
        
        # ═══ ثبت سفارش عضو ═══
        if text == "👥 ثبت سفارش عضو":
            db["pending_members"][user_id] = {"step": "waiting_link"}
            save_db(db)
            send_message(
                chat_id,
                "📩 **لطفاً لینک کانال مورد نظر را بفرستید.**\n\n"
                "⚠️ حتماً باید کانال باشد!\n"
                "🚫 گروه قبول نمیشود!",
                cancel_keyboard()
            )
            return
        
        # ═══ زدن کد هدیه ═══
        if text == "🎁 زدن کد هدیه":
            db["pending_orders"][user_id] = {"step": "waiting_gift_code"}
            save_db(db)
            send_message(chat_id, "🎁 **لطفاً کد هدیه رو وارد کن:**", cancel_keyboard())
            return
        
        # ═══ پشتیبانی ═══
        if text == "💬 پشتیبانی":
            db["pending_support"][user_id] = {"step": "waiting"}
            save_db(db)
            send_message(
                chat_id,
                "💬 **پشتیبانی**\n\n"
                "لطفاً پیامت رو بفرست تا کمکت کنیم:",
                cancel_keyboard()
            )
            return
# ═══ پایان بخش ۶ ═══
        # ============ پنل مالک ============
        
        # ═══ تنظیم سکه ═══
        if text == "⚙️ تنظیم سکه" and user_id == OWNER_ID:
            send_message(
                chat_id,
                f"⚙️ **تنظیم سکه:**\n\n"
                f"👁️ سکه دیدم: {get_setting('seen_reward', 1)}\n"
                f"📝 سکه سین: {get_setting('sin_cost', 1)}\n"
                f"👥 هزینه عضو: {get_setting('member_cost', 5)}\n"
                f"🪙 پاداش معمولی: {get_setting('member_normal_reward', 3)}\n"
                f"🛡️ پاداش تضمینی: {get_setting('member_guaranteed_reward', 7)}\n"
                f"👥 سکه دعوت: {get_setting('invite_reward', 15)}\n"
                f"🎁 هدیه روزانه: {get_setting('daily_gift', 5)}\n"
                f"🎁 هدیه استارت: {get_setting('start_gift', 25)}\n\n"
                f"کدوم رو تغییر بدم؟",
                coin_settings_keyboard()
            )
            return
        
        coin_settings_map = {
            "👁️ سکه دیدم": ("seen_reward", "سکه دیدم"),
            "📝 سکه سین": ("sin_cost", "سکه سین"),
            "👥 هزینه عضو": ("member_cost", "هزینه عضو"),
            "🪙 پاداش معمولی": ("member_normal_reward", "پاداش معمولی"),
            "🛡️ پاداش تضمینی": ("member_guaranteed_reward", "پاداش تضمینی"),
            "👥 سکه دعوت": ("invite_reward", "سکه دعوت"),
            "🎁 هدیه روزانه": ("daily_gift", "هدیه روزانه"),
            "🎁 هدیه استارت": ("start_gift", "هدیه استارت")
        }
        
        if text in coin_settings_map and user_id == OWNER_ID:
            key, label = coin_settings_map[text]
            db["pending_coin_setting"][user_id] = {"key": key}
            save_db(db)
            send_message(
                chat_id,
                f"✏️ **{label}**\n\n"
                f"مقدار فعلی: {get_setting(key, 0)}\n\n"
                f"مقدار جدید رو بفرست:",
                cancel_keyboard()
            )
            return
        
        # ═══ پردازش مقدار جدید تنظیم سکه ═══
        pcs = db.get("pending_coin_setting", {}).get(user_id, {})
        if pcs.get("key") and user_id == OWNER_ID:
            try:
                val = int(convert_number(text))
                db["settings"][pcs["key"]] = val
                del db["pending_coin_setting"][user_id]
                save_db(db)
                send_message(chat_id, f"✅ **ذخیره شد: {val}**\n\n(تو همه جا اعمال شد)", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر بفرست!", coin_settings_keyboard())
            return
        
        # ═══ جوین اجباری ═══
        if text == "🔒 جوین اجباری" and user_id == OWNER_ID:
            channels = db.get("join_channels", [])
            msg = "🔒 **جوین اجباری**\n\n📊 **لیست کانال‌ها:**\n"
            if channels:
                for i, ch in enumerate(channels, 1):
                    msg += f"{i}. {ch}\n"
            else:
                msg += "(خالی)\n"
            msg += "\n📌 **افزودن:** `add @channel`\n📌 **حذف:** `del 1`"
            send_message(chat_id, msg, cancel_keyboard())
            return
        
        if text.startswith("add ") and user_id == OWNER_ID:
            ch = text[4:].strip()
            if ch not in db.get("join_channels", []):
                db.setdefault("join_channels", []).append(ch)
                save_db(db)
            send_message(chat_id, f"✅ **{ch} اضافه شد!**", owner_keyboard())
            return
        
        if text.startswith("del ") and user_id == OWNER_ID:
            try:
                idx = int(text[4:].strip()) - 1
                channels = db.get("join_channels", [])
                if 0 <= idx < len(channels):
                    removed = channels.pop(idx)
                    save_db(db)
                    send_message(chat_id, f"✅ **{removed} حذف شد!**", owner_keyboard())
                else:
                    send_message(chat_id, "❌ شماره اشتباه!", owner_keyboard())
            except:
                send_message(chat_id, "❌ فرمت: `del 1`", owner_keyboard())
            return
        
        # ═══ مسدود کردن ═══
        if text == "🚫 مسدود کردن" and user_id == OWNER_ID:
            db["pending_ban"][user_id] = {"step": "waiting"}
            save_db(db)
            send_message(chat_id, "🚫 **آیدی عددی کاربر رو بفرست:**", cancel_keyboard())
            return
        
        # ═══ رفع مسدودیت ═══
        if text == "✅ رفع مسدودیت" and user_id == OWNER_ID:
            db["pending_unban"][user_id] = {"step": "waiting"}
            save_db(db)
            send_message(chat_id, "✅ **آیدی عددی کاربر رو بفرست:**", cancel_keyboard())
            return
# ═══ پایان بخش ۷ ═══
        # ═══ ساخت کد هدیه ═══
        if text == "🎁 ساخت کد هدیه" and user_id == OWNER_ID:
            db["pending_gift"][user_id] = {"step": "waiting_coins"}
            save_db(db)
            send_message(chat_id, "💰 **چند سکه توی کد باشه؟**", owner_keyboard())
            return
        
        # ═══ سکه پاکت ═══
        if text == "🎁 سکه پاکت" and user_id == OWNER_ID:
            db["pending_packet"][user_id] = {"step": "waiting_coins"}
            save_db(db)
            send_message(chat_id, "💰 **چند سکه توی پاکت باشه؟**", owner_keyboard())
            return
        
        # ═══ افزودن سکه به همه ═══
        if text == "💰 افزودن سکه به همه" and user_id == OWNER_ID:
            db["pending_add_coins"][user_id] = {"step": "waiting_amount"}
            save_db(db)
            send_message(chat_id, "💰 **چند سکه به همه کاربرا اضافه بشه؟**\n\n📌 فقط عدد بفرست!", owner_keyboard())
            return
        
        # ═══ تغییر سکه دعوت ═══
        if text == "🎁 تغییر سکه دعوت" and user_id == OWNER_ID:
            db["pending_gift"][user_id] = {"step": "waiting_invite_reward"}
            save_db(db)
            send_message(
                chat_id,
                f"🎁 **تغییر سکه دعوت:**\n\n"
                f"💰 سکه فعلی هر دعوت: **{INVITE_REWARD}**\n\n"
                f"🔢 سکه جدید رو وارد کن:\n"
                f"مثال: ۲۰",
                owner_keyboard()
            )
            return
        
        # ═══ آمار کل ═══
        if text == "📊 آمار کل" and user_id == OWNER_ID:
            stats = db["stats"]
            total_users = len(db["users"])
            joined_users = sum(1 for u in db["users"].values() if u["joined"])
            shamsi_date = get_shamsi_date()
            shamsi_time = datetime.now().strftime("%H:%M:%S")
            send_message(
                chat_id,
                f"📊 **آمار کلی ربات:**\n\n"
                f"👥 کاربران کل: {total_users}\n"
                f"✅ عضو کانال: {joined_users}\n"
                f"📝 سفارشات سین: {stats['total_orders']}\n"
                f"🔄 فعال سین: {stats['total_orders'] - stats['completed_orders']}\n"
                f"✅ تکمیل سین: {stats['completed_orders']}\n"
                f"👥 سفارشات عضو: {stats.get('total_members', 0)}\n"
                f"✅ تکمیل عضو: {stats.get('completed_members', 0)}\n"
                f"🗑️ حذف شده: {stats['deleted_messages']}\n"
                f"📅 تاریخ: {shamsi_date}\n"
                f"⏰ ساعت: {shamsi_time}",
                owner_keyboard()
            )
            return
        
        # ═══ پیام همگانی ═══
        if text == "📢 پیام همگانی" and user_id == OWNER_ID:
            db["pending_broadcast"][user_id] = {"step": "waiting_message"}
            save_db(db)
            send_message(chat_id, "📢 **پیام همگانی رو بفرست:**", owner_keyboard())
            return
        
        # ═══ رتبه‌بندی ═══
        if text == "🏆 رتبه‌بندی" and user_id == OWNER_ID:
            users_sorted = sorted(db["users"].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
            msg = "🏆 **رتبه‌بندی کاربران:**\n\n"
            for i, (uid, data) in enumerate(users_sorted, 1):
                uname = data.get("username", "")
                if uname:
                    msg += f"{i}. @{uname} → {data['coins']:,} سکه\n"
                else:
                    msg += f"{i}. کاربر {uid[:6]}... → {data['coins']:,} سکه\n"
            send_message(chat_id, msg, owner_keyboard())
            return
        
        # ═══ بازگشت مالک ═══
        if text == "🔙 بازگشت" and user_id == OWNER_ID:
            send_message(chat_id, "🔙 **برگشتی به منوی اصلی!**", main_keyboard())
            return
# ═══ پایان بخش ۸ ═══
        # ============================================
        # 🎁 سکه پاکت (پردازش)
        # ============================================
        pp = db.get("pending_packet", {}).get(user_id, {})
        if pp.get("step") == "waiting_coins":
            try:
                db["pending_packet"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db(db)
                send_message(chat_id, "👥 **چند نفره باشه؟**", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", owner_keyboard())
            return
        
        if pp.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                db["pending_packet"][user_id]["step"] = "waiting_text"
                db["pending_packet"][user_id]["capacity"] = cap
                save_db(db)
                send_message(chat_id, "📝 **متن پاکت چی باشه؟**", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", owner_keyboard())
            return
        
        if pp.get("step") == "waiting_text":
            packet_text = text.strip()
            packet_coins = pp["coins"]
            packet_cap = pp["capacity"]
            packet_id = str(int(time.time() * 1000))
            db["coin_packets"][packet_id] = {
                "coins": packet_coins,
                "capacity": packet_cap,
                "text": packet_text,
                "used_by": []
            }
            kb = {"inline_keyboard": [[{"text": "🎁 باز کردن سکه", "callback_data": f"packet_{packet_id}"}]]}
            send_message(CHANNEL_ID, f"🎁 **سکه پاکت**\n\n{packet_text}", kb)
            db["pending_packet"].pop(user_id, None)
            save_db(db)
            send_message(chat_id, "✅ **سکه پاکت توی کانال گذاشته شد!** 🎉", owner_keyboard())
            return
        
        # ============================================
        # 💰 انتقال سکه (پردازش)
        # ============================================
        pt = db["pending_transfer"].get(user_id, {})
        if pt.get("step") == "waiting_id":
            target = text.strip()
            if target in db["users"] and target != user_id:
                db["pending_transfer"][user_id] = {"step": "waiting_amount", "target": target}
                save_db(db)
                send_message(
                    chat_id,
                    f"💰 **چند سکه میخوای به کاربر {target} انتقال بدی؟**\n"
                    f"💰 موجودی تو: {get_coins(user_id):,} سکه",
                    cancel_keyboard()
                )
            else:
                send_message(chat_id, "❌ کاربر یافت نشد یا نمیتونی به خودت انتقال بدی!", main_keyboard())
                db["pending_transfer"].pop(user_id, None)
                save_db(db)
            return
        
        if pt.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                target = pt["target"]
                if amount <= 0:
                    send_message(chat_id, "❌ عدد باید بزرگتر از صفر باشه!", main_keyboard())
                elif remove_coins(user_id, amount):
                    add_coins(target, amount)
                    send_message(
                        chat_id,
                        f"✅ **{amount} سکه به کاربر {target} انتقال دادی!**\n"
                        f"💰 موجودی جدید: {get_coins(user_id):,} سکه",
                        main_keyboard()
                    )
                    try:
                        sender_name = get_user(user_id).get("username", name)
                        send_message(
                            int(target),
                            f"🎁 **کاربر {sender_name} برات {amount} سکه انتقال داد!** 🎉\n"
                            f"💰 موجودی: {get_coins(target):,} سکه"
                        )
                    except:
                        pass
                else:
                    send_message(chat_id, "❌ سکه کافی نداری!", main_keyboard())
            except:
                send_message(chat_id, "❌ لطفاً یه عدد معتبر وارد کن!", main_keyboard())
            db["pending_transfer"].pop(user_id, None)
            save_db(db)
            return
# ═══ پایان بخش ۹ ═══
        # ============================================
        # 💰 افزودن سکه به همه (پردازش)
        # ============================================
        pac = db["pending_add_coins"].get(user_id, {})
        if pac.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                if amount <= 0:
                    send_message(chat_id, "❌ عدد باید بزرگتر از صفر باشه!", owner_keyboard())
                    return
                count = 0
                for uid in db["users"]:
                    add_coins(uid, amount)
                    count += 1
                del db["pending_add_coins"][user_id]
                save_db(db)
                send_message(chat_id, f"✅ **{amount} سکه به {count} کاربر اضافه شد!** 🎉", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", owner_keyboard())
            return
        
        # ============================================
        # 🎁 تغییر سکه دعوت (پردازش)
        # ============================================
        pg = db["pending_gift"].get(user_id, {})
        if pg.get("step") == "waiting_invite_reward":
            try:
                new_val = int(convert_number(text))
                old_val = INVITE_REWARD
                INVITE_REWARD = new_val
                db["invite_reward"] = new_val
                del db["pending_gift"][user_id]
                save_db(db)
                send_message(
                    chat_id,
                    f"✅ **سکه دعوت تغییر کرد!**\n\n"
                    f"💰 قبلی: {old_val}\n"
                    f"💰 جدید: **{new_val}**\n\n"
                    f"📝 متن دکمه دعوت هم آپدیت شد!",
                    owner_keyboard()
                )
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", owner_keyboard())
            return
        
        # ============================================
        # 👁️ سین‌زن (پردازش)
        # ============================================
        pending = db["pending_orders"].get(user_id, {})
        
        if pending.get("step") == "waiting_forward":
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db["pending_orders"][user_id] = {
                    "step": "waiting_count",
                    "message_id": message["message_id"],
                    "from_chat_id": message["forward_from_chat"]["id"]
                }
                save_db(db)
                coins = get_coins(user_id)
                send_message(
                    chat_id,
                    f"🔢 **چند سین نیاز داری داداش؟**\n\n"
                    f"💰 هر سین = {SIN_COST} سکه\n"
                    f"💳 موجودی فعلی تو: {coins:,} سکه\n\n"
                    f"⚠️ حداقل: {MIN_SIN} سین\n\n"
                    f"📌 فقط یه عدد بفرست (فارسی یا انگلیسی)!",
                    cancel_keyboard()
                )
            else:
                send_message(
                    chat_id,
                    f"❌ **این پیام از کانال نیست!**\n\n"
                    f"⚠️ لطفاً پیام رو از یه **کانال** فوروارد کن.",
                    cancel_keyboard()
                )
            return
        
        if pending.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_SIN:
                    send_message(chat_id, f"❌ حداقل باید {MIN_SIN} سین ثبت کنی!", cancel_keyboard())
                    return
                coins = get_coins(user_id)
                total_cost = count * SIN_COST
                if coins < total_cost:
                    send_message(
                        chat_id,
                        f"❌ سکه کافی نداری داداش!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}",
                        cancel_keyboard()
                    )
                    del db["pending_orders"][user_id]
                    save_db(db)
                    return
                remove_coins(user_id, total_cost)
                fwd_result = forward_message(CHANNEL_ID, chat_id, pending["message_id"])
                if fwd_result.get("ok"):
                    fwd_msg_id = fwd_result["result"]["message_id"]
                    db["order_counter"] = db.get("order_counter", 0) + 1
                    order_number = db["order_counter"]
                    order_id = str(int(time.time() * 1000))
                    db["orders"][order_id] = {
                        "user_id": user_id,
                        "count": count,
                        "message_id": fwd_msg_id,
                        "reply_message_id": None,
                        "seen_count": 0,
                        "status": "active",
                        "order_number": order_number
                    }
                    db["seen_records"][order_id] = []
                    db["stats"]["total_orders"] += 1
                    get_user(user_id)["total_orders"] += 1
                    
                    keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": "👁️ دیدم", "callback_data": f"seen_{order_id}"},
                                {"text": "🤖 مشاهده ربات", "url": BOT_LINK}
                            ],
                            [{"text": "🚨 گزارش", "callback_data": f"report_{order_id}"}]
                        ]
                    }
                    
                    reply_result = send_reply(
                        CHANNEL_ID, fwd_msg_id,
                        f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: 0\n#{order_number}",
                        keyboard
                    )
                    
                    if reply_result.get("ok"):
                        db["orders"][order_id]["reply_message_id"] = reply_result["result"]["message_id"]
                    
                    del db["pending_orders"][user_id]
                    save_db(db)
                    
                    send_message(
                        chat_id,
                        f"✅ **سفارش با موفقیت ثبت شد!** 🎉\n\n"
                        f"🔢 تعداد سین: {count}\n"
                        f"💰 هزینه: {total_cost} سکه\n"
                        f"💳 موجودی جدید: {get_coins(user_id):,} سکه\n"
                        f"📝 شماره سفارش: #{order_number}\n\n"
                        f"👁️ منتظر باش تا کاربرا دکمه «دیدم» رو بزنن!",
                        main_keyboard()
                    )
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ **خطا در ثبت سفارش!** سکه‌ها برگشت داده شد.", main_keyboard())
                    del db["pending_orders"][user_id]
                    save_db(db)
            except ValueError:
                send_message(chat_id, "❌ **لطفاً یه عدد معتبر وارد کن!**", cancel_keyboard())
            return
# ═══ پایان بخش ۱۰ ═══
        # ============================================
        # 👥 عضوگیر (پردازش)
        # ============================================
        pmem = db["pending_members"].get(user_id, {})
        
        if pmem.get("step") == "waiting_link":
            link = text.strip()
            db["pending_members"][user_id] = {"step": "waiting_admin", "link": link}
            save_db(db)
            send_message(
                chat_id,
                "🔗 **لطفاً منو توی اون کانال ادمین کن!**\n\n"
                "⚠️ با تمام دسترسی‌ها\n"
                "✅ بعد بنویس: **ادمین کردم**",
                cancel_keyboard()
            )
            return
        
        if pmem.get("step") == "waiting_admin":
            if text.strip() == "ادمین کردم":
                link = pmem["link"]
                try:
                    if "ble.ir/" in link:
                        chat_username = "@" + link.split("ble.ir/")[-1].strip("/")
                    elif link.startswith("@"):
                        chat_username = link
                    elif link.startswith("https://"):
                        chat_username = "@" + link.split("/")[-1].strip("/")
                    else:
                        chat_username = link
                    
                    chat_info = get_chat(chat_username)
                    if chat_info.get("ok"):
                        target_chat_id = chat_info["result"]["id"]
                        member_status = get_chat_member(target_chat_id, int(TOKEN.split(":")[0]))
                        if member_status.get("ok") and member_status["result"]["status"] == "administrator":
                            db["pending_members"][user_id] = {
                                "step": "waiting_type",
                                "link": link,
                                "chat_id": target_chat_id
                            }
                            save_db(db)
                            send_message(
                                chat_id,
                                "📥 **لطفاً نوع عضویت را انتخاب کنید:**\n\n"
                                "┌──────────────────────────┐\n"
                                "│  🥇 **۱. نوع تضمینی**    │\n"
                                "│                          │\n"
                                "│  💰 هزینه هر عضو: ۱۰ سکه │\n"
                                "│  🛡️ کاربر ۴۸ ساعت بمونه  │\n"
                                "│  ❌ اگه زودتر ترک کنه    │\n"
                                "│     → کاربر ۷ سکه جریمه  │\n"
                                "│     → ۵ سکه به شما برگشت  │\n"
                                "├──────────────────────────┤\n"
                                "│  🥉 **۲. نوع معمولی**    │\n"
                                "│                          │\n"
                                "│  💰 هزینه هر عضو: ۵ سکه  │\n"
                                "│  👤 کاربر میتونه هر وقت  │\n"
                                "│     ترک کنه              │\n"
                                "│  ⏰ حداقل ۲ دقیقه بمونه  │\n"
                                "└──────────────────────────┘\n\n"
                                "🔢 لطفاً عدد **۱ یا ۲** را وارد کنید:",
                                cancel_keyboard()
                            )
                        else:
                            send_message(chat_id, "❌ **هنوز ادمین نشدم!**\n\nبا تمام دسترسی‌ها ادمین کن و دوباره بنویس: ادمین کردم", cancel_keyboard())
                    else:
                        send_message(chat_id, "❌ **لینک نامعتبره!**\n\nلینک درست رو بفرست.", cancel_keyboard())
                except Exception as e:
                    send_message(chat_id, "❌ **خطا!**\n\nلینک رو چک کن یا دوباره بنویس: ادمین کردم", cancel_keyboard())
            else:
                send_message(chat_id, "⚠️ لطفاً بنویس: **ادمین کردم**", cancel_keyboard())
            return
# ═══ پایان بخش ۱۱ ═══
        # ═══ انتخاب نوع عضویت (فارسی/انگلیسی) ═══
        if pmem.get("step") == "waiting_type":
            choice = convert_number(text.strip())
            if choice in ["1", "2"]:
                # ✅ ۱ = تضمینی | ۲ = معمولی
                order_type = "guaranteed" if choice == "1" else "normal"
                db["pending_members"][user_id]["order_type"] = order_type
                db["pending_members"][user_id]["step"] = "waiting_count"
                save_db(db)
                cost_per = 10 if order_type == "guaranteed" else 5
                type_name = "تضمینی" if order_type == "guaranteed" else "معمولی"
                send_message(
                    chat_id,
                    f"📥 **ثبت سفارش عضو - {type_name}**\n\n"
                    f"👥 تعداد عضو موردنیاز را وارد کن داداش\n"
                    f"💰 هزینه هر عضو: {cost_per} سکه\n"
                    f"📌 حداقل سفارش: ۱ عضو\n\n"
                    f"⌨️ لطفاً فقط عدد (مثلاً 50 یا ۵۰) را ارسال کنید.",
                    cancel_keyboard()
                )
            else:
                send_message(chat_id, "❌ فقط عدد **۱ یا ۲** را وارد کنید!", cancel_keyboard())
            return
        
        # ═══ تعداد عضو (پردازش) ═══
        if pmem.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_MEMBER:
                    send_message(chat_id, f"❌ حداقل باید {MIN_MEMBER} عضو انتخاب کنی!", cancel_keyboard())
                    return
                
                link = pmem["link"]
                target_chat_id = pmem["chat_id"]
                order_type = pmem.get("order_type", "normal")
                cost_per = 10 if order_type == "guaranteed" else 5
                total_cost = count * cost_per
                
                coins = get_coins(user_id)
                if coins < total_cost:
                    send_message(
                        chat_id,
                        f"❌ سکه کافی نداری!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}",
                        cancel_keyboard()
                    )
                    del db["pending_members"][user_id]
                    save_db(db)
                    return
                
                remove_coins(user_id, total_cost)
                db["member_counter"] = db.get("member_counter", 0) + 1
                mnum = db["member_counter"]
                mid = str(int(time.time() * 1000))
                
                # ✅ پاداش بر اساس نوع
                reward = 7 if order_type == "guaranteed" else 3
                type_name = "تضمینی" if order_type == "guaranteed" else "معمولی"
                
                db["member_orders"][mid] = {
                    "user_id": user_id,
                    "count": count,
                    "link": link,
                    "chat_id": target_chat_id,
                    "message_id": None,
                    "seen_count": 0,
                    "status": "active",
                    "order_number": mnum,
                    "order_type": order_type,
                    "reward": reward
                }
                db["member_records"][mid] = []
                db["stats"]["total_members"] = db["stats"].get("total_members", 0) + 1
                
                # ✅ فیکس لینک دکمه
                url_link = link
                if not url_link.startswith("http"):
                    if url_link.startswith("@"):
                        url_link = f"https://ble.ir/{url_link[1:]}"
                    elif url_link.startswith("ble.ir/"):
                        url_link = f"https://{url_link}"
                    else:
                        url_link = f"https://ble.ir/{url_link.lstrip('/')}"
                
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": f"🪙 {reward} سکه میگیری!", "callback_data": f"info_{mid}"}
                        ],
                        [
                            {"text": "🔗 عضویت در کانال", "url": url_link},
                            {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}
                        ],
                        [
                            {"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"},
                            {"text": "🤖 مشاهده ربات", "url": BOT_LINK}
                        ]
                    ]
                }
                
                # ✅ متن کانال
                if order_type == "normal":
                    warning_text2 = "\n⏰ حداقل ۲ دقیقه عضو بمون!"
                else:
                    warning_text2 = "\n🛡️ باید ۴۸ ساعت عضو بمونی!\n❌ ترک زودتر = ۷ سکه جریمه"
                
                sent = send_message(
                    CHANNEL_ID,
                    f"📋 **سفارش عضو - {type_name}**\n\n"
                    f"🔗 لینک کانال:\n{url_link}\n\n"
                    f"👥 تعداد عضو درخواستی: **{count}**\n"
                    f"✅ تعداد عضو شده: **0**\n"
                    f"📝 شماره سفارش: #{mnum}\n\n"
                    f"🪙 **{reward} سکه میگیری!**{warning_text2}",
                    keyboard
                )
                
                if sent.get("ok"):
                    db["member_orders"][mid]["message_id"] = sent["result"]["message_id"]
                
                del db["pending_members"][user_id]
                save_db(db)
                
                send_message(
                    chat_id,
                    f"🎉 **سفارش شما با موفقیت ثبت شد!**\n\n"
                    f"⏳ منتظر باش کاربرا عضو کانالت بشن.\n\n"
                    f"💰 موجودی جدید: {get_coins(user_id):,} سکه",
                    main_keyboard()
                )
            except Exception as e:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", cancel_keyboard())
            return
# ═══ پایان بخش ۱۲ ═══
        # ============================================
        # 🎁 کد هدیه (پردازش)
        # ============================================
        if pending.get("step") == "waiting_gift_code":
            code = text.upper().strip()
            if code in db["gift_codes"]:
                g = db["gift_codes"][code]
                u = get_user(user_id)
                if code in u["used_gift_codes"]:
                    send_message(chat_id, "❌ تو قبلاً این کد رو زدی!", main_keyboard())
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ این کد هدیه تموم شده! ظرفیتش پر شده.", main_keyboard())
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    u["used_gift_codes"].append(code)
                    save_db(db)
                    send_message(
                        chat_id,
                        f"🎉 **تبریک! {g['coins']:,} سکه!**\n"
                        f"💳 موجودی: {get_coins(user_id):,}",
                        main_keyboard()
                    )
            else:
                send_message(chat_id, "❌ کد نامعتبر!", main_keyboard())
            del db["pending_orders"][user_id]
            save_db(db)
            return
        
        # ============================================
        # 🎁 ساخت کد هدیه (پردازش مالک)
        # ============================================
        pg = db["pending_gift"].get(user_id, {})
        if pg.get("step") == "waiting_coins":
            try:
                db["pending_gift"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db(db)
                send_message(chat_id, "👥 **ظرفیت چند نفره؟**", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", owner_keyboard())
            return
        
        if pg.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                db["gift_codes"][code] = {"coins": pg["coins"], "capacity": cap, "used_by": []}
                del db["pending_gift"][user_id]
                save_db(db)
                send_message(
                    chat_id,
                    f"🎁 **کد هدیه ساخته شد!**\n\n"
                    f"🔑 کد: `{code}`\n"
                    f"💰 سکه: {pg['coins']:,}\n"
                    f"👥 ظرفیت: {cap} نفر\n\n"
                    f"📊 هرکی استفاده کنه بهت خبر می‌دم!",
                    owner_keyboard()
                )
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", owner_keyboard())
            return
# ═══ پایان بخش ۱۳ ═══
        # ============================================
        # 📢 پیام همگانی (پردازش - سریع)
        # ============================================
        pbc = db["pending_broadcast"].get(user_id, {})
        if pbc.get("step") == "waiting_message":
            del db["pending_broadcast"][user_id]
            save_db(db)
            executor.submit(broadcast_fast, user_id, text)
            send_message(chat_id, "📢 **شروع ارسال سریع...**\n\n(۱۰۰ نفر در ثانیه)", owner_keyboard())
            return
        
        # ============ پیش‌فرض ============
        send_message(
            chat_id,
            f"👋 **سلام {name} جان!** 😎\n\n"
            f"⚡ من هایپرسین هستم! ابرسین‌زن + عضوگیر\n"
            f"🎁 اولین عضویت = {START_GIFT} سکه هدیه\n\n"
            f"از دکمه‌های زیر استفاده کن:",
            main_keyboard()
        )
    
    except Exception as e:
        print(f"⚠️ خطا در handle_message: {e}")
        traceback.print_exc()
        gc.collect()
        time.sleep(0.001)

# ═══ پایان بخش ۱۴ ═══
# ============================================
# 🔘 پردازش دکمه‌های شیشه‌ای
# ============================================
def handle_callback(callback):
    try:
        callback_id = callback["id"]
        data = callback["data"]
        user_id = callback["from"]["id"]
        user_id_str = str(user_id)
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id", CHANNEL_ID)
        
        # ═══ چک مسدود بودن ═══
        if user_id_str in db.get("banned", []):
            answer_callback(callback_id, "🚫 شما مسدود شدید!", show_alert=True)
            return
        
        # ═══ پشتیبانی — جواب دادن ═══
        if data.startswith("support_reply_"):
            sup_id = data.replace("support_reply_", "")
            if sup_id not in db.get("support_messages", {}):
                answer_callback(callback_id, "❌!", show_alert=True)
                return
            if user_id_str != str(OWNER_ID):
                answer_callback(callback_id, "❌ دسترسی نداری!", show_alert=True)
                return
            db["pending_support_reply"][user_id_str] = {"step": "waiting", "sup_id": sup_id}
            save_db(db)
            answer_callback(callback_id, "✏️ جوابت رو بنویس")
            send_message(
                user_id,
                f"✏️ **جوابت رو برای کاربر بنویس:**\n\n🆔 `{sup_id}`",
                cancel_keyboard()
            )
            return
        
        # ═══ پشتیبانی — رد کردن ═══
        if data.startswith("support_reject_"):
            sup_id = data.replace("support_reject_", "")
            if sup_id in db.get("support_messages", {}):
                target = db["support_messages"][sup_id]["user_id"]
                db["support_messages"].pop(sup_id)
                save_db(db)
                try:
                    send_message(int(target), "❌ **پیامت رد شد.**\n\n💡 اگه مشکل جدیه، دوباره با جزئیات بیشتر بفرست.")
                except:
                    pass
            answer_callback(callback_id, "❌ رد شد!", show_alert=True)
            try:
                msg_id = callback.get("message", {}).get("message_id")
                if msg_id:
                    delete_message(OWNER_ID, msg_id)
            except:
                pass
            return
        
        # ═══ چک عضویت ═══
        if data == "check_join":
            if check_joined(user_id):
                user = get_user(user_id)
                if not user.get("got_start_gift"):
                    add_coins(user_id, START_GIFT)
                    user["got_start_gift"] = True
                    
                    # چک دعوت
                    if user.get("invited_by") and user_id_str in db["invited_users"]:
                        inviter_id = user["invited_by"]
                        if user_id_str not in db.get("rewarded_users", []):
                            add_coins(inviter_id, INVITE_REWARD)
                            inviter = get_user(inviter_id)
                            inviter["invite_count"] = inviter.get("invite_count", 0) + 1
                            db.setdefault("rewarded_users", []).append(user_id_str)
                            save_db(db)
                            try:
                                send_message(
                                    int(inviter_id),
                                    f"🎉 **کاربر عضو کانال هم شد!**\n\n"
                                    f"👤 {callback['from'].get('first_name', 'کاربر')}\n"
                                    f"✅ با لینک دعوت تو اومد\n"
                                    f"✅ عضو کانال هم شد\n\n"
                                    f"🎁 **{INVITE_REWARD} سکه بهت اهدا شد!** 💰\n"
                                    f"💰 موجودی: {get_coins(inviter_id):,} سکه"
                                )
                            except:
                                pass
                    
                    save_db(db)
                    answer_callback(callback_id, f"✅ عضو شدی! 🎁 {START_GIFT} سکه هدیه گرفتی!")
                    send_message(
                        user_id,
                        f"✅ **عضو شدی!** 🎉\n\n"
                        f"🎁 **{START_GIFT} سکه هدیه** بهت اضافه شد!\n"
                        f"💰 موجودی: {get_coins(user_id):,} سکه\n\n"
                        f"حالا می‌تونی از ربات استفاده کنی!",
                        main_keyboard()
                    )
                else:
                    answer_callback(callback_id, "✅ عضو شدی!")
                    send_message(user_id, "✅ **عضو شدی!** 🎉\nحالا می‌تونی از ربات استفاده کنی!", main_keyboard())
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی! لطفاً اول عضو کانال شو.", show_alert=True)
            return
        
        # ═══ بازگشت ═══
        if data == "back_to_main":
            send_message(user_id, "🏠 منوی اصلی:", main_keyboard())
            answer_callback(callback_id)
            return
        
        # ═══ کپی آیدی ═══
        if data == "copy_id":
            answer_callback(callback_id, f"✅ آیدی عددی: {user_id}", show_alert=True)
            return
# ═══ پایان بخش ۱۵ ═══
        # ============================================
        # 🎁 سکه پاکت
        # ============================================
        if data.startswith("packet_"):
            pid = data.replace("packet_", "")
            if pid not in db.get("coin_packets", {}):
                answer_callback(callback_id, "❌ پاکت وجود نداره!", show_alert=True)
                return
            p = db["coin_packets"][pid]
            if user_id_str in p["used_by"]:
                answer_callback(callback_id, "⚠️ قبلاً باز کردی!", show_alert=True)
                return
            if len(p["used_by"]) >= p["capacity"]:
                answer_callback(callback_id, "😢 **دیر رسیدی!**\n\nامیدوارم سکه پاکت بعدی مال تو باشه! 🥲", show_alert=True)
                return
            p["used_by"].append(user_id_str)
            add_coins(user_id, p["coins"])
            save_db(db)
            answer_callback(
                callback_id,
                f"🎉 **سکه پاکت باز شد!**\n\n🪙 تعداد سکه هدیه: {p['coins']}\n💰 موجودی: {get_coins(user_id):,}",
                show_alert=True
            )
            return
        
        # ============================================
        # 👁️ سین‌زن — دیدم
        # ============================================
        if data.startswith("seen_"):
            order_id = data.replace("seen_", "")
            if order_id not in db["orders"]:
                answer_callback(callback_id, "❌ این سفارش وجود نداره!")
                return
            order = db["orders"][order_id]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!")
                return
            if user_id_str in db["seen_records"].get(order_id, []):
                answer_callback(callback_id, "⚠️ قبلاً دیدم رو زدی!")
                return
            db["seen_records"][order_id].append(user_id_str)
            order["seen_count"] += 1
            add_coins(user_id, SEEN_REWARD)
            new_seen = order["seen_count"]
            count = order["count"]
            order_number = order.get("order_number", "?")
            answer_callback(callback_id, f"👁️ ثبت شد! (+{SEEN_REWARD} سکه) | 💰 موجودی: {get_coins(user_id):,} سکه")
            if order.get("reply_message_id"):
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "👁️ دیدم", "callback_data": f"seen_{order_id}"},
                            {"text": "🤖 مشاهده ربات", "url": BOT_LINK}
                        ],
                        [{"text": "🚨 گزارش", "callback_data": f"report_{order_id}"}]
                    ]
                }
                try:
                    edit_message_text(
                        CHANNEL_ID,
                        order["reply_message_id"],
                        f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: {new_seen}\n#{order_number}",
                        keyboard
                    )
                except:
                    pass
            if new_seen >= count:
                order["status"] = "completed"
                db["stats"]["completed_orders"] += 1
                get_user(order["user_id"])["completed_orders"] += 1
                try:
                    delete_message(CHANNEL_ID, order["message_id"])
                    db["stats"]["deleted_messages"] += 1
                except:
                    pass
                try:
                    if order.get("reply_message_id"):
                        delete_message(CHANNEL_ID, order["reply_message_id"])
                except:
                    pass
                try:
                    send_message(
                        int(order["user_id"]),
                        f"🎉 **تبریک داداش!**\n\n"
                        f"🔢 {count} سین درخواستی تو کامل خورد!\n"
                        f"📩 پیام از کانال حذف شد.\n\n"
                        f"💡 **حالا می‌تونی:**\n"
                        f"• 🪙 بری کسب سکه کنی\n"
                        f"• 👁️ سفارش جدید ثبت کنی\n"
                        f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                        main_keyboard()
                    )
                except:
                    pass
            save_db(db)
            return
        
        # ============================================
        # 🚨 گزارش سین
        # ============================================
        if data.startswith("report_"):
            order_id = data.replace("report_", "")
            if order_id not in db["orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True)
                return
            order = db["orders"][order_id]
            reporter_username = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 گزارش ثبت شد!", show_alert=True)
            try:
                send_message(
                    int(OWNER_ID),
                    f"🚨 **گزارش سین**\n\n"
                    f"👤 گزارش‌دهنده: @{reporter_username}\n"
                    f"📝 سفارش: #{order.get('order_number', '?')}\n"
                    f"🔢 سین درخواستی: {order['count']}\n"
                    f"👁️ سین خورده: {order['seen_count']}\n\n"
                    f"⚠️ بررسی کن!"
                )
            except:
                pass
            return
# ═══ پایان بخش ۱۶ ═══
        # ============================================
        # 👥 عضوگیر — اطلاعات پاداش
        # ============================================
        if data.startswith("info_"):
            mid = data.replace("info_", "")
            o = db["member_orders"].get(mid, {})
            reward = o.get("reward", 3)
            otype = o.get("order_type", "normal")
            if otype == "guaranteed":
                answer_callback(
                    callback_id,
                    f"🪙 {reward} سکه میگیری!\n⚠️ باید ۴۸ ساعت بمونی!\n❌ ترک زودهنگام = -۷ سکه",
                    show_alert=True
                )
            else:
                answer_callback(callback_id, f"🪙 {reward} سکه میگیری!\n⏰ حداقل ۲ دقیقه بمون!", show_alert=True)
            return
        
        # ============================================
        # 👥 عضوگیر — عضو شدم
        # ============================================
        if data.startswith("mjoin_"):
            mid = data.replace("mjoin_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True)
                return
            order = db["member_orders"][mid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!", show_alert=True)
                return
            if user_id_str in db["member_records"].get(mid, []):
                answer_callback(callback_id, "⚠️ قبلاً عضو شدی!", show_alert=True)
                return
            
            # ضد تقلب: سفارش‌دهنده خودش نباشه
            if is_order_owner(user_id_str, mid):
                answer_callback(callback_id, "❌ نمیتونی توی سفارش خودت عضو بشی!", show_alert=True)
                return
            
            target_chat_id = order["chat_id"]
            member_status = get_chat_member(target_chat_id, user_id)
            if member_status.get("ok") and member_status["result"]["status"] in ["member", "administrator", "creator"]:
                db["member_records"][mid].append(user_id_str)
                order["seen_count"] += 1
                reward = order.get("reward", 3)
                add_coins(user_id, reward)
                otype = order.get("order_type", "normal")
                type_name = "معمولی" if otype == "normal" else "تضمینی"
                warning_text = "\n⚠️ باید ۴۸ ساعت بمونی!" if otype == "guaranteed" else "\n⏰ حداقل ۲ دقیقه بمون!"
                
                # ذخیره زمان عضویت برای هر دو نوع
                db["guaranteed_members"][f"{user_id_str}_{mid}"] = str(datetime.now())
                save_db(db)
                
                new_seen = order["seen_count"]
                count = order["count"]
                mnum = order.get("order_number", "?")
                answer_callback(
                    callback_id,
                    f"✅ عضو شدی! 🎉 +{reward} سکه | 💰 موجودی: {get_coins(user_id):,} سکه",
                    show_alert=True
                )
                
                if order.get("message_id"):
                    keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": f"🪙 {reward} سکه میگیری!", "callback_data": f"info_{mid}"}
                            ],
                            [
                                {"text": "🔗 عضویت در کانال", "url": order["link"]},
                                {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}
                            ],
                            [
                                {"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"},
                                {"text": "🤖 مشاهده ربات", "url": BOT_LINK}
                            ]
                        ]
                    }
                    try:
                        edit_message_text(
                            CHANNEL_ID,
                            order["message_id"],
                            f"📋 **سفارش عضو - {type_name}**\n\n"
                            f"🔗 لینک کانال: {order['link']}\n"
                            f"👥 تعداد درخواستی: {count}\n"
                            f"✅ تعداد عضو شده: {new_seen}\n"
                            f"#{mnum}\n\n"
                            f"🪙 **{reward} سکه میگیری!**{warning_text}",
                            keyboard
                        )
                    except:
                        pass
                
                if new_seen >= count:
                    order["status"] = "completed"
                    db["stats"]["completed_members"] = db["stats"].get("completed_members", 0) + 1
                    try:
                        delete_message(CHANNEL_ID, order["message_id"])
                        db["stats"]["deleted_messages"] += 1
                    except:
                        pass
                    try:
                        send_message(
                            int(order["user_id"]),
                            f"🎉 **تبریک داداش!**\n\n"
                            f"👥 {count} عضو درخواستی تو کامل شد!\n"
                            f"📩 پیام از کانال حذف شد.\n\n"
                            f"💡 **حالا می‌تونی:**\n"
                            f"• 🪙 بری کسب سکه کنی\n"
                            f"• 👥 سفارش عضو جدید ثبت کنی\n"
                            f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                            main_keyboard()
                        )
                    except:
                        pass
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی! اول عضو شو تا سکه بگیری.", show_alert=True)
            save_db(db)
            return
        
        # ============================================
        # 🚨 گزارش عضو
        # ============================================
        if data.startswith("mreport_"):
            mid = data.replace("mreport_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True)
                return
            order = db["member_orders"][mid]
            reporter_username = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 گزارش ثبت شد!", show_alert=True)
            try:
                send_message(
                    int(OWNER_ID),
                    f"🚨 **گزارش عضو**\n\n"
                    f"👤 گزارش‌دهنده: @{reporter_username}\n"
                    f"📝 سفارش: #{order.get('order_number', '?')}\n"
                    f"🔗 لینک: {order['link']}\n"
                    f"👥 درخواستی: {order['count']}\n"
                    f"✅ عضو شده: {order['seen_count']}\n\n"
                    f"⚠️ بررسی کن!"
                )
            except:
                pass
            return
    
    except Exception as e:
        print(f"⚠️ خطا در handle_callback: {e}")
        traceback.print_exc()
        gc.collect()
        time.sleep(0.001)

# ═══ پایان بخش ۱۷ ═══
# ============================================
# 🚀 حلقه اصلی (فوق سریع) با چک ترک کاربر
# ============================================
last_update_id = 0

def main():
    global last_update_id, INVITE_REWARD
    INVITE_REWARD = db.get("invite_reward", INVITE_REWARD)
    
    print("⚡ هایپرسین | سین‌زن + عضوگیر")
    print(f"🤖 @{BOT_USERNAME} | 📢 {CHANNEL_LINK}")
    print(f"👁️ دیدم: {SEEN_REWARD} | 📝 سین: {SIN_COST} | 👥 عضو: {MEMBER_COST}")
    print(f"📁 دیتابیس: {DB_FILE}")
    print(f"🛡️ ۶ محافظ فعال | ⚡ فوق سریع | 🥇 تضمینی | 🎁 سکه پاکت")
    print(f"♾️ همیشه روشن")
    print("-" * 40)
    
    while True:
        try:
            server_guard.protect()
            updates = api_call("getUpdates", {"offset": last_update_id + 1, "timeout": 5})
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    
                    msg = update.get("message", {})
                    
                    # ═══ چک ترک کاربر (هم معمولی هم تضمینی) ═══
                    if msg and "left_chat_member" in msg:
                        left_user_id = str(msg["left_chat_member"]["id"])
                        left_chat_id = str(msg["chat"]["id"])
                        
                        for mid, order in list(db["member_orders"].items()):
                            if str(order.get("chat_id")) != left_chat_id:
                                continue
                            
                            otype = order.get("order_type", "normal")
                            key = f"{left_user_id}_{mid}"
                            
                            # فقط ۱ بار جریمه
                            if key in db["punished_users"]:
                                continue
                            if left_user_id not in db["member_records"].get(mid, []):
                                continue
                            
                            join_time_str = db["guaranteed_members"].get(key)
                            
                            # ═══ تضمینی: ۴۸ ساعت ═══
                            if otype == "guaranteed":
                                if join_time_str and not is_48h_passed(join_time_str):
                                    if remove_coins(left_user_id, 7):
                                        add_coins(order["user_id"], 5)
                                        mark_punished(left_user_id, mid)
                                        try:
                                            send_message(
                                                int(left_user_id),
                                                f"⚠️ **شما کانال رو قبل از ۴۸ ساعت ترک کردید!**\n\n"
                                                f"📢 کانال: {order['link']}\n"
                                                f"📋 نوع سفارش: **تضمینی**\n"
                                                f"⏰ باید ۴۸ ساعت عضو می‌ماندید!\n\n"
                                                f"💰 **۷ سکه از موجودی شما کم شد.**\n"
                                                f"💳 موجودی: {get_coins(left_user_id):,} سکه"
                                            )
                                        except:
                                            pass
                                        try:
                                            send_message(
                                                int(order["user_id"]),
                                                f"🔔 **یه کاربر کانال رو قبل از ۴۸ ساعت ترک کرد!**\n\n"
                                                f"📢 کانال: {order['link']}\n"
                                                f"📋 نوع سفارش: **تضمینی**\n\n"
                                                f"💰 **۵ سکه به موجودی شما برگشت داده شد.**\n"
                                                f"💳 موجودی: {get_coins(order['user_id']):,} سکه"
                                            )
                                        except:
                                            pass
                            
                            # ═══ معمولی: ۲ دقیقه ═══
                            elif otype == "normal":
                                if join_time_str and not is_2min_passed(join_time_str):
                                    if remove_coins(left_user_id, 3):
                                        add_coins(order["user_id"], 2)
                                        mark_punished(left_user_id, mid)
                                        try:
                                            send_message(
                                                int(left_user_id),
                                                f"⚠️ **ترک سفارش معمولی!**\n\n"
                                                f"🚫 زودتر از ۲ دقیقه ترک کردی!\n\n"
                                                f"💰 **۳ سکه از موجودیت کم شد.**"
                                            )
                                        except:
                                            pass
                                        try:
                                            send_message(
                                                int(order["user_id"]),
                                                f"🔔 **یه کاربر قبل ۲ دقیقه کانال رو ترک کرد!**\n\n"
                                                f"📋 نوع: معمولی\n\n"
                                                f"💰 **۲ سکه به موجودی شما برگشت داده شد.**"
                                            )
                                        except:
                                            pass
                    
                    # ═══ پردازش پیام ═══
                    if "message" in update and "left_chat_member" not in msg:
                        handle_message(msg)
                    elif "callback_query" in update:
                        handle_callback(update["callback_query"])
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n👋 ربات خاموش شد!")
            break
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            print("🔄 ادامه می‌دم...")
            time.sleep(1)
            continue

# ═══ پایان بخش ۱۸ ═══
# ============================================
# 🌐 Flask Server
# ============================================
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Hypersin Bale Bot!"

@app.route('/ping')
def ping():
    return "pong ✅"

@app.route('/health')
def health():
    return jsonify({
        "status": "online",
        "users": len(db.get("users", {})),
        "orders": len(db.get("orders", {}))
    })

@app.route('/stats')
def stats():
    return jsonify(db.get("stats", {}))

# ═══ پایان بخش ۱۹ ═══
# ============================================
# 🚀 اجرا
# ============================================
if __name__ == "__main__":
    # 💓 Ping Worker
    threading.Thread(target=ping_worker, daemon=True).start()
    
    # 🚀 حلقه اصلی ربات
    threading.Thread(target=main, daemon=True).start()
    
    # 🌐 Flask Server
    app.run(host="0.0.0.0", port=10000)

# ═══ پایان کد ═══