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
        
        # جدول ادمین‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY,
                username TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # درج لینک پیش‌فرض گروه VIP
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('vip_group_link', ?)
        ''', (VIP_GROUP_LINK,))
        
        # درج ادمین اصلی
        cursor.execute('''
            INSERT OR IGNORE INTO admins (admin_id, username) 
            VALUES (?, 'main_admin')
        ''', (ADMIN_ID,))
        
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
    
    def is_admin(self, user_id):
        """بررسی ادمین بودن کاربر"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def add_admin(self, admin_id, username):
        """اضافه کردن ادمین جدید"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO admins (admin_id, username)
            VALUES (?, ?)
        ''', (admin_id, username))
        conn.commit()
        conn.close()
    
    def remove_admin(self, admin_id):
        """حذف ادمین (به جز ادمین اصلی)"""
        if admin_id == ADMIN_ID:
            return False  # نمی‌توان ادمین اصلی را حذف کرد
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE admin_id = ?', (admin_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_all_admins(self):
        """دریافت لیست تمام ادمین‌ها"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins ORDER BY added_at')
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_user_stats(self):
        """دریافت آمار کاربران"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # تعداد کل کاربران
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # تعداد کاربران تایید شده
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "approved"')
        approved_users = cursor.fetchone()[0]
        
        # تعداد کاربران در انتظار
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "pending"')
        pending_users = cursor.fetchone()[0]
        
        # تعداد کاربران رد شده
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "rejected"')
        rejected_users = cursor.fetchone()[0]
        
        conn.close()
        return {
            'total': total_users,
            'approved': approved_users,
            'pending': pending_users,
            'rejected': rejected_users
        }
    
    def get_all_users(self, status=None):
        """دریافت لیست کاربران"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM users WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def delete_user(self, user_id):
        """حذف کاربر از دیتابیس"""
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def revoke_user_access(self, user_id):
        """لغو دسترسی کاربر (تغییر وضعیت به rejected)"""
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

async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی عضویت کاربر در کانال"""
    try:
        member = await context.bot.get_chat_member(chat_id="@trade_bn", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام خوش‌آمدگویی با بررسی عضویت اجباری"""
    user = update.effective_user
    
    # بررسی عضویت در کانال (به جز ادمین‌ها)
    if not bot_instance.is_admin(user.id):
        is_member = await check_channel_membership(user.id, context)
        if not is_member:
            # دکمه بررسی مجدد
            check_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بررسی مجدد", callback_data='check_membership')],
                [InlineKeyboardButton("📢 عضویت در کانال", url='https://t.me/trade_bn')]
            ])
            
            membership_text = (
                "⚠️ برای استفاده از ربات باید عضو کانال باشید!\n\n"
                "📢 لطفاً ابتدا در کانال @trade_bn عضو شوید\n\n"
                "✅ پس از عضویت، دکمه 'بررسی مجدد' را بزنید"
            )
            
            await update.message.reply_text(
                membership_text,
                reply_markup=check_keyboard
            )
            return
    
    # دکمه‌های inline
    keyboard = [
        [InlineKeyboardButton("💎 عضویت در VIP", callback_data='register_uid')],
        [InlineKeyboardButton("📞 پشتیبانی", url='https://t.me/CHECKUIDOURBIT')]
    ]
    
    if bot_instance.is_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton("⚙️ مدیریت بات", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # دکمه‌های پایین (Reply Keyboard)
    reply_keyboard = [
        ["💎 عضویت در VIP", "📊 وضعیت من"],
        ["📞 پشتیبانی", "ℹ️ راهنما"]
    ]
    
    if bot_instance.is_admin(update.effective_user.id):
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
    
    # بررسی عضویت در کانال (به جز ادمین‌ها)
    if not bot_instance.is_admin(user.id):
        is_member = await check_channel_membership(user.id, context)
        if not is_member:
            check_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بررسی مجدد", callback_data='check_membership')],
                [InlineKeyboardButton("📢 عضویت در کانال", url='https://t.me/trade_bn')]
            ])
            
            membership_text = (
                "⚠️ برای استفاده از ربات باید عضو کانال باشید!\n\n"
                "📢 لطفاً ابتدا در کانال @trade_bn عضو شوید\n\n"
                "✅ پس از عضویت، دکمه 'بررسی مجدد' را بزنید"
            )
            
            await update.message.reply_text(
                membership_text,
                reply_markup=check_keyboard
            )
            return
    
    # Handle reply keyboard buttons
    if message_text == "💎 عضویت در VIP":
        account_keyboard = create_glass_keyboard([
            [("بله ✅", "has_account"), ("خیر ❌", "no_account")]
        ])
        
        await update.message.reply_text(
            "برای ورود به VIP کانال Trade BN :\n\n"
            "- باید شرایط زیر را انجام بدهید\n\n"
            "➊ - یک حساب در صرافی اوربیت با کد رفرال TRADEBN بسازید\n\n"
            "➋ - و حسابتون رو هر چقدر دوست داشتین شارژ کنید!\n\n"
            "- یکی 50 دلار شارژ میکنه\n"
            "- یکی 1000 شارژ میکنه و حداقلش 50 دلار هست\n\n"
            "❗️اگر قبلا در این صرافی اکانت دارید و کد رفرال ما را وارد نکردید بایستی اکانت جدید با لینک زیر بسازید:\n\n"
            "https://www.ourbit.com/register?inviteCode=TradeBN\n\n"
            "❓ آیا در صرافی اوربیت اکانت دارید؟",
            reply_markup=account_keyboard,
            parse_mode='Markdown',
            disable_web_page_preview=True
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
            "📋 شرایط شرکت در VIP:\n\n"
            "🔹 با لینک رفرال ما در صرافی ثبت نام بکنید و حسابتون رو هر چقدر دوست داشتین شارژ کنید!\n\n"
            "💰 مثال‌های شارژ:\n"
            "- یکی 50 دلار شارژ میکنه\n"
            "- یکی 1000 شارژ میکنه و حداقلش 50 دلار هست\n\n"
            "🔗 لینک ثبت‌نام⁉️👇🏻\n\n"
            "https://www.ourbit.com/register?inviteCode=TradeBN\n\n"
            "همین🫡 مخلص"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown', disable_web_page_preview=True)
        return
    
    elif message_text == "⚙️ پنل مدیریت" and bot_instance.is_admin(user.id):
        await admin_panel(update, context)
        return
    
    # Check if user is admin and message starts with /admin
    if bot_instance.is_admin(user.id) and message_text.startswith('/admin'):
        await admin_panel(update, context)
        return
    
    # Handle admin operations
    if bot_instance.is_admin(user.id):
        # Handle admin link change
        if context.user_data.get('waiting_for_link'):
            await handle_admin_link_change(update, context)
            return
        
        # Handle adding new admin
        elif context.user_data.get('waiting_for_admin_id'):
            await handle_add_admin(update, context)
            return
        
        # Handle removing admin
        elif context.user_data.get('waiting_for_remove_admin_id'):
            await handle_remove_admin(update, context)
            return
        
        # Handle deleting user
        elif context.user_data.get('waiting_for_delete_user_id'):
            await handle_delete_user(update, context)
            return
        
        # Handle revoking user access
        elif context.user_data.get('waiting_for_revoke_user_id'):
            await handle_revoke_access(update, context)
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
    if not bot_instance.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ شما دسترسی ادمین ندارید!")
        return
    
    admin_keyboard = create_glass_keyboard([
        [("آمار کاربران 📊", "user_stats"), ("مدیریت کاربران 👥", "manage_users")],
        [("مدیریت ادمین‌ها 👑", "manage_admins"), ("تنظیمات ⚙️", "bot_settings")],
        [("تغییر لینک VIP 🔗", "change_vip_link")]
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
    
    if data == 'check_membership':
        user = query.from_user
        is_member = await check_channel_membership(user.id, context)
        
        if is_member:
            # کاربر عضو شده، نمایش منوی اصلی
            keyboard = [
                [InlineKeyboardButton("💎 عضویت در VIP", callback_data='register_uid')],
                [InlineKeyboardButton("📞 پشتیبانی", url='https://t.me/CHECKUIDOURBIT')]
            ]
            
            if bot_instance.is_admin(user.id):
                keyboard.append([InlineKeyboardButton("⚙️ مدیریت بات", callback_data='admin_panel')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = (
                "✅ عضویت شما تایید شد!\n\n"
                "🌟 به بات کانال TradeBN خوش آمدید! 🌟\n\n"
                "💎 جهت ثبت UID لطفاً UID مورد نظر خود را ارسال کنید\n\n"
                "🔸 از دکمه‌های زیر استفاده کنید:"
            )
            
            await query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup
            )
        else:
            # کاربر هنوز عضو نشده
            await query.answer(
                "❌ شما هنوز عضو کانال نشده‌اید! لطفاً ابتدا عضو شوید.",
                show_alert=True
            )
    
    elif data == 'register_uid':
        account_keyboard = create_glass_keyboard([
            [("بله ✅", "has_account"), ("خیر ❌", "no_account")]
        ])
        
        await query.edit_message_text(
            "برای ورود به VIP کانال Trade BN :\n\n"
            "- باید شرایط زیر را انجام بدهید\n\n"
            "➊ - یک حساب در صرافی اوربیت با کد رفرال TRADEBN بسازید\n\n"
            "➋ - و حسابتون رو هر چقدر دوست داشتین شارژ کنید!\n\n"
            "- یکی 50 دلار شارژ میکنه\n"
            "- یکی 1000 شارژ میکنه و حداقلش 50 دلار هست\n\n"
            "❗️اگر قبلا در این صرافی اکانت دارید و کد رفرال ما را وارد نکردید بایستی اکانت جدید با لینک زیر بسازید:\n\n"
            "https://www.ourbit.com/register?inviteCode=TradeBN\n\n"
            "❓ آیا در صرافی اوربیت اکانت دارید؟",
            reply_markup=account_keyboard,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    elif data == 'has_account':
        # Send UID image with caption for users who already have an account
        with open('uid.jpg', 'rb') as photo:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo,
                caption="✅با کمک عکس بالا، شناسه کاربری (UID) خود را بردارید و ارسال کنید :"
            )
        await query.message.delete()
    
    elif data == 'no_account':
        # Send message with link to create account and continue membership button
        continue_keyboard = create_glass_keyboard([
            [("ادامه عضویت", "continue_membership")]
        ])
        
        await query.edit_message_text(
            "💎 با استفاده از لینک زیر یک اکانت در صرافی اوربیت بسازید و پس از آن روی دکمه «ادامه عضویت» بزنید.\n\n"
            "https://www.ourbit.com/register?inviteCode=TradeBN",
            reply_markup=continue_keyboard,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    elif data == 'continue_membership':
        # Send UID image with caption for continuing membership
        with open('uid.jpg', 'rb') as photo:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo,
                caption="✅با کمک عکس بالا، شناسه کاربری (UID) خود را بردارید و ارسال کنید :"
            )
        await query.message.delete()
    
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
            [("آمار کاربران 📊", "user_stats"), ("مدیریت کاربران 👥", "manage_users")],
            [("مدیریت ادمین‌ها 👑", "manage_admins"), ("تنظیمات ⚙️", "bot_settings")],
            [("تغییر لینک VIP 🔗", "change_vip_link")]
        ])
        
        admin_text = (
            "🔧 پنل مدیریت بات\n\n"
            "لطفاً گزینه مورد نظر را انتخاب کنید:"
        )
        
        await query.edit_message_text(admin_text, reply_markup=admin_keyboard)
    
    elif data == 'user_stats':
        stats = bot_instance.get_user_stats()
        stats_text = (
            "📊 آمار کاربران:\n\n"
            f"👥 کل کاربران: {stats['total']}\n"
            f"✅ تایید شده: {stats['approved']}\n"
            f"⏳ در انتظار: {stats['pending']}\n"
            f"❌ رد شده: {stats['rejected']}\n\n"
            "🔙 برای بازگشت از /admin استفاده کنید"
        )
        await query.edit_message_text(stats_text)
    
    elif data == 'manage_users':
        user_management_keyboard = create_glass_keyboard([
            [("کاربران تایید شده ✅", "list_approved"), ("کاربران در انتظار ⏳", "list_pending")],
            [("کاربران رد شده ❌", "list_rejected"), ("حذف کاربر 🗑️", "delete_user_prompt")],
            [("لغو دسترسی کاربر 🚫", "revoke_access_prompt"), ("🔙 بازگشت", "admin_panel")]
        ])
        
        await query.edit_message_text(
            "👥 مدیریت کاربران:\n\nگزینه مورد نظر را انتخاب کنید:",
            reply_markup=user_management_keyboard
        )
    
    elif data == 'manage_admins':
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ فقط ادمین اصلی می‌تواند ادمین‌ها را مدیریت کند!", show_alert=True)
            return
        
        admin_management_keyboard = create_glass_keyboard([
            [("لیست ادمین‌ها 👑", "list_admins"), ("اضافه کردن ادمین ➕", "add_admin_prompt")],
            [("حذف ادمین ➖", "remove_admin_prompt"), ("🔙 بازگشت", "admin_panel")]
        ])
        
        await query.edit_message_text(
            "👑 مدیریت ادمین‌ها:\n\nگزینه مورد نظر را انتخاب کنید:",
            reply_markup=admin_management_keyboard
        )
    
    elif data == 'bot_settings':
        vip_link = bot_instance.get_vip_link()
        settings_text = (
            "⚙️ تنظیمات بات:\n\n"
            f"🔗 لینک گروه VIP: {vip_link}\n\n"
            "🔙 برای بازگشت از /admin استفاده کنید"
        )
        await query.edit_message_text(settings_text)
    
    elif data.startswith('list_'):
        status_map = {
            'list_approved': 'approved',
            'list_pending': 'pending', 
            'list_rejected': 'rejected'
        }
        status = status_map.get(data)
        users = bot_instance.get_all_users(status)
        
        if not users:
            await query.edit_message_text(f"📝 هیچ کاربری با وضعیت '{status}' یافت نشد.")
            return
        
        user_list = f"📋 کاربران {status}:\n\n"
        for i, user in enumerate(users[:10], 1):  # نمایش 10 کاربر اول
            username = f"@{user[1]}" if user[1] else "بدون نام کاربری"
            user_list += f"{i}. {username} (ID: {user[0]})\nUID: {user[2]}\n\n"
        
        if len(users) > 10:
            user_list += f"... و {len(users) - 10} کاربر دیگر\n\n"
        
        user_list += "🔙 برای بازگشت از /admin استفاده کنید"
        await query.edit_message_text(user_list)
    
    elif data == 'list_admins':
        admins = bot_instance.get_all_admins()
        admin_list = "👑 لیست ادمین‌ها:\n\n"
        
        for i, admin in enumerate(admins, 1):
            username = admin[1] if admin[1] else "نامشخص"
            status = "(ادمین اصلی)" if admin[0] == ADMIN_ID else ""
            admin_list += f"{i}. {username} {status}\nID: {admin[0]}\n\n"
        
        admin_list += "🔙 برای بازگشت از /admin استفاده کنید"
        await query.edit_message_text(admin_list)
    
    elif data == 'add_admin_prompt':
        await query.edit_message_text(
            "➕ اضافه کردن ادمین جدید:\n\n"
            "لطفاً ID کاربری که می‌خواهید ادمین کنید را ارسال کنید:\n\n"
            "مثال: 123456789"
        )
        context.user_data['waiting_for_admin_id'] = True
    
    elif data == 'remove_admin_prompt':
        await query.edit_message_text(
            "➖ حذف ادمین:\n\n"
            "لطفاً ID ادمینی که می‌خواهید حذف کنید را ارسال کنید:\n\n"
            "⚠️ توجه: نمی‌توانید ادمین اصلی را حذف کنید"
        )
        context.user_data['waiting_for_remove_admin_id'] = True
    
    elif data == 'delete_user_prompt':
        await query.edit_message_text(
            "🗑️ حذف کاربر:\n\n"
            "لطفاً ID کاربری که می‌خواهید حذف کنید را ارسال کنید:\n\n"
            "⚠️ توجه: این عمل غیرقابل بازگشت است!"
        )
        context.user_data['waiting_for_delete_user_id'] = True
    
    elif data == 'revoke_access_prompt':
        await query.edit_message_text(
            "🚫 لغو دسترسی کاربر:\n\n"
            "لطفاً ID کاربری که می‌خواهید دسترسی‌اش را لغو کنید را ارسال کنید:\n\n"
            "این کار وضعیت کاربر را به 'رد شده' تغییر می‌دهد"
        )
        context.user_data['waiting_for_revoke_user_id'] = True

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
"🚫 حساب اوربیت شما حداقل موجودی لازم (۵۰ دلار) را ندارد. برای ادامه، لطفاً ابتدا والت خود را شارژ کرده و سپس UID را ارسال نمایید. ممنون از همکاری شما 🌐"
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

# Handle adding new admin
async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین اصلی می‌تواند ادمین جدید اضافه کند!")
        context.user_data['waiting_for_admin_id'] = False
        return
    
    admin_id_text = update.message.text
    if admin_id_text.isdigit():
        admin_id = int(admin_id_text)
        if bot_instance.is_admin(admin_id):
            await update.message.reply_text("⚠️ این کاربر قبلاً ادمین است!")
        else:
            bot_instance.add_admin(admin_id, "new_admin")
            await update.message.reply_text(
                f"✅ کاربر {admin_id} با موفقیت به عنوان ادمین اضافه شد!"
            )
    else:
        await update.message.reply_text(
            "❌ ID نامعتبر! لطفاً فقط اعداد وارد کنید\n"
            "مثال: 123456789"
        )
    context.user_data['waiting_for_admin_id'] = False

# Handle removing admin
async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین اصلی می‌تواند ادمین‌ها را حذف کند!")
        context.user_data['waiting_for_remove_admin_id'] = False
        return
    
    admin_id_text = update.message.text
    if admin_id_text.isdigit():
        admin_id = int(admin_id_text)
        if admin_id == ADMIN_ID:
            await update.message.reply_text("❌ نمی‌توانید ادمین اصلی را حذف کنید!")
        elif not bot_instance.is_admin(admin_id):
            await update.message.reply_text("⚠️ این کاربر ادمین نیست!")
        else:
            success = bot_instance.remove_admin(admin_id)
            if success:
                await update.message.reply_text(
                    f"✅ ادمین {admin_id} با موفقیت حذف شد!"
                )
            else:
                await update.message.reply_text("❌ خطا در حذف ادمین!")
    else:
        await update.message.reply_text(
            "❌ ID نامعتبر! لطفاً فقط اعداد وارد کنید\n"
            "مثال: 123456789"
        )
    context.user_data['waiting_for_remove_admin_id'] = False

# Handle deleting user
async def handle_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_text = update.message.text
    if user_id_text.isdigit():
        user_id = int(user_id_text)
        user_data = bot_instance.get_user_by_id(user_id)
        if user_data:
            bot_instance.delete_user(user_id)
            await update.message.reply_text(
                f"✅ کاربر {user_id} با موفقیت حذف شد!\n"
                f"UID حذف شده: {user_data[2]}"
            )
        else:
            await update.message.reply_text("❌ کاربر یافت نشد!")
    else:
        await update.message.reply_text(
            "❌ ID نامعتبر! لطفاً فقط اعداد وارد کنید\n"
            "مثال: 123456789"
        )
    context.user_data['waiting_for_delete_user_id'] = False

# Handle revoking user access
async def handle_revoke_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_text = update.message.text
    if user_id_text.isdigit():
        user_id = int(user_id_text)
        user_data = bot_instance.get_user_by_id(user_id)
        if user_data:
            bot_instance.revoke_user_access(user_id)
            await update.message.reply_text(
                f"✅ دسترسی کاربر {user_id} لغو شد!\n"
                f"UID: {user_data[2]}\n"
                f"وضعیت جدید: رد شده"
            )
            
            # اطلاع‌رسانی به کاربر
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🚫 دسترسی شما به گروه VIP لغو شد!\n\n"
                         "دلیل: عدم رعایت قوانین\n"
                         "برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
                )
            except:
                pass  # اگر نتوان پیام ارسال کرد
        else:
            await update.message.reply_text("❌ کاربر یافت نشد!")
    else:
        await update.message.reply_text(
            "❌ ID نامعتبر! لطفاً فقط اعداد وارد کنید\n"
            "مثال: 123456789"
        )
    context.user_data['waiting_for_revoke_user_id'] = False

def main():
    # Initialize database
    bot_instance.init_database()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot
    print("🤖 Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()