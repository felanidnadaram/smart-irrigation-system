from datetime import datetime, timedelta
from bson import ObjectId
from app.database import get_db


async def get_field_stats(field_id: str, hours: int = 24) -> dict:
    db = get_db()
    since = datetime.utcnow() - timedelta(hours=hours)

    pipeline = [
        {"$match": {"field_id": field_id, "timestamp": {"$gte": since}}},
        {"$group": {
            "_id": None,
            "avg_soil_moisture": {"$avg": "$soil_moisture"},
            "avg_temperature": {"$avg": "$temperature"},
            "avg_humidity": {"$avg": "$humidity"},
            "avg_light_intensity": {"$avg": "$light_intensity"},
            "min_soil_moisture": {"$min": "$soil_moisture"},
            "max_soil_moisture": {"$max": "$soil_moisture"},
            "min_temperature": {"$min": "$temperature"},
            "max_temperature": {"$max": "$temperature"},
            "reading_count": {"$sum": 1},
        }},
    ]

    result = await db.sensor_data.aggregate(pipeline).to_list(1)
    if not result:
        return None

    stats = result[0]
    stats.pop("_id", None)
    return stats


async def get_sensor_trend(field_id: str, hours: int = 24, metric: str = "soil_moisture") -> list:
    db = get_db()
    since = datetime.utcnow() - timedelta(hours=hours)

    pipeline = [
        {"$match": {"field_id": field_id, "timestamp": {"$gte": since}}},
        {"$sort": {"timestamp": 1}},
        {"$project": {
            "timestamp": 1,
            "value": f"${metric}",
        }},
    ]

    result = await db.sensor_data.aggregate(pipeline).to_list(1000)
    return [{"timestamp": r["timestamp"].isoformat(), "value": r["value"]} for r in result]


async def predict_next_day(field_id: str) -> dict:
    db = get_db()
    now = datetime.utcnow()
    since = now - timedelta(hours=48)

    pipeline = [
        {"$match": {"field_id": field_id, "timestamp": {"$gte": since}}},
        {"$sort": {"timestamp": 1}},
        {"$project": {
            "timestamp": 1,
            "soil_moisture": 1,
            "temperature": 1,
            "humidity": 1,
        }},
    ]

    readings = await db.sensor_data.aggregate(pipeline).to_list(100)
    if len(readings) < 2:
        return None

    recent = readings[-10:] if len(readings) >= 10 else readings

    def linear_extrapolate(values):
        n = len(values)
        if n < 2:
            return values[-1] if values else 0
        x_vals = list(range(n))
        y_vals = values
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        if denominator == 0:
            return y_vals[-1]
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return slope * (n + 24) + intercept

    moisture_vals = [r["soil_moisture"] for r in recent]
    temp_vals = [r["temperature"] for r in recent]
    humidity_vals = [r["humidity"] for r in recent]

    predicted_moisture = round(max(0, min(100, linear_extrapolate(moisture_vals))), 2)
    predicted_temp = round(max(-10, min(55, linear_extrapolate(temp_vals))), 2)
    predicted_humidity = round(max(0, min(100, linear_extrapolate(humidity_vals))), 2)

    def calc_trend(values):
        if len(values) < 2:
            return "پایدار"
        avg_first = sum(values[:len(values) // 2]) / (len(values) // 2)
        avg_second = sum(values[len(values) // 2:]) / (len(values) - len(values) // 2)
        diff = avg_second - avg_first
        if diff > 2:
            return "افزایشی"
        elif diff < -2:
            return "کاهشی"
        return "پایدار"

    confidence = min(0.95, 0.5 + len(recent) * 0.05)

    return {
        "predicted_soil_moisture": predicted_moisture,
        "predicted_temperature": predicted_temp,
        "predicted_humidity": predicted_humidity,
        "confidence": round(confidence, 2),
        "prediction_date": (now + timedelta(days=1)).isoformat(),
        "trend": calc_trend(moisture_vals),
    }


async def get_system_stats() -> dict:
    db = get_db()

    total_users = await db.users.count_documents({})
    total_farmers = await db.users.count_documents({"role": "farmer"})
    total_fields = await db.fields.count_documents({})
    active_fields = await db.fields.count_documents({"is_active": True})
    total_readings = await db.sensor_data.count_documents({})
    total_decisions = await db.decisions.count_documents({})
    unresolved_decisions = await db.decisions.count_documents({"is_resolved": False})

    since_24h = datetime.utcnow() - timedelta(hours=24)
    readings_24h = await db.sensor_data.count_documents({"timestamp": {"$gte": since_24h}})
    decisions_24h = await db.decisions.count_documents({"created_at": {"$gte": since_24h}})

    pipeline = [
        {"$match": {"timestamp": {"$gte": since_24h}}},
        {"$group": {
            "_id": None,
            "avg_soil_moisture": {"$avg": "$soil_moisture"},
            "avg_temperature": {"$avg": "$temperature"},
            "avg_humidity": {"$avg": "$humidity"},
        }},
    ]
    avg_result = await db.sensor_data.aggregate(pipeline).to_list(1)

    avg_data = {}
    if avg_result:
        avg_data = {
            "avg_soil_moisture": round(avg_result[0].get("avg_soil_moisture", 0), 2),
            "avg_temperature": round(avg_result[0].get("avg_temperature", 0), 2),
            "avg_humidity": round(avg_result[0].get("avg_humidity", 0), 2),
        }

    return {
        "total_users": total_users,
        "total_farmers": total_farmers,
        "total_fields": total_fields,
        "active_fields": active_fields,
        "total_readings": total_readings,
        "readings_24h": readings_24h,
        "total_decisions": total_decisions,
        "unresolved_decisions": unresolved_decisions,
        "decisions_24h": decisions_24h,
        "sensor_averages_24h": avg_data,
    }
