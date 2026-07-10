# سیستم کشاورزی هوشمند دقیق

پلتفرم مدیریت مزارع بر پایه داده‌های سنسور که خوانش‌های محیطی تولید می‌کند، شرایط را بر اساس آستانه‌های پیکربندی‌شده ارزیابی می‌کند و توصیه‌های خودکار آبیاری و هشدارهای محیطی صادر می‌کند. این پروژه در قالب درس مهندسی نرم‌افزار توسعه یافته است.

---

## فهرست مطالب

- [معرفی پروژه](#معرفی-پروژه)
- [قابلیت‌های اصلی](#قابلیت‌های-اصلی)
- [معماری سیستم](#معماری-سیستم)
- [ساختار مخزن](#ساختار-مخزن)
- [پیش‌نیازها](#پیش‌نیازها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [پیکربندی](#پیکربندی)
- [اجرای برنامه](#اجرای-برنامه)
- [بارگذاری داده‌های نمونه](#بارگذاری-داده‌های-نمونه)
- [مرجع API](#مرجع-api)
- [داشبوردهای جلویی](#داشبوردهای-جلویی)
- [آزمون‌ها](#آزمون‌ها)
- [گواهی‌نامه‌های پیش‌فرض](#گواهی‌نامه‌های-پیش‌فرض)

---

## معرفی پروژه

کشاورزی به واکنش‌های به‌موقع در برابر تغییر شرایط محیطی وابسته است. این سیستم یک شبکه سنسور IoT را در مزارع شبیه‌سازی می‌کند و به‌طور مداوم داده‌های رطوبت خاک، دما، رطوبت هوا و شدت نور را جمع‌آوری می‌کند. یک موتور تصمیم‌گیری مبتنی بر قاعده، هر خوانش را در برابر آستانه‌های پیکربندی‌شده ارزیابی کرده و توصیه‌هایی مانند «آبیاری مزرعه X امروز» یا «هشدار دمای بالا» تولید می‌کند.

دو نقش کاربری با سیستم تعامل دارند:

- **کشاورز** — مزارع تحت مالکیت خود را مدیریت می‌کند، داده‌های سنسور و روندها را مشاهده می‌کند و توصیه‌ها را دریافت می‌کند.
- **مدیر** — تمام کاربران و مزارع را مدیریت می‌کند، آمار سراسری سیستم را رصد می‌کند و آستانه‌های تصمیم‌گیری را پیکربندی می‌کند.

تمام داده‌ها در MongoDB ذخیره شده و سیستم هم API REST و هم داشبوردهای سمت سرور را ارائه می‌دهد.

---

## قابلیت‌های اصلی

### احراز هویت و مجوزدهی

- ثبت‌نام کاربر با تعیین نقش (`farmer` یا `admin`).
- ورود مبتنی بر JWT با انقضای قابل پیکربندی توکن (پیش‌فرض: ۲۴ ساعت).
- دریافت کاربر جاری از طریق `GET /auth/me`.
- هش رمز عبور با bcrypt.
- محافظت endpoint‌ها بر اساس نقش با استفاده از dependency injection در FastAPI.
- نگهبانان نقش کشاورز و مدیر (`require_farmer`, `require_admin`).

### مدیریت مزارع

- عملیات CRUD بر مزارع کشاورزی (ایجاد، خواندن، ویرایش، حذف).
- هر مزرعه دارای: نام، موقعیت، نوع محصول، مساحت (هکتار)، یادداشت و برنامه آبیاری است.
- اعمال مالکیت — کشاورزان فقط به مزارع خود دسترسی و تغییر دارند.
- جداسازی بین کشاورزان — دسترسی متقاطع به مزارع کد `403 Forbidden` یا `404 Not Found` برمی‌گرداند.
- مدیر می‌تواند تمام مزارع تمام کشاورزان را مدیریت کند.

### مدیریت داده‌های سنسور

- تولید داده‌های مصنوعی سنسور با الگوهای واقع‌گرایانه روزانه (پیک دما در ظهر، شدت نور مطابق قوس خورشید).
- اندازه‌گیری‌های پشتیبانی‌شده: رطوبت خاک، دما، رطوبت هوا، شدت نور، pH خاک، سرعت باد، بارندگی.
- بازیابی آخرین خوانش برای هر مزرعه.
- پرس‌وجوی داده‌های تاریخچه با فیلتر زمان اختیاری (`start_time`, `end_time`) و محدودیت قابل پیکربندی.
- تولید خوانش تکی درخواستی (`POST /sensors/{id}/generate`).
- تولید انبوه داده‌های تاریخچه برای تعداد روزهای قابل پیکربندی (`POST /sensors/{id}/generate-historical`).
- تولید خودکار ۷ روز داده تاریخچه هنگام ایجاد مزرعه جدید.

### موتور تصمیم‌گیری و توصیه

- ارزیابی مبتنی بر قاعده خوانش‌های سنسور در برابر آستانه‌های پیکربندی‌شده.
- انواع تصمیمات تولیدشده:

  | نوع | محرک |
  |------|---------|
  | `irrigation` | رطوبت خاک زیر حداقل یا بالای حداکثر |
  | `temperature_alert` | دما بالای حداکثر یا زیر حداقل |
  | `humidity_alert` | رطوبت هوا زیر حداقل یا بالای حداکثر |
  | `light_alert` | شدت نور بالای حداکثر |

- سطوح اولویت: `low`، `medium`، `high`، `critical` — شدت در مقادیر بحرانی افزایش می‌یابد.
- هشدارهای همزمان متعدد برای شرایط بحرانی ترکیبی.
- ذخیره تصمیمات در MongoDB با پرچم‌های وضعیت `is_read` و `is_resolved`.
- کشاورزان می‌توانند تصمیمات را حل یا به‌عنوان خوانده‌شده علامت‌گذاری کنند.
- آستانه‌های جهانی توسط مدیران از طریق API قابل پیکربندی هستند.

### مدیریت

- مشاهده تمام کاربران، به‌روزرسانی ویژگی‌های کاربر (نام، تلفن، نقش، وضعیت فعال)، حذف کاربران.
- جلوگیری از حذف خود — مدیران نمی‌توانند حساب خود را حذف کنند.
- حذف آبشاری — حذف یک کاربر مزارع او را نیز حذف می‌کند.
- مشاهده و مدیریت تمام مزارع در سراسر سیستم.
- مشاهده تمام تصمیمات در سطح سیستم.
- پیکربندی آستانه‌های تصمیم‌گیری جهانی (`soil_moisture_low`, `temperature_high` و غیره).
- آمار سراسری: تعداد کل کاربران، مزارع، خوانش‌ها، تصمیمات، میانگین‌های ۲۴ ساعته.
- ثبت رویداد سیستم (راه‌اندازی، seed، رویدادهای عملیاتی).
- تولید انبوه داده‌های سنسور برای تمام مزارع فعال.

---

## معماری سیستم

### ساختار لایه‌ای

```text
Client Request
      |
      v
FastAPI Router Layer (app/routers/)
      |
      v
Authentication Dependencies (app/routers/auth.py)
      |
      v
Pydantic Validation Schemas (app/models/)
      |
      v
Business Logic Services (app/services/)
      |
      v
MongoDB via Motor Async Driver (app/database.py)
      |
      v
JSON Response
```

### وظایف لایه‌ها

| لایه | پوشه | وظیفه |
|-------|-----------|---------------|
| **نقطه ورود** | `app/main.py` | ایجاد برنامه FastAPI، مدیریت lifecycle، ثبت middleware، اضافه کردن routerها، اتصال فایل‌های ایستا و template |
| **پیکربندی** | `app/config.py` | متغیرهای محیطی، نام دیتابیس، تنظیمات JWT، آستانه‌های پیش‌فرض تصمیم‌گیری |
| **دیتابیس** | `app/database.py` | چرخه حیات کلاینت Motor، اتصال دیتابیس، ایجاد ایندکس، دسترسی جهانی به `db` |
| **روترها** | `app/routers/` | تعریف endpointهای HTTP، اعتبارسنجی درخواست، قالب‌بندی پاسخ |
| **احراز هویت** | `app/routers/auth.py` | ایجاد/تأیید JWT، هش رمز عبور، توابع وابسته مبتنی بر نقش |
| **مدل‌ها** | `app/models/` | اسکیماهای Pydantic برای اعتبارسنجی درخواست و serialization پاسخ |
| **سرویس‌ها** | `app/services/` | منطق کسب‌وکار — تولید سنسور، تحلیل تصمیم، آنالیتیکس، عملیات CRUD |
| **میان‌افزار** | `app/middleware.py` | مدیریت خطای سراسری با پیام‌های خطای فارسی |
| **ابزارها** | `app/utils/` | ثابت‌های پیام فارسی و توابع کمکی |
| **قالب‌ها** | `app/templates/` | قالب‌های HTML جینجا برای صفحه ورود، داشبورد کشاورز، داشبورد مدیر |
| **فایل‌های ایستا** | `app/static/` | شیت‌های استایل CSS و کلاینت‌های JavaScript برای هر دو داشبورد |
| **آزمون‌ها** | `tests/` | آزمون‌های خودکار سطح واحد، یکپارچه و سیستم |

### کلکسیون‌های دیتابیس

| کلکسیون | هدف | ایندکس‌های کلیدی |
|------------|---------|-------------|
| `users` | حساب‌های کاربری | `username` (unique)، `role` |
| `fields` | رکوردهای مزرعه | `owner_id` |
| `sensor_data` | خوانش‌های سنسور | `(field_id, timestamp)`، `timestamp` |
| `decisions` | توصیه‌ها و هشدارها | `(field_id, created_at)`، `created_at` |
| `events` | گزارش رویداد سیستم | `timestamp` |
| `settings` | پیکربندی جهانی (آستانه‌ها) | `_id` |

---

## ساختار مخزن

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                  # نقطه ورود برنامه FastAPI
│   ├── config.py                # پیکربندی مبتنی بر متغیرهای محیطی
│   ├── database.py              # اتصال و دسترسی MongoDB
│   ├── middleware.py             # میان‌افزار مدیریت خطای سراسری
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # اسکیماهای User، Token، LoginRequest
│   │   ├── field.py             # اسکیماهای CRUD و پاسخ Field
│   │   ├── sensor_data.py       # اسکیماهای خوانش سنسور
│   │   └── decision.py          # اسکیماهای Decision، Threshold، Prediction
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py              # /auth — ثبت‌نام، ورود، me
│   │   ├── fields.py            # /fields — CRUD مزارع کشاورز
│   │   ├── sensors.py           # /sensors — تولید و بازیابی داده
│   │   ├── decisions.py         # /decisions — بازیابی و حل تصمیمات
│   │   ├── dashboard_farmer.py  # /dashboard/farmer — نمای کلی، آمار، پیش‌بینی کشاورز
│   │   └── dashboard_admin.py   # /dashboard/admin — مدیریت و نظارت مدیر
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sensor_generator.py  # تولید مصنوعی خوانش سنسور
│   │   ├── decisions.py         # موتور تصمیم‌گیری مبتنی بر قاعده
│   │   ├── analytics.py         # پرس‌وجوهای aggregation، روندها، پیش‌بینی‌ها
│   │   ├── farmer_service.py    # عملیات مزرعه در حوزه کشاورز
│   │   └── admin_service.py     # عملیات در حوزه مدیر، ثبت رویداد
│   ├── templates/
│   │   ├── index.html           # صفحه ورود
│   │   ├── farmer_dashboard.html
│   │   └── admin_dashboard.html
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── farmer.js
│   │       └── admin.js
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # ثابت‌های پیام فارسی و توابع کمکی
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # فیکسچرهای آزمون، جداسازی دیتابیس، راه‌اندازی کلاینت
│   ├── test_auth.py             # ۸ آزمون احراز هویت
│   ├── test_fields.py           # ۸ آزمون مدیریت مزارع
│   ├── test_sensors.py          # ۵ آزمون داده سنسور
│   ├── test_decisions.py        # ۱۱ آزمون واحد موتور تصمیم‌گیری
│   ├── test_admin.py            # ۸ آزمون داشبورد مدیر
│   └── test_system_flows.py     # ۶ آزمون یکپارچه نهایی
├── requirements.txt             # وابستگی‌های Python
├── pytest.ini                   # پیکربندی pytest
├── run.py                       # اسکریپت راه‌اندازی برنامه
├── seed.py                      # بارگذار دیتابیس با داده‌های نمونه
├── TESTING.md                   # مستندات مجموعه آزمون (فارسی)
└── TEST_REPORT.md               # گزارش رسمی آزمون (انگلیسی)
```

---

## پیش‌نیازها

- **Python** نسخه ۳.۱۰ یا بالاتر
- **MongoDB** در حال اجرا روی `mongodb://localhost:27017`
- **pip** برای نصب بسته‌ها

---

## نصب و راه‌اندازی

۱. مخزن را کلون یا دانلود کنید:

```bash
cd intelligent-precision-agriculture
```

۲. یک محیط مجازی ایجاد و فعال کنید (توصیه‌شده):

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

۳. وابستگی‌ها را نصب کنید:

```bash
pip install -r requirements.txt
```

این دستور تمام وابستگی‌های اجرایی و آزمون را نصب می‌کند:

| بسته | هدف |
|---------|---------|
| `fastapi` | چارچوب وب |
| `uvicorn` | سرور ASGI |
| `motor` | درایور ناهمگام MongoDB |
| `pymongo` | درایور MongoDB (وابسته motor) |
| `pydantic` | اعتبارسنجی داده و تنظیمات |
| `python-jose[cryptography]` | ایجاد و تأیید توکن JWT |
| `bcrypt` | هش رمز عبور |
| `python-multipart` | تجزیه داده فرم برای FastAPI |
| `jinja2` | رندر قالب |
| `pytest` | چارچوب آزمون |
| `pytest-cov` | گزارش پوشش |
| `httpx` | کلاینت HTTP ناهمگام برای آزمون API |

---

## پیکربندی

تمام پیکربندی از طریق متغیرهای محیطی با مقادیر پیش‌فرض منطقی در `app/config.py` مدیریت می‌شود.

| متغیر | پیش‌فرض | توضیحات |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | رشته اتصال MongoDB |
| `DATABASE_NAME` | `precision_agriculture` | نام دیتابیس تولید |
| `TESTING` | `0` | روی `1` تنظیم شود تا از دیتابیس تست استفاده شود |
| `TEST_DATABASE_NAME` | `precision_agriculture_test` | نام دیتابیس تست (زمانی که `TESTING=1` باشد) |
| `SECRET_KEY` | `a3f5b8c1d4e7f0a2b6c9d3e8f1a4b7c0d5e9f2a6` | کلید امضای JWT |
| `ALGORITHM` | `HS256` | الگوریتم JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (۲۴ ساعت) | مدت عمر توکن |

آستانه‌های پیش‌فرض تصمیم‌گیری (تعریف‌شده در `app/config.py`):

| آستانه | مقدار پیش‌فرض | واحد |
|-----------|--------------|------|
| `soil_moisture_low` | ۳۰.۰ | درصد |
| `soil_moisture_high` | ۸۰.۰ | درصد |
| `temperature_high` | ۳۵.۰ | درجه سانتی‌گراد |
| `temperature_low` | ۵.۰ | درجه سانتی‌گراد |
| `humidity_low` | ۲۰.۰ | درصد |
| `humidity_high` | ۹۰.۰ | درصد |
| `light_intensity_high` | ۹۰۰۰۰ | لوکس |

فایل `.env` در مخزن وجود ندارد. در صورت نیاز به مقادیر غیرپیش‌فرض، متغیرهای محیطی را قبل از شروع برنامه تنظیم کنید.

---

## اجرای برنامه

سرور FastAPI را راه‌اندازی کنید:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

یا از اسکریپت راه‌اندازی ارائه‌شده استفاده کنید:

```bash
python run.py
```

برنامه در آدرس‌های زیر در دسترس خواهد بود:

| آدرس | توضیحات |
|-----|-------------|
| `http://localhost:8000` | صفحه ورود (ریشه) |
| `http://localhost:8000/dashboard/farmer` | داشبورد کشاورز |
| `http://localhost:8000/dashboard/admin` | داشبورد مدیر |
| `http://localhost:8000/docs` | Swagger UI (مستندات خودکار API) |
| `http://localhost:8000/redoc` | ReDoc (مستندات جایگزین API) |

---

## بارگذاری داده‌های نمونه

اسکریپت seed کاربران نمونه، مزارع، خوانش‌های سنسور و تصمیمات را در دیتابیس تولید ایجاد می‌کند.

```bash
python seed.py
```

**هشدار:** این اسکریپت تمام داده‌های موجود در کلکسیون‌های `users`، `fields`، `sensor_data`، `decisions` و `events` را قبل از درج داده‌های نمونه حذف می‌کند.

اسکریپت seed موارد زیر را ایجاد می‌کند:

| رکورد | مقدار |
|--------|-------|
| کاربر مدیر | `admin` / `admin123` |
| کشاورز | `farmer1` / `farmer123` |
| کشاورز | `farmer2` / `farmer123` |
| مزارع | ۳ مزرعه (گندم، پسته، برنج) با ۷ روز داده سنسور هرکدام |
| تصمیمات | تولیدشده از آخرین خوانش هر مزرعه |

---

## مرجع API

تمام endpointهای API نیاز به توکن `Bearer` در هدر `Authorization` دارند مگر اینکه خلاف آن ذکر شده باشد. پیام‌های خطا به فارسی برگردانده می‌شوند.

### احراز هویت — `/auth`

| متد | مسیر | احراز هویت | توضیحات |
|--------|------|------|-------------|
| `POST` | `/auth/register` | خیر | ثبت‌نام کاربر جدید |
| `POST` | `/auth/login` | خیر | ورود و دریافت توکن JWT |
| `GET` | `/auth/me` | بله | دریافت اطلاعات کاربر جاری |

**POST /auth/register** — بدنه درخواست:

```json
{
  "username": "string (3-50 chars)",
  "password": "string (6+ chars)",
  "full_name": "string (2-100 chars)",
  "role": "farmer | admin",
  "phone": "string (optional)"
}
```

**POST /auth/login** — بدنه درخواست:

```json
{
  "username": "string",
  "password": "string"
}
```

پاسخ:

```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "role": "farmer",
  "user_id": "mongodb_object_id",
  "full_name": "user_full_name"
}
```

### مدیریت مزارع — `/fields`

| متد | مسیر | احراز هویت | توضیحات |
|--------|------|------|-------------|
| `GET` | `/fields/` | کشاورز | لیست مزارع تحت مالکیت کاربر جاری |
| `POST` | `/fields/` | کشاورز | ایجاد مزرعه جدید |
| `GET` | `/fields/{field_id}` | کشاورز | دریافت یک مزرعه خاص |
| `PUT` | `/fields/{field_id}` | کشاورز | ویرایش مزرعه (فقط مالک) |
| `DELETE` | `/fields/{field_id}` | کشاورز | حذف مزرعه (فقط مالک) |

ایجاد مزرعه به‌طور خودکار ۷ روز داده تاریخچه سنسور برای آن مزرعه تولید می‌کند.

### داده‌های سنسور — `/sensors`

| متد | مسیر | احراز هویت | توضیحات |
|--------|------|------|-------------|
| `GET` | `/sensors/{field_id}/latest` | کشاورز | دریافت آخرین خوانش |
| `GET` | `/sensors/{field_id}/history` | کشاورز | پرس‌وجوی خوانش‌ها بر اساس بازه زمانی |
| `POST` | `/sensors/{field_id}/generate` | کشاورز | تولید خوانش جدید |
| `POST` | `/sensors/{field_id}/generate-historical` | کشاورز | تولید خوانش‌های تاریخچه |

**GET /sensors/{field_id}/history** — پارامترهای query:

| پارامتر | نوع | پیش‌فرض | توضیحات |
|-----------|------|---------|-------------|
| `start_time` | datetime | — | فیلتر خوانش‌ها پس از این زمان |
| `end_time` | datetime | — | فیلتر خوانش‌ها قبل از این زمان |
| `limit` | int | 100 | حداکثر خوانش‌های برگشتی (۱-۱۰۰۰) |

**POST /sensors/{field_id}/generate-historical** — پارامترهای query:

| پارامتر | نوع | پیش‌فرض | توضیحات |
|-----------|------|---------|-------------|
| `days` | int | 7 | تعداد روزهای تولید (۱-۳۰) |

### تصمیمات — `/decisions`

| متد | مسیر | احراز هویت | توضیحات |
|--------|------|------|-------------|
| `GET` | `/decisions/{field_id}` | کشاورز | دریافت تصمیمات یک مزرعه خاص |
| `GET` | `/decisions/alerts/all` | کشاورز | دریافت تمام هشدارهای حل‌نشده |
| `PUT` | `/decisions/{decision_id}/resolve` | کشاورز | علامت‌گذاری تصمیم به‌عنوان حل‌شده |
| `PUT` | `/decisions/{decision_id}/read` | کشاورز | علامت‌گذاری تصمیم به‌عنوان خوانده‌شده |

### داشبورد کشاورز — `/dashboard/farmer`

| متد | مسیر | احراز هویت | توضیحات |
|--------|------|------|-------------|
| `GET` | `/dashboard/farmer/overview` | کشاورز | نمای کلی داشبورد شامل مزارع، هشدارها، آخرین خوانش‌ها |
| `GET` | `/dashboard/farmer/field/{field_id}/stats` | کشاورز | آمار سنسور (میانگین، حداقل، حداکثر) طی N ساعت |
| `GET` | `/dashboard/farmer/field/{field_id}/prediction` | کشاورز | پیش‌بینی فردا با استفاده از extrapolation خطی |
| `GET` | `/dashboard/farmer/field/{field_id}/trend` | کشاورز | داده روند سری زمانی برای یک معیار خاص |

**GET /dashboard/farmer/field/{field_id}/trend** — پارامترهای query:

| پارامتر | نوع | پیش‌فرض | توضیحات |
|-----------|------|---------|-------------|
| `metric` | string | `soil_moisture` | معیار روند: `soil_moisture`، `temperature`، `humidity`، `light_intensity` |
| `hours` | int | 24 | پنجره زمانی به ساعت |

### داشبورد مدیر — `/dashboard/admin`

| متد | مسیر | احراز هویت | توضیحات |
|--------|------|------|-------------|
| `GET` | `/dashboard/admin/stats` | مدیر | آمار سراسری سیستم |
| `GET` | `/dashboard/admin/users` | مدیر | لیست تمام کاربران |
| `PUT` | `/dashboard/admin/users/{user_id}` | مدیر | ویرایش کاربر |
| `DELETE` | `/dashboard/admin/users/{user_id}` | مدیر | حذف کاربر |
| `GET` | `/dashboard/admin/fields` | مدیر | لیست تمام مزارع |
| `POST` | `/dashboard/admin/fields` | مدیر | ایجاد مزرعه برای هر کشاورزی |
| `PUT` | `/dashboard/admin/fields/{field_id}` | مدیر | ویرایش هر مزرعه‌ای |
| `DELETE` | `/dashboard/admin/fields/{field_id}` | مدیر | حذف هر مزرعه‌ای |
| `GET` | `/dashboard/admin/decisions` | مدیر | لیست تمام تصمیمات |
| `GET` | `/dashboard/admin/events` | مدیر | مشاهده گزارش رویداد سیستم |
| `GET` | `/dashboard/admin/thresholds` | مدیر | دریافت آستانه‌های جهانی جاری |
| `PUT` | `/dashboard/admin/thresholds` | مدیر | به‌روزرسانی آستانه‌های جهانی |
| `POST` | `/dashboard/admin/generate-all` | مدیر | تولید داده سنسور برای تمام مزارع فعال |

---

## داشبوردهای جلویی

برنامه شامل داشبوردهای HTML سمت سرور است:

- **صفحه ورود** (`/`) — ورود کشاورز/مدیر با تب‌های انتخاب نقش. رابط کاربری فارسی.
- **داشبورد کشاورز** (`/dashboard/farmer`) — لیست مزارع با وضعیت سنسور، هشدارها، مدیریت مزارع (افزودن/ویرایش/حذف)، نمای جزئیات سنسور با آمار و پیش‌بینی‌ها.
- **داشبورد مدیر** (`/dashboard/admin`) — رابط کاربری تب‌دار برای نمای کلی سیستم، مدیریت کاربران، مدیریت مزارع، نظارت بر تصمیمات و پیکربندی آستانه‌ها.

داشبوردها از طریق فراخوانی‌های `fetch()` به endpointهای API توضیح‌داده‌شده در بالا با backend ارتباط برقرار می‌کنند. تمام متن‌های نمایش داده‌شده به کاربر به فارسی هستند.

---

## آزمون‌ها

### اجرای آزمون‌ها

```bash
# اجرای تمام آزمون‌ها
pytest

# خروجی مفصل
pytest -v

# با گزارش پوشش (ترمینال)
pytest --cov=app --cov-report=term-missing

# با گزارش پوشش HTML
pytest --cov=app --cov-report=html

# اجرای یک فایل آزمون خاص
pytest tests/test_decisions.py

# اجرای یک آزمون خاص
pytest tests/test_auth.py::test_admin_login_success -v
```

### جداسازی دیتابیس آزمون

آزمون‌ها روی یک دیتابیس MongoDB جداگانه (`precision_agriculture_test`) عمل می‌کنند تا اطمینان حاصل شود که دیتابیس تولید هرگز تغییر نمی‌کند. این کار از طریق موارد زیر انجام می‌شود:

۱. `tests/conftest.py` در زمان import مقدار `os.environ["TESTING"] = "1"` را تنظیم می‌کند.
۲. `app/config.py` این مورد را تشخیص داده و `DATABASE_NAME` را به `precision_agriculture_test` تغییر می‌دهد.
۳. هر آزمون یک فیکسچر `test_db` دریافت می‌کند که تمام کلکسیون‌ها را قبل و بعد از اجرا پاک می‌کند.

### فهرست آزمون‌ها

| فایل | سطح | تعداد | توضیحات |
|------|-------|-------|-------------|
| `test_auth.py` | سیستم | ۸ | ورود، ثبت‌نام، اعتبارسنجی توکن، مدیریت خطا |
| `test_fields.py` | سیستم | ۸ | CRUD، اعمال مالکیت، کنترل دسترسی |
| `test_sensors.py` | یکپارچه | ۵ | تولید داده، بازیابی، پرس‌وجوی بازه زمانی |
| `test_decisions.py` | واحد | ۱۱ | قواعد آستانه، اولویت‌ها، حاشیه‌ها |
| `test_admin.py` | سیستم | ۸ | endpointهای مدیر، نگهبانان نقش، جلوگیری از حذف خود |
| `test_system_flows.py` | یکپارچه | ۶ | گردش‌کار نهایی در ماژول‌های متعدد |
| **مجموع** | | **۴۶** | |

### خلاصه پوشش

پوشش کل: **۶۷٪**

| ماژول | پوشش |
|--------|----------|
| `app/services/sensor_generator.py` | ۹۴٪ |
| `app/routers/auth.py` | ۹۳٪ |
| `app/routers/fields.py` | ۹۲٪ |
| `app/routers/sensors.py` | ۹۲٪ |
| `app/main.py` | ۸۱٪ |
| `app/routers/dashboard_admin.py` | ۷۶٪ |
| `app/services/decisions.py` | ۷۵٪ |
| `app/middleware.py` | ۷۵٪ |
| `app/services/farmer_service.py` | ۷۰٪ |
| `app/routers/dashboard_farmer.py` | ۵۲٪ |
| `app/routers/decisions.py` | ۵۱٪ |
| `app/database.py` | ۴۲٪ |
| `app/services/admin_service.py` | ۳۸٪ |
| `app/services/analytics.py` | ۲۹٪ |

گزارش‌های تفصیلی آزمون در [TEST_REPORT.md](TEST_REPORT.md) در دسترس هستند.

---

## گواهی‌نامه‌های پیش‌فرض

پس از اجرای `python seed.py`:

| نقش | نام کاربری | رمز عبور |
|------|----------|----------|
| مدیر | `admin` | `admin123` |
| کشاورز | `farmer1` | `farmer123` |
| کشاورز | `farmer2` | `farmer123` |

این گواهی‌نامه‌ها فقط برای اهداف توسعه و آزمون هستند.


نسخه انگلیسی  English version :
# Intelligent Precision Agriculture System

A sensor-driven farm management platform that generates environmental readings, evaluates conditions against configurable thresholds, and produces automated irrigation recommendations and environmental alerts. Built as a Software Engineering course project.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Seeding Sample Data](#seeding-sample-data)
- [API Reference](#api-reference)
- [Frontend Dashboards](#frontend-dashboards)
- [Testing](#testing)
- [Default Credentials](#default-credentials)

---

## Project Overview

Agriculture depends on timely responses to changing environmental conditions. This system simulates an IoT sensor network deployed across farm fields, continuously collecting data on soil moisture, temperature, humidity, and light intensity. A rule-based decision engine evaluates each reading against configurable thresholds and generates recommendations such as "irrigate field X today" or "high temperature alert."

Two user roles interact with the system:

- **Farmer** — manages owned fields, views sensor data and trends, receives recommendations.
- **Administrator** — manages all users and fields, monitors system-wide statistics, configures decision thresholds.

The system stores all data in MongoDB and exposes both a REST API and server-rendered dashboards.

---

## Key Features

### Authentication and Authorization

- User registration with role assignment (`farmer` or `admin`).
- JWT-based login with configurable token expiration (default: 24 hours).
- Current-user retrieval via `GET /auth/me`.
- Password hashing with bcrypt.
- Role-based endpoint protection using FastAPI dependency injection.
- Farmer and admin role guards (`require_farmer`, `require_admin`).

### Field Management

- CRUD operations on agricultural fields (create, read, update, delete).
- Each field has: name, location, crop type, area (hectares), notes, and irrigation schedule.
- Ownership enforcement — farmers can only access and modify their own fields.
- Isolation between farmers — cross-farm access returns `403 Forbidden` or `404 Not Found`.
- Admin can manage all fields across all farmers.

### Sensor Data Management

- Synthetic sensor data generation with realistic diurnal patterns (temperature peaks at midday, light intensity follows sun arc).
- Supported measurements: soil moisture, temperature, humidity, light intensity, soil pH, wind speed, rainfall.
- Latest reading retrieval per field.
- Historical data query with optional time-range filtering (`start_time`, `end_time`) and configurable limit.
- On-demand single reading generation (`POST /sensors/{id}/generate`).
- Bulk historical data generation for a configurable number of days (`POST /sensors/{id}/generate-historical`).
- Automatic 7-day historical data generation when a new field is created.

### Decision and Recommendation Engine

- Rule-based evaluation of sensor readings against configurable thresholds.
- Decision types produced:

  | Type | Trigger |
  |------|---------|
  | `irrigation` | Soil moisture below minimum or above maximum |
  | `temperature_alert` | Temperature above maximum or below minimum |
  | `humidity_alert` | Humidity below minimum or above maximum |
  | `light_alert` | Light intensity above maximum |

- Priority levels: `low`, `medium`, `high`, `critical` — severity escalates at extreme values.
- Multiple simultaneous alerts for compound worst-case conditions.
- Decisions stored in MongoDB with `is_read` and `is_resolved` status flags.
- Farmers can resolve or mark decisions as read.
- Global thresholds configurable by administrators via API.

### Administration

- View all users, update user properties (name, phone, role, active status), delete users.
- Self-deletion prevention — administrators cannot delete their own account.
- Cascade deletion — deleting a user removes their fields.
- View and manage all fields across the system.
- View all decisions system-wide.
- Configure global decision thresholds (`soil_moisture_low`, `temperature_high`, etc.).
- System-wide statistics: total users, fields, readings, decisions, 24-hour averages.
- System event log tracking (startup, seed, operational events).
- Bulk sensor data generation for all active fields.

---

## System Architecture

### Layered Structure

```text
Client Request
      |
      v
FastAPI Router Layer (app/routers/)
      |
      v
Authentication Dependencies (app/routers/auth.py)
      |
      v
Pydantic Validation Schemas (app/models/)
      |
      v
Business Logic Services (app/services/)
      |
      v
MongoDB via Motor Async Driver (app/database.py)
      |
      v
JSON Response
```

### Layer Responsibilities

| Layer | Directory | Responsibility |
|-------|-----------|---------------|
| **Entry Point** | `app/main.py` | FastAPI app creation, lifespan management, middleware registration, router inclusion, static file and template mounting |
| **Configuration** | `app/config.py` | Environment variables, database name, JWT settings, default decision thresholds |
| **Database** | `app/database.py` | Motor client lifecycle, database connection, index creation, global `db` accessor |
| **Routers** | `app/routers/` | HTTP endpoint definitions, request validation, response formatting |
| **Authentication** | `app/routers/auth.py` | JWT creation/verification, password hashing, role-based dependency functions |
| **Models** | `app/models/` | Pydantic schemas for request validation and response serialization |
| **Services** | `app/services/` | Business logic — sensor generation, decision analysis, analytics, CRUD operations |
| **Middleware** | `app/middleware.py` | Global exception handling with Persian error messages |
| **Utilities** | `app/utils/` | Persian message constants and helper functions |
| **Templates** | `app/templates/` | Jinja2 HTML templates for login, farmer dashboard, admin dashboard |
| **Static Assets** | `app/static/` | CSS stylesheets and JavaScript clients for both dashboards |
| **Tests** | `tests/` | Unit, integration, and system-level automated tests |

### Database Collections

| Collection | Purpose | Key Indexes |
|------------|---------|-------------|
| `users` | User accounts | `username` (unique), `role` |
| `fields` | Farm field records | `owner_id` |
| `sensor_data` | Sensor readings | `(field_id, timestamp)`, `timestamp` |
| `decisions` | Recommendations and alerts | `(field_id, created_at)`, `created_at` |
| `events` | System event log | `timestamp` |
| `settings` | Global configuration (thresholds) | `_id` |

---

## Repository Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment-based configuration
│   ├── database.py              # MongoDB connection and accessor
│   ├── middleware.py             # Global error handling middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User, Token, LoginRequest schemas
│   │   ├── field.py             # Field CRUD and response schemas
│   │   ├── sensor_data.py       # Sensor reading schemas
│   │   └── decision.py          # Decision, Threshold, Prediction schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py              # /auth — register, login, me
│   │   ├── fields.py            # /fields — farmer field CRUD
│   │   ├── sensors.py           # /sensors — data generation and retrieval
│   │   ├── decisions.py         # /decisions — decision retrieval and resolution
│   │   ├── dashboard_farmer.py  # /dashboard/farmer — farmer overview, stats, predictions
│   │   └── dashboard_admin.py   # /dashboard/admin — admin management and monitoring
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sensor_generator.py  # Synthetic sensor reading generation
│   │   ├── decisions.py         # Rule-based decision engine
│   │   ├── analytics.py         # Aggregation queries, trends, predictions
│   │   ├── farmer_service.py    # Farmer-scoped field operations
│   │   └── admin_service.py     # Admin-scoped operations, event logging
│   ├── templates/
│   │   ├── index.html           # Login page
│   │   ├── farmer_dashboard.html
│   │   └── admin_dashboard.html
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── farmer.js
│   │       └── admin.js
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Persian message constants and helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures, database isolation, client setup
│   ├── test_auth.py             # 8 authentication tests
│   ├── test_fields.py           # 8 field management tests
│   ├── test_sensors.py          # 5 sensor data tests
│   ├── test_decisions.py        # 11 decision engine unit tests
│   ├── test_admin.py            # 8 admin dashboard tests
│   └── test_system_flows.py     # 6 end-to-end integration tests
├── requirements.txt             # Python dependencies
├── pytest.ini                   # pytest configuration
├── run.py                       # Application launcher script
├── seed.py                      # Database seeder with sample data
├── TESTING.md                   # Test suite documentation (Persian)
└── TEST_REPORT.md               # Formal test report (English)
```

---

## Prerequisites

- **Python** 3.10 or later
- **MongoDB** running on `mongodb://localhost:27017`
- **pip** for package installation

---

## Installation

1. Clone or download the repository:

```bash
cd intelligent-precision-agriculture
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

This installs all runtime and testing dependencies:

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `motor` | Async MongoDB driver |
| `pymongo` | MongoDB driver (motor dependency) |
| `pydantic` | Data validation and settings |
| `python-jose[cryptography]` | JWT token creation and verification |
| `bcrypt` | Password hashing |
| `python-multipart` | Form data parsing for FastAPI |
| `jinja2` | Template rendering |
| `pytest` | Test framework |
| `pytest-cov` | Coverage reporting |
| `httpx` | Async HTTP client for API testing |

---

## Configuration

All configuration is handled through environment variables with sensible defaults defined in `app/config.py`.

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `precision_agriculture` | Production database name |
| `TESTING` | `0` | Set to `1` to use test database |
| `TEST_DATABASE_NAME` | `precision_agriculture_test` | Test database name (used when `TESTING=1`) |
| `SECRET_KEY` | `a3f5b8c1d4e7f0a2b6c9d3e8f1a4b7c0d5e9f2a6` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | Token lifetime |

Default decision thresholds (defined in `app/config.py`):

| Threshold | Default Value | Unit |
|-----------|--------------|------|
| `soil_moisture_low` | 30.0 | % |
| `soil_moisture_high` | 80.0 | % |
| `temperature_high` | 35.0 | °C |
| `temperature_low` | 5.0 | °C |
| `humidity_low` | 20.0 | % |
| `humidity_high` | 90.0 | % |
| `light_intensity_high` | 90000 | lux |

No `.env` file is included in the repository. Set environment variables before starting the application if you need non-default values.

---

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided launcher script:

```bash
python run.py
```

The application will be available at:

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Login page (root) |
| `http://localhost:8000/dashboard/farmer` | Farmer dashboard |
| `http://localhost:8000/dashboard/admin` | Admin dashboard |
| `http://localhost:8000/docs` | Swagger UI (auto-generated API docs) |
| `http://localhost:8000/redoc` | ReDoc (alternative API docs) |

---

## Seeding Sample Data

The seed script creates sample users, fields, sensor readings, and decisions in the production database.

```bash
python seed.py
```

**Warning:** This drops all existing data in the `users`, `fields`, `sensor_data`, `decisions`, and `events` collections before inserting sample data.

The seed script creates:

| Record | Value |
|--------|-------|
| Admin user | `admin` / `admin123` |
| Farmer user | `farmer1` / `farmer123` |
| Farmer user | `farmer2` / `farmer123` |
| Fields | 3 fields (wheat, pistachio, rice) with 7 days of sensor data each |
| Decisions | Generated from the latest reading of each field |

---

## API Reference

All API endpoints require a `Bearer` token in the `Authorization` header unless noted otherwise. Error messages are returned in Persian (Farsi).

### Authentication — `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | Register a new user |
| `POST` | `/auth/login` | No | Login and receive JWT token |
| `GET` | `/auth/me` | Yes | Get current user information |

**POST /auth/register** — Request body:

```json
{
  "username": "string (3-50 chars)",
  "password": "string (6+ chars)",
  "full_name": "string (2-100 chars)",
  "role": "farmer | admin",
  "phone": "string (optional)"
}
```

**POST /auth/login** — Request body:

```json
{
  "username": "string",
  "password": "string"
}
```

Response:

```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "role": "farmer",
  "user_id": "mongodb_object_id",
  "full_name": "user_full_name"
}
```

### Field Management — `/fields`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/fields/` | Farmer | List fields owned by current user |
| `POST` | `/fields/` | Farmer | Create a new field |
| `GET` | `/fields/{field_id}` | Farmer | Get a specific field |
| `PUT` | `/fields/{field_id}` | Farmer | Update a field (owner only) |
| `DELETE` | `/fields/{field_id}` | Farmer | Delete a field (owner only) |

Creating a field automatically generates 7 days of historical sensor data for that field.

### Sensor Data — `/sensors`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sensors/{field_id}/latest` | Farmer | Get most recent reading |
| `GET` | `/sensors/{field_id}/history` | Farmer | Query readings by time range |
| `POST` | `/sensors/{field_id}/generate` | Farmer | Generate a new reading |
| `POST` | `/sensors/{field_id}/generate-historical` | Farmer | Generate historical readings |

**GET /sensors/{field_id}/history** — Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_time` | datetime | — | Filter readings after this time |
| `end_time` | datetime | — | Filter readings before this time |
| `limit` | int | 100 | Maximum readings to return (1-1000) |

**POST /sensors/{field_id}/generate-historical** — Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 7 | Number of days to generate (1-30) |

### Decisions — `/decisions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/decisions/{field_id}` | Farmer | Get decisions for a specific field |
| `GET` | `/decisions/alerts/all` | Farmer | Get all unresolved alerts |
| `PUT` | `/decisions/{decision_id}/resolve` | Farmer | Mark a decision as resolved |
| `PUT` | `/decisions/{decision_id}/read` | Farmer | Mark a decision as read |

### Farmer Dashboard — `/dashboard/farmer`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/dashboard/farmer/overview` | Farmer | Dashboard overview with fields, alerts, latest readings |
| `GET` | `/dashboard/farmer/field/{field_id}/stats` | Farmer | Sensor statistics (avg, min, max) over N hours |
| `GET` | `/dashboard/farmer/field/{field_id}/prediction` | Farmer | Next-day prediction using linear extrapolation |
| `GET` | `/dashboard/farmer/field/{field_id}/trend` | Farmer | Time-series trend data for a specific metric |

**GET /dashboard/farmer/field/{field_id}/trend** — Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | `soil_moisture` | Metric to trend: `soil_moisture`, `temperature`, `humidity`, `light_intensity` |
| `hours` | int | 24 | Time window in hours |

### Admin Dashboard — `/dashboard/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/dashboard/admin/stats` | Admin | System-wide statistics |
| `GET` | `/dashboard/admin/users` | Admin | List all users |
| `PUT` | `/dashboard/admin/users/{user_id}` | Admin | Update a user |
| `DELETE` | `/dashboard/admin/users/{user_id}` | Admin | Delete a user |
| `GET` | `/dashboard/admin/fields` | Admin | List all fields |
| `POST` | `/dashboard/admin/fields` | Admin | Create a field for any farmer |
| `PUT` | `/dashboard/admin/fields/{field_id}` | Admin | Update any field |
| `DELETE` | `/dashboard/admin/fields/{field_id}` | Admin | Delete any field |
| `GET` | `/dashboard/admin/decisions` | Admin | List all decisions |
| `GET` | `/dashboard/admin/events` | Admin | View system event log |
| `GET` | `/dashboard/admin/thresholds` | Admin | Get current global thresholds |
| `PUT` | `/dashboard/admin/thresholds` | Admin | Update global thresholds |
| `POST` | `/dashboard/admin/generate-all` | Admin | Generate sensor data for all active fields |

---

## Frontend Dashboards

The application includes server-rendered HTML dashboards:

- **Login Page** (`/`) — Farmer/admin login with role selection tabs. Persian UI.
- **Farmer Dashboard** (`/dashboard/farmer`) — Field list with sensor status, alerts, field management (add/edit/delete), detailed sensor view with stats and predictions.
- **Admin Dashboard** (`/dashboard/admin`) — Tabbed interface for system overview, user management, field management, decision monitoring, and threshold configuration.

Dashboards communicate with the backend via `fetch()` calls to the API endpoints described above. All user-facing text is in Persian (Farsi).

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# With coverage report (terminal)
pytest --cov=app --cov-report=term-missing

# With HTML coverage report
pytest --cov=app --cov-report=html

# Run a specific test file
pytest tests/test_decisions.py

# Run a specific test case
pytest tests/test_auth.py::test_admin_login_success -v
```

### Test Database Isolation

Tests operate on a separate MongoDB database (`precision_agriculture_test`) to ensure the production database is never modified. This is achieved by:

1. `tests/conftest.py` sets `os.environ["TESTING"] = "1"` at import time.
2. `app/config.py` detects this and switches `DATABASE_NAME` to `precision_agriculture_test`.
3. Each test receives a `test_db` fixture that cleans all collections before and after execution.

### Test Inventory

| File | Level | Count | Description |
|------|-------|-------|-------------|
| `test_auth.py` | System | 8 | Login, registration, token validation, error handling |
| `test_fields.py` | System | 8 | CRUD, ownership enforcement, access control |
| `test_sensors.py` | Integration | 5 | Data generation, retrieval, time-range queries |
| `test_decisions.py` | Unit | 11 | Threshold rules, priorities, edge cases |
| `test_admin.py` | System | 8 | Admin endpoints, role guards, self-deletion prevention |
| `test_system_flows.py` | Integration | 6 | End-to-end workflows across multiple modules |
| **Total** | | **46** | |

### Coverage Summary

Overall coverage: **67%**

| Module | Coverage |
|--------|----------|
| `app/services/sensor_generator.py` | 94% |
| `app/routers/auth.py` | 93% |
| `app/routers/fields.py` | 92% |
| `app/routers/sensors.py` | 92% |
| `app/main.py` | 81% |
| `app/routers/dashboard_admin.py` | 76% |
| `app/services/decisions.py` | 75% |
| `app/middleware.py` | 75% |
| `app/services/farmer_service.py` | 70% |
| `app/routers/dashboard_farmer.py` | 52% |
| `app/routers/decisions.py` | 51% |
| `app/database.py` | 42% |
| `app/services/admin_service.py` | 38% |
| `app/services/analytics.py` | 29% |

Detailed test reports are available in [TEST_REPORT.md](TEST_REPORT.md).

---

## Default Credentials

After running `python seed.py`:

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `admin123` |
| Farmer | `farmer1` | `farmer123` |
| Farmer | `farmer2` | `farmer123` |

These credentials are for development and testing purposes only.
