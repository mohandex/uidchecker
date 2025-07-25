# 🤖 Trade BN VIP Bot

بات تلگرام پیشرفته برای مدیریت عضویت VIP کانال Trade BN با سیستم ثبت UID صرافی اوربیت

## ✨ ویژگی‌ها

### 🔐 سیستم امنیتی
- 📢 بررسی عضویت اجباری کانال `@trade_bn`
- 🔒 محدودیت دسترسی برای غیرعضوها
- 👑 سیستم مدیریت چندسطحه ادمین

### 🆔 سیستم ثبت UID پیشرفته
- 💰 راهنمای کامل ایجاد حساب صرافی اوربیت
- 🔗 کد رفرال اختصاصی `TRADEBN`
- 💵 شرایط حداقل واریز 50 دلار
- 🎯 جریان کاری هوشمند برای کاربران جدید و موجود
- ✅ سیستم تایید توسط ادمین

### 🔧 پنل مدیریت جامع
- 📊 آمار کاربران (کل، تایید شده، در انتظار، رد شده)
- 👥 مدیریت کاربران (لیست، حذف، لغو دسترسی)
- 👑 مدیریت ادمین‌ها (اضافه/حذف)
- 🔗 تغییر لینک گروه VIP
- ⚙️ تنظیمات بات

### 🎨 رابط کاربری
- 🔹 دکمه‌های شیشه‌ای زیبا
- 📱 طراحی ریسپانسیو
- 🌟 تجربه کاربری بهینه

## 🚀 نصب و راه‌اندازی

### 1. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### 2. تنظیم متغیرهای محیطی
فایل `.env` را ویرایش کنید:
```env
BOT_TOKEN=توکن_بات_شما
ADMIN_ID=آیدی_عددی_ادمین
```

### 3. اجرای بات
```bash
python bot.py
```

## 📋 نحوه استفاده

### برای کاربران:
1. **شروع**: دستور `/start` را ارسال کنید
2. **عضویت کانال**: ابتدا باید عضو کانال `@trade_bn` باشید
3. **عضویت در VIP**: روی دکمه "💎 عضویت در VIP" کلیک کنید
4. **انتخاب وضعیت حساب**:
   - اگر حساب اوربیت دارید: "بله" را انتخاب کنید
   - اگر حساب ندارید: "خیر" را انتخاب کنید و حساب جدید بسازید
5. **ارسال UID**: UID خود را از صرافی اوربیت ارسال کنید
6. **تایید**: منتظر تایید ادمین باشید
7. **دسترسی VIP**: پس از تایید، لینک گروه VIP دریافت کنید

### برای ادمین:
1. **ورود به پنل**: دستور `/admin` را ارسال کنید
2. **مدیریت کاربران**:
   - مشاهده آمار کاربران
   - تایید/رد درخواست‌های UID
   - حذف کاربران
   - لغو دسترسی کاربران
3. **مدیریت ادمین‌ها** (فقط ادمین اصلی):
   - اضافه کردن ادمین جدید
   - حذف ادمین موجود
4. **تنظیمات**:
   - تغییر لینک گروه VIP
   - مشاهده تنظیمات بات

## 🗄️ ساختار پایگاه داده

### جدول Users
- `user_id`: آیدی کاربر تلگرام
- `username`: نام کاربری
- `uid`: UID ارسالی از صرافی اوربیت
- `status`: وضعیت (pending/approved/rejected)
- `created_at`: زمان ایجاد

### جدول Admins
- `user_id`: آیدی ادمین تلگرام
- `username`: نام کاربری ادمین
- `added_at`: زمان اضافه شدن

### جدول Settings
- `key`: کلید تنظیمات
- `value`: مقدار تنظیمات

## 🔧 تنظیمات

- **VIP Group Link**: لینک گروه VIP که پس از تایید به کاربران ارسال می‌شود
- **Admin ID**: آیدی عددی ادمین اصلی
- **Channel Username**: نام کاربری کانال اجباری (`@trade_bn`)
- **Ourbit Referral Code**: کد رفرال صرافی اوربیت (`TRADEBN`)

## 📝 نکات مهم

### 🔐 امنیت و دسترسی
- کاربران باید عضو کانال `@trade_bn` باشند
- UID باید فقط شامل اعداد باشد
- فقط ادمین اصلی می‌تواند ادمین‌های جدید اضافه کند
- سیستم اعلان خودکار برای لغو دسترسی

### 💰 صرافی اوربیت
- حساب باید با کد رفرال `TRADEBN` ساخته شود
- حداقل واریز 50 دلار الزامی است
- کاربران موجود بدون کد رفرال باید حساب جدید بسازند
- لینک ثبت‌نام: `https://www.ourbit.com/register?inviteCode=TradeBN`

### 🎨 طراحی و عملکرد
- دکمه‌های شیشه‌ای زیبا با افکت‌های بصری
- پشتیبانی کامل از زبان فارسی
- مدیریت خطاها و پیام‌های راهنما
- ذخیره‌سازی ایمن در پایگاه داده SQLite

## 🛡️ امنیت

- 🔐 توکن بات و آیدی ادمین در فایل `.env` محفوظ نگهداری می‌شود
- 👑 دسترسی به پنل مدیریت فقط برای ادمین‌های مجاز
- 📢 بررسی عضویت کانال قبل از هر عملیات
- ✅ اعتبارسنجی UID قبل از ذخیره در پایگاه داده
- 🚫 محدودیت دسترسی برای کاربران غیرعضو
- 🔒 رمزگذاری ایمن اطلاعات حساس

## 📱 دستورات بات

### دستورات عمومی:
- `/start` - شروع بات و نمایش منوی اصلی
- `/admin` - ورود به پنل مدیریت (فقط ادمین‌ها)

### دکمه‌های تعاملی:
- **💎 عضویت در VIP** - شروع فرآیند ثبت UID صرافی اوربیت
- **پشتیبانی** - دریافت اطلاعات تماس با پشتیبانی
- **بررسی مجدد عضویت** - تایید عضویت در کانال
- **بله** - تایید داشتن حساب اوربیت (در فرآیند ثبت UID)
- **خیر** - عدم داشتن حساب اوربیت (در فرآیند ثبت UID)
- **ادامه عضویت** - ادامه فرآیند پس از ایجاد حساب جدید

### پنل مدیریت:
- **آمار کاربران** - نمایش آمار کامل کاربران
- **مدیریت کاربران** - عملیات مربوط به کاربران
- **مدیریت ادمین‌ها** - اضافه/حذف ادمین (فقط ادمین اصلی)
- **تنظیمات** - مشاهده و تغییر تنظیمات بات

## 🔄 جریان کاری ثبت UID

```
1. کاربر /start می‌زند
   ↓
2. بررسی عضویت کانال @trade_bn
   ↓
3. کلیک روی "💎 عضویت در VIP"
   ↓
4. نمایش راهنمای صرافی اوربیت
   ↓
5. انتخاب وضعیت حساب (دارم/ندارم)
   ↓
6. ارسال UID از تصویر راهنما
   ↓
7. بررسی و تایید توسط ادمین
   ↓
8. دریافت لینک گروه VIP
```

## 🆕 آپدیت‌های اخیر

### نسخه 2.0.0
- ✅ اضافه شدن بررسی عضویت اجباری کانال
- 🏦 یکپارچه‌سازی با صرافی اوربیت
- 🎯 جریان کاری هوشمند برای کاربران جدید/موجود
- 👑 سیستم مدیریت چندسطحه ادمین
- 📊 پنل آمار پیشرفته
- 🚫 قابلیت لغو دسترسی کاربران
- 🎨 بهبود رابط کاربری و دکمه‌های شیشه‌ای