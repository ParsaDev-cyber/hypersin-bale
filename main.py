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