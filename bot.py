import telebot
from telebot import types
import sqlite3

# ==========================================
# 1. الإعدادات
# ==========================================
BOT_TOKEN = '8537777670:AAF0A1gilcAsAq_TCYYBnBKzBaHzQdPacvw'
SUPPORT_BOT_TOKEN = '8840219324:AAGIgevAOdWjVstTfi6ks_-fh3_55xtW6-Q'
ADMIN_ID = 8787133610

# ضع يوزر بوت الدعم هنا (بدون @)
SUPPORT_BOT_USERNAME = 'YourSupportBotUsername' 

USDT_ADDRESS = "0x9d9af619335070d4c8173951c2641139fac74cedcfecd52efa57506936c11b52"
TON_ADDRESS = "UQCGb128MHndk9ZH6d6qsAe3Wo05gub7C-hb55jW0ANRKtP9"

bot = telebot.TeleBot(BOT_TOKEN)
support_bot = telebot.TeleBot(SUPPORT_BOT_TOKEN)

# ==========================================
# 2. قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('shadow_vip.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, pay_type TEXT, content TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO products (name, price, pay_type, content) VALUES ('100 نجمة (USDT)', 1.5, 'usdt', '')")
        c.execute("INSERT INTO products (name, price, pay_type, content) VALUES ('100 نجمة (TON)', 1.1, 'ton', '')")
        c.execute("INSERT INTO products (name, price, pay_type, content) VALUES ('VPN (15 نجمة)', 15.0, 'stars', '')")
        c.execute("INSERT INTO products (name, price, pay_type, content) VALUES ('25 نجمة (30 نقطة)', 30.0, 'points', '')")
    conn.commit()
    conn.close()
init_db()

# ==========================================
# 3. واجهة المتجر (للزوار)
# ==========================================
def user_menu(message, user_id):
    conn = sqlite3.connect('shadow_vip.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    conn.close()

    text = f"""
💎 **SHADOW VIP STORE** 💎
➖➖➖➖➖➖➖➖➖➖
👤 **المستخدم:** {message.from_user.first_name}
💰 **رصيدك:** {balance} نقطة
➖➖➖➖➖➖➖➖➖➖
⚡ اختر الخدمة من الأسفل:
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    conn = sqlite3.connect('shadow_vip.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM products")
    products = c.fetchall()
    conn.close()

    buttons = []
    for p in products:
        buttons.append(types.InlineKeyboardButton(p[1], callback_data=f"buy_{p[0]}"))
    
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i+1])
        else:
            markup.row(buttons[i])
            
    # إضافة زر بوت الدعم
    markup.row(types.InlineKeyboardButton("💬 الدعم الفني", url=f"https://t.me/{SUPPORT_BOT_USERNAME}"))
    markup.row(types.InlineKeyboardButton("👥 دعوة صديق (+2)", callback_data='referral'))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ==========================================
# 4. لوحة تحكم المالك
# ==========================================
def admin_panel(message):
    text = "👑 **لوحة تحكم SHADOW**\n\nمن هنا تتحكم في متجرك بالكامل:"
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_add = types.InlineKeyboardButton("➕ إضافة منتج جديد", callback_data='admin_add')
    btn_list = types.InlineKeyboardButton("📋 عرض المنتجات", callback_data='admin_list')
    markup.add(btn_add, btn_list)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# ==========================================
# 5. أوامر البدء
# ==========================================
@bot.message_handler(commands=['start', 'admin'])
def start(message):
    user_id = message.from_user.id
    
    # إذا كان المالك
    if user_id == ADMIN_ID:
        admin_panel(message)
        return

    # إذا كان زائراً عادياً
    conn = sqlite3.connect('shadow_vip.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    
    # نظام الإحالات
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        referrer_id = int(args[1].split('_')[1])
        if referrer_id != user_id:
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            if c.fetchone()[0] == 0: 
                c.execute("UPDATE users SET balance = balance + 2 WHERE user_id=?", (referrer_id,))
                c.execute("UPDATE users SET balance = balance + 2 WHERE user_id=?", (user_id,))
                bot.send_message(referrer_id, "🎉 مبروك! انضم شخص من خلال رابطك، حصلت على 2 نقطة.")
    conn.commit()
    conn.close()
    
    user_menu(message, user_id)

# ==========================================
# 6. الأزرار
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    # لوحة المالك
    if call.data == 'admin_add' and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "أرسل اسم المنتج:")
        bot.register_next_step_handler(msg, process_add_name)
    
    elif call.data == 'admin_list' and user_id == ADMIN_ID:
        conn = sqlite3.connect('shadow_vip.db')
        c = conn.cursor()
        c.execute("SELECT id, name, price, pay_type FROM products")
        prods = c.fetchall()
        conn.close()
        text = "📋 **المنتجات الحالية:**\n\n"
        for p in prods:
            text += f"ID: {p[0]} | {p[1]} | {p[2]} ({p[3]})\n"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

    # الشراء والإحالة
    elif call.data.startswith('buy_') or call.data == 'referral':
        
        if call.data == 'referral':
            ref_link = f"https://t.me/{bot.get_me().username}?start=ref_{user_id}"
            bot.send_message(call.message.chat.id, f"👥 **دعوة صديق**\n\nشارك الرابط:\n\n`{ref_link}`", parse_mode='Markdown')
            return

        product_id = call.data.split('_')[1]
        conn = sqlite3.connect('shadow_vip.db')
        c = conn.cursor()
        c.execute("SELECT name, price, pay_type, content FROM products WHERE id=?", (product_id,))
        product = c.fetchone()
        conn.close()

        name, price, pay_type, content = product

        if pay_type in ['usdt', 'ton']:
            address = USDT_ADDRESS if pay_type == 'usdt' else TON_ADDRESS
            text = f"💎 **{name}**\n\nقم بالتحويل إلى:\n`{address}`\n\nثم أرسل الصورة للدعم:\n@{SUPPORT_BOT_USERNAME}"
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
            bot.send_message(ADMIN_ID, f"🔔 {user_id} يطلب {name}.")

        elif pay_type == 'stars':
            if product_id == '3': # زر VPN
                text = f"⭐ **{name}**\n\nيرجى التواصل مع الدعم (@{SUPPORT_BOT_USERNAME}) لإتمام الدفع واستلام الرابط المباشر."
                bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
            else:
                text = f"⭐ **{name}**\n\nتواصل مع الدعم: @{SUPPORT_BOT_USERNAME}"
                bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

        elif pay_type == 'points':
            conn = sqlite3.connect('shadow_vip.db')
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            balance = c.fetchone()[0]
            if balance >= price:
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, user_id))
                conn.commit()
                bot.answer_callback_query(call.id, "✅ تم الشراء!", show_alert=True)
                bot.send_message(call.message.chat.id, f"🎁 {content}")
            else:
                bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
            conn.close()

# ==========================================
# 7. دوال إضافة المنتجات (للمالك)
# ==========================================
def process_add_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id, "أرسل السعر (أرقام فقط):")
    bot.register_next_step_handler(msg, process_add_price, name)

def process_add_price(message, name):
    try:
        price = float(message.text)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("نجوم ⭐", callback_data=f"type_stars_{name}_{price}"))
        markup.add(types.InlineKeyboardButton("نقاط 💰", callback_data=f"type_points_{name}_{price}"))
        markup.add(types.InlineKeyboardButton("USDT 💎", callback_data=f"type_usdt_{name}_{price}"))
        bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "خطأ في السعر.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_') and call.from_user.id == ADMIN_ID)
def save_product(call):
    _, pay_type, name, price = call.data.split('_')
    content = USDT_ADDRESS if pay_type == 'usdt' else (TON_ADDRESS if pay_type == 'ton' else "")
    conn = sqlite3.connect('shadow_vip.db')
    c = conn.cursor()
    c.execute("INSERT INTO products (name, price, pay_type, content) VALUES (?, ?, ?, ?)", (name, float(price), pay_type, content))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم إضافة المنتج!")
    admin_panel(call.message)

# ==========================================
# 8. بوت الدعم
# ==========================================
@support_bot.message_handler(commands=['start'])
def support_start(message):
    text = """
👋 **مرحباً بك في الدعم الفني لمتجر SHADOW**

يرجى إرسال صورة التحويل (Screenshot) هنا، وسوف يتم الرد عليك في أقرب وقت ممكن.
"""
    support_bot.send_message(message.chat.id, text, parse_mode='Markdown')

@support_bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    support_bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    support_bot.send_message(message.chat.id, "✅ **تم استلام الصورة بنجاح.**\nسيتم مراجعة طلبك والرد عليك قريباً.")
    support_bot.send_message(ADMIN_ID, f"📩 وصلت صورة تحويل جديدة من: {message.from_user.id}")

# ==========================================
# 9. التشغيل
# ==========================================
print("[*] Shadow VIP Bot is running...")
bot.infinity_polling()
