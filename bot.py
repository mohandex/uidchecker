import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
import re

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# متغیرهای محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
VIP_GROUP_LINK = os.getenv('VIP_GROUP_LINK', 'https://t.me/your_vip_group')

class TradeBNBot:
    def __init__(self):
        self.init_database()
        
    def init_database(self):
        """ایجاد دیتابیس و جداول"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                uid TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول تنظیمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # درج لینک پیش‌فرض گروه VIP
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('vip_group_link', ?)
        ''', (VIP_GROUP_LINK,))
        
        conn.commit()
        conn.close()
    
    def get_vip_link(self):
        """دریافت لینک گروه VIP از دیتابیس"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = "vip_group_link"')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else VIP_GROUP_LINK
    
    def update_vip_link(self, new_link):
        """به‌روزرسانی لینک گروه VIP"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE settings SET value = ? WHERE key = "vip_group_link"', (new_link,))
        conn.commit()
        conn.close()
    
    def save_user_uid(self, user_id, username, uid):
        """ذخیره UID کاربر"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, uid, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, username, uid))
        conn.commit()
        conn.close()
    
    def get_user_by_id(self, user_id):
        """دریافت اطلاعات کاربر"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def approve_user(self, user_id):
        """تایید کاربر"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = "approved" WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def reject_user(self, user_id):
        """رد کاربر"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = "rejected" WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

# ایجاد نمونه از کلاس بات
bot_instance = TradeBNBot()

# Glass-style button helper
def create_glass_keyboard(buttons):
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for text, callback_data in row:
            keyboard_row.append(InlineKeyboardButton(f"🔹 {text} 🔹", callback_data=callback_data))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام خوش‌آمدگویی"""
    # دکمه‌های inline
    keyboard = [
        [InlineKeyboardButton("🔹 ثبت UID", callback_data='register_uid')],
        [InlineKeyboardButton("📞 پشتیبانی", url='https://t.me/CHECKUIDOURBIT')]
    ]
    
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ مدیریت بات", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # دکمه‌های پایین (Reply Keyboard)
    reply_keyboard = [
        ["🆔 ثبت UID", "📊 وضعیت من"],
        ["📞 پشتیبانی", "ℹ️ راهنما"]
    ]
    
    if update.effective_user.id == ADMIN_ID:
        reply_keyboard.append(["⚙️ پنل مدیریت"])
    
    keyboard_markup = ReplyKeyboardMarkup(
        reply_keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    welcome_text = (
        "🌟 به بات کانال TradeBN خوش آمدید! 🌟\n\n"
        "💎 جهت ثبت UID لطفاً UID مورد نظر خود را ارسال کنید\n\n"
        "🔸 از دکمه‌های زیر یا منوی پایین استفاده کنید:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard_markup,
        parse_mode='HTML'
    )
    
    # ارسال دکمه‌های inline به صورت جداگانه
    await update.message.reply_text(
        "🔹 گزینه‌های سریع:",
        reply_markup=reply_markup
    )

# Message handler for UID
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text
    
    # Handle reply keyboard buttons
    if message_text == "🆔 ثبت UID":
        await update.message.reply_text(
            "🆔 لطفاً UID خود را ارسال کنید:\n\n"
            "⚠️ فقط اعداد مجاز هستند\n"
            "مثال: 123456789"
        )
        return
    
    elif message_text == "📊 وضعیت من":
        user_data = bot_instance.get_user_by_id(user.id)
        if user_data:
            status_text = (
                f"📊 وضعیت شما:\n\n"
                f"🆔 UID: {user_data[2]}\n"
                f"📈 وضعیت: {user_data[3]}\n"
                f"📅 تاریخ ثبت: {user_data[4]}"
            )
        else:
            status_text = "❌ شما هنوز UID ثبت نکرده‌اید!"
        await update.message.reply_text(status_text)
        return
    
    elif message_text == "📞 پشتیبانی":
        support_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 تماس با پشتیبانی", url='https://t.me/CHECKUIDOURBIT')]
        ])
        await update.message.reply_text(
            "📞 برای تماس با پشتیبانی از دکمه زیر استفاده کنید:",
            reply_markup=support_keyboard
        )
        return
    
    elif message_text == "ℹ️ راهنما":
        help_text = (
            "ℹ️ راهنمای استفاده از بات:\n\n"
            "1️⃣ ابتدا UID خود را ثبت کنید\n"
            "2️⃣ منتظر تایید ادمین باشید\n"
            "3️⃣ پس از تایید، لینک گروه VIP دریافت کنید\n\n"
            "💡 نکات مهم:\n"
            "• UID باید فقط شامل اعداد باشد\n"
            "• هر کاربر فقط یک بار می‌تواند UID ثبت کند\n"
            "• در صورت رد شدن، می‌توانید مجدداً تلاش کنید"
        )
        await update.message.reply_text(help_text)
        return
    
    elif message_text == "⚙️ پنل مدیریت" and user.id == ADMIN_ID:
        await admin_panel(update, context)
        return
    
    # Check if user is admin and message starts with /admin
    if user.id == ADMIN_ID and message_text.startswith('/admin'):
        await admin_panel(update, context)
        return
    
    # Handle admin link change
    if user.id == ADMIN_ID and context.user_data.get('waiting_for_link'):
        await handle_admin_link_change(update, context)
        return
    
    # Check if message is a valid UID (only numbers)
    if message_text.isdigit():
        # Save user and UID to database
        bot_instance.save_user_uid(user.id, user.username, message_text)
        
        # Send confirmation to user
        confirmation_text = (
            "✅ UID شما دریافت شد!\n\n"
            f"🆔 UID: {message_text}\n\n"
            "⏳ در صورت تایید، لینک گروه VIP خودکار ارسال خواهد شد\n\n"
            "🔄 درحال ارسال به ادمین برای تایید..."
        )
        await update.message.reply_text(confirmation_text)
        
        # Send to admin for approval
        admin_keyboard = create_glass_keyboard([
            [("تایید ✅", f"approve_{user.id}"), ("رد ❌", f"reject_{user.id}")]
        ])
        
        admin_text = (
            "🔔 درخواست جدید ثبت UID\n\n"
            f"👤 کاربر: @{user.username or 'بدون نام کاربری'}\n"
            f"🆔 User ID: {user.id}\n"
            f"🔢 UID: {message_text}\n\n"
            "لطفاً تصمیم خود را اعلام کنید:"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=admin_keyboard
        )
    else:
        error_text = (
            "❌ UID نامعتبر!\n\n"
            "⚠️ لطفاً فقط اعداد وارد کنید\n"
            "مثال: 123456789"
        )
        await update.message.reply_text(error_text)

# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ شما دسترسی ادمین ندارید!")
        return
    
    admin_keyboard = create_glass_keyboard([
        [("تغییر لینک گروه VIP 🔗", "change_vip_link")],
        [("مشاهده تنظیمات ⚙️", "view_settings")]
    ])
    
    admin_text = (
        "🔧 پنل مدیریت بات\n\n"
        "لطفاً گزینه مورد نظر را انتخاب کنید:"
    )
    
    await update.message.reply_text(admin_text, reply_markup=admin_keyboard)

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'register_uid':
        await query.edit_message_text(
            "🆔 لطفاً UID خود را ارسال کنید:\n\n"
            "⚠️ فقط اعداد مجاز هستند\n"
            "مثال: 123456789"
        )
    
    elif data.startswith('approve_'):
        user_id = int(data.split('_')[1])
        await approve_user(query, context, user_id)
    
    elif data.startswith('reject_'):
        user_id = int(data.split('_')[1])
        await reject_user(query, context, user_id)
    
    elif data == 'change_vip_link':
        await query.edit_message_text(
            "🔗 لینک جدید گروه VIP را ارسال کنید:\n\n"
            "مثال: https://t.me/your_new_vip_group"
        )
        context.user_data['waiting_for_link'] = True
    
    elif data == 'admin_panel':
        admin_keyboard = create_glass_keyboard([
            [("تغییر لینک گروه VIP 🔗", "change_vip_link")],
            [("مشاهده تنظیمات ⚙️", "view_settings")]
        ])
        
        admin_text = (
            "🔧 پنل مدیریت بات\n\n"
            "لطفاً گزینه مورد نظر را انتخاب کنید:"
        )
        
        await query.edit_message_text(admin_text, reply_markup=admin_keyboard)
    
    elif data == 'view_settings':
        vip_link = bot_instance.get_vip_link()
        settings_text = (
            "⚙️ تنظیمات فعلی:\n\n"
            f"🔗 لینک گروه VIP: {vip_link}"
        )
        await query.edit_message_text(settings_text)

# Approve user
async def approve_user(query, context, user_id):
    bot_instance.approve_user(user_id)
    vip_link = bot_instance.get_vip_link()
    
    # Send VIP link to user
    user_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 ورود به گروه VIP 💎 🔹", url=vip_link)]
    ])
    
    user_text = (
        "🎉 تبریک! UID شما تایید شد\n\n"
        "💎 اکنون می‌توانید به گروه VIP دسترسی داشته باشید:\n\n"
        "👇 روی دکمه زیر کلیک کنید:"
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=user_text,
        reply_markup=user_keyboard
    )
    
    # Update admin message
    await query.edit_message_text(
        f"✅ کاربر {user_id} تایید شد و لینک VIP ارسال گردید"
    )

# Reject user
async def reject_user(query, context, user_id):
    bot_instance.reject_user(user_id)
    
    # Send rejection message to user
    rejection_text = (
        "❌ متأسفانه UID شما تایید نشد\n\n"
        "🔄 می‌توانید مجدداً UID صحیح خود را ارسال کنید"
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=rejection_text
    )
    
    # Update admin message
    await query.edit_message_text(
        f"❌ کاربر {user_id} رد شد"
    )

# Handle admin link change
async def handle_admin_link_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_link = update.message.text
    if new_link.startswith('https://t.me/'):
        bot_instance.update_vip_link(new_link)
        await update.message.reply_text(
            f"✅ لینک گروه VIP با موفقیت تغییر یافت:\n\n{new_link}"
        )
    else:
        await update.message.reply_text(
            "❌ لینک نامعتبر! لطفاً لینک معتبر تلگرام ارسال کنید\n"
            "مثال: https://t.me/your_group"
        )
    context.user_data['waiting_for_link'] = False

def main():
    # Initialize database
    bot_instance.init_database()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot
    print("🤖 Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()