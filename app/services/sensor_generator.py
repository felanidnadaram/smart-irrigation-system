import random
from datetime import datetime, timedelta
from bson import ObjectId
from app.database import get_db


async def generate_sensor_reading(field_id: str) -> dict:
    now = datetime.utcnow()
    hour = now.hour

    base_moisture = 45.0 + random.uniform(-15, 15)
    moisture_variation = random.uniform(-5, 5)
    soil_moisture = max(5, min(95, base_moisture + moisture_variation))

    if 6 <= hour <= 18:
        temp_base = 25.0 + (hour - 12) * 1.5
    else:
        temp_base = 18.0
    temperature = max(-5, min(55, temp_base + random.uniform(-5, 5)))

    humidity = max(10, min(95, 55.0 + random.uniform(-20, 20)))

    if 6 <= hour <= 20:
        light_base = 50000 * (1 - abs(hour - 13) / 7)
        light_intensity = max(0, min(110000, light_base + random.uniform(-10000, 10000)))
    else:
        light_intensity = max(0, random.uniform(0, 500))

    soil_ph = max(4.0, min(9.0, 6.5 + random.uniform(-1, 1)))
    wind_speed = max(0, random.uniform(0, 30))
    rainfall = max(0, random.random() * 5 if random.random() > 0.7 else 0)

    reading = {
        "field_id": field_id,
        "timestamp": now,
        "soil_moisture": round(soil_moisture, 2),
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "light_intensity": round(light_intensity, 2),
        "soil_ph": round(soil_ph, 2),
        "wind_speed": round(wind_speed, 2),
        "rainfall": round(rainfall, 2),
    }

    db = get_db()
    result = await db.sensor_data.insert_one(reading)
    reading["_id"] = str(result.inserted_id)
    return reading


async def generate_historical_data(field_id: str, days: int = 7, readings_per_day: int = 24):
    db = get_db()
    readings = []
    now = datetime.utcnow()

    for day in range(days, 0, -1):
        for hour_offset in range(readings_per_day):
            timestamp = now - timedelta(days=day, hours=hour_offset)
            hour = timestamp.hour

            if 6 <= hour <= 18:
                temp_base = 25.0 + (hour - 12) * 1.5
            else:
                temp_base = 18.0

            base_moisture = 45.0 + random.uniform(-15, 15)
            soil_moisture = max(5, min(95, base_moisture + random.uniform(-5, 5)))
            temperature = max(-5, min(55, temp_base + random.uniform(-5, 5)))
            humidity = max(10, min(95, 55.0 + random.uniform(-20, 20)))

            if 6 <= hour <= 20:
                light_base = 50000 * (1 - abs(hour - 13) / 7)
                light_intensity = max(0, min(110000, light_base + random.uniform(-10000, 10000)))
            else:
                light_intensity = max(0, random.uniform(0, 500))

            reading = {
                "field_id": field_id,
                "timestamp": timestamp,
                "soil_moisture": round(soil_moisture, 2),
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "light_intensity": round(light_intensity, 2),
                "soil_ph": round(max(4.0, min(9.0, 6.5 + random.uniform(-1, 1))), 2),
                "wind_speed": round(max(0, random.uniform(0, 30)), 2),
                "rainfall": round(max(0, random.random() * 5 if random.random() > 0.7 else 0), 2),
            }
            readings.append(reading)

    if readings:
        await db.sensor_data.insert_many(readings)
    return len(readings)
