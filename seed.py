import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime, timedelta
from app.config import MONGO_URI, DATABASE_NAME


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]

    await db.users.drop()
    await db.fields.drop()
    await db.sensor_data.drop()
    await db.decisions.drop()
    await db.events.drop()

    admin_user = {
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "role": "admin",
        "full_name": "مدیر سیستم",
        "phone": "09121234567",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    admin_result = await db.users.insert_one(admin_user)
    admin_id = str(admin_result.inserted_id)
    print(f"کاربر مدیر ایجاد شد: admin / admin123 (ID: {admin_id})")

    farmer_user = {
        "username": "farmer1",
        "password_hash": hash_password("farmer123"),
        "role": "farmer",
        "full_name": "علی محمدی",
        "phone": "09198765432",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    farmer_result = await db.users.insert_one(farmer_user)
    farmer_id = str(farmer_result.inserted_id)
    print(f"کشاورز ایجاد شد: farmer1 / farmer123 (ID: {farmer_id})")

    farmer2_user = {
        "username": "farmer2",
        "password_hash": hash_password("farmer123"),
        "role": "farmer",
        "full_name": "زهرا کریمی",
        "phone": "09351112233",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    farmer2_result = await db.users.insert_one(farmer2_user)
    farmer2_id = str(farmer2_result.inserted_id)
    print(f"کشاورز ایجاد شد: farmer2 / farmer123 (ID: {farmer2_id})")

    fields_data = [
        {
            "owner_id": farmer_id,
            "field_name": "زراعت گندم شمالی",
            "location": "استان خراسان رضوی، مشهد",
            "crop_type": "گندم",
            "area_hectares": 15.5,
            "notes": "مزرعه اصلی در منطقه کوهستانی",
            "irrigation_schedule": "هر ۳ روز یکبار",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "owner_id": farmer_id,
            "field_name": "باغ پسته",
            "location": "استان کرمان، رفسنجان",
            "crop_type": "پسته",
            "area_hectares": 25.0,
            "notes": "باغ پسته با آبیاری قطره‌ای",
            "irrigation_schedule": "هر ۵ روز یکبار",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "owner_id": farmer2_id,
            "field_name": "مزرعه برنج",
            "location": "استان گیلان، رشت",
            "crop_type": "برنج",
            "area_hectares": 10.0,
            "notes": "مزرعه برنج آبی",
            "irrigation_schedule": "روزانه",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    ]

    field_ids = []
    for f in fields_data:
        result = await db.fields.insert_one(f)
        field_ids.append(str(result.inserted_id))
        print(f"مزرعه ایجاد شد: {f['field_name']} (ID: {str(result.inserted_id)})")

    import random

    for fid in field_ids:
        readings = []
        now = datetime.utcnow()
        for day in range(7, 0, -1):
            for hour in range(0, 24, 2):
                ts = now - timedelta(days=day, hours=hour)
                h = ts.hour
                if 6 <= h <= 18:
                    temp_base = 25.0 + (h - 12) * 1.5
                else:
                    temp_base = 18.0

                moisture = max(5, min(95, 45 + random.uniform(-15, 15)))
                temp = max(-5, min(55, temp_base + random.uniform(-5, 5)))
                humidity = max(10, min(95, 55 + random.uniform(-20, 20)))

                if 6 <= h <= 20:
                    light = max(0, min(110000, 50000 * (1 - abs(h - 13) / 7) + random.uniform(-10000, 10000)))
                else:
                    light = max(0, random.uniform(0, 500))

                readings.append({
                    "field_id": fid,
                    "timestamp": ts,
                    "soil_moisture": round(moisture, 2),
                    "temperature": round(temp, 2),
                    "humidity": round(humidity, 2),
                    "light_intensity": round(light, 2),
                    "soil_ph": round(max(4.0, min(9.0, 6.5 + random.uniform(-1, 1))), 2),
                    "wind_speed": round(max(0, random.uniform(0, 30)), 2),
                    "rainfall": round(max(0, random.random() * 5 if random.random() > 0.7 else 0), 2),
                })

        await db.sensor_data.insert_many(readings)
        print(f"{len(readings)} داده سنسور برای مزرعه {fid} تولید شد")

        from app.services.decisions import analyze_and_decide
        from app.config import THRESHOLDS

        latest = readings[0]
        decisions = await analyze_and_decide(fid, latest, THRESHOLDS)
        for d in decisions:
            d["is_read"] = False
            d["is_resolved"] = False
            d["created_at"] = datetime.utcnow()
            await db.decisions.insert_one(d)

        if decisions:
            print(f"{len(decisions)} تصمیم برای مزرعه {fid} ایجاد شد")

    await db.events.insert_one({
        "event_type": "seed",
        "message": "داده‌های اولیه با موفقیت بارگذاری شدند",
        "details": {"users": 3, "fields": 3},
        "timestamp": datetime.utcnow(),
    })

    print("\n=== بارگذاری داده‌ها با موفقیت انجام شد ===")
    print("نام کاربری مدیر: admin / admin123")
    print("نام کاربری کشاورز: farmer1 / farmer123")
    print("نام کاربری کشاورز: farmer2 / farmer123")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
