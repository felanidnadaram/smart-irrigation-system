from datetime import datetime
from bson import ObjectId
from app.database import get_db
from app.config import THRESHOLDS


async def analyze_and_decide(field_id: str, sensor_data: dict, thresholds: dict = None) -> list:
    if thresholds is None:
        thresholds = THRESHOLDS

    decisions = []

    moisture = sensor_data.get("soil_moisture", 0)
    temperature = sensor_data.get("temperature", 0)
    humidity = sensor_data.get("humidity", 0)
    light = sensor_data.get("light_intensity", 0)

    if moisture < thresholds.get("soil_moisture_low", 30):
        decisions.append({
            "field_id": field_id,
            "decision_type": "irrigation",
            "priority": "critical" if moisture < 15 else "high",
            "title": "نیاز به آبیاری",
            "description": f"رطوبت خاک در مزرعه بسیار پایین است: {moisture:.1f}%",
            "recommended_action": f"آبیاری فوری توصیه می‌شود. رطوبت فعلی {moisture:.1f}% و آستانه {thresholds.get('soil_moisture_low', 30)}% است.",
            "sensor_value": moisture,
            "threshold_value": thresholds.get("soil_moisture_low", 30),
        })
    elif moisture > thresholds.get("soil_moisture_high", 80):
        decisions.append({
            "field_id": field_id,
            "decision_type": "irrigation",
            "priority": "medium",
            "title": "آبیاری غیرضروری",
            "description": f"رطوبت خاک بیش از حد مطلوب است: {moisture:.1f}%",
            "recommended_action": "آبیاری را متوقف کنید. رطوبت خاک در محدوده بالا قرار دارد.",
            "sensor_value": moisture,
            "threshold_value": thresholds.get("soil_moisture_high", 80),
        })

    if temperature > thresholds.get("temperature_high", 35):
        decisions.append({
            "field_id": field_id,
            "decision_type": "temperature_alert",
            "priority": "critical" if temperature > 42 else "high",
            "title": "هشدار دمای بالا",
            "description": f"دمای هوا بسیار بالا است: {temperature:.1f}°C",
            "recommended_action": "اقدامات خنک‌سازی مانند سایه‌بان یا آبیاری هوایی را در نظر بگیرید.",
            "sensor_value": temperature,
            "threshold_value": thresholds.get("temperature_high", 35),
        })
    elif temperature < thresholds.get("temperature_low", 5):
        decisions.append({
            "field_id": field_id,
            "decision_type": "temperature_alert",
            "priority": "high" if temperature < 0 else "medium",
            "title": "هشدار دمای پایین",
            "description": f"دمای هوا بسیار پایین است: {temperature:.1f}°C",
            "recommended_action": "اقدامات محافظتی برای محصولات در برابر یخ‌زدگی انجام دهید.",
            "sensor_value": temperature,
            "threshold_value": thresholds.get("temperature_low", 5),
        })

    if humidity < thresholds.get("humidity_low", 20):
        decisions.append({
            "field_id": field_id,
            "decision_type": "humidity_alert",
            "priority": "medium",
            "title": "رطوبت پایین هوا",
            "description": f"رطوبت هوا بسیار پایین است: {humidity:.1f}%",
            "recommended_action": "سیستم‌های مه‌پاشی یا آبیاری هوایی را فعال کنید.",
            "sensor_value": humidity,
            "threshold_value": thresholds.get("humidity_low", 20),
        })
    elif humidity > thresholds.get("humidity_high", 90):
        decisions.append({
            "field_id": field_id,
            "decision_type": "humidity_alert",
            "priority": "medium",
            "title": "رطوبت بالای هوا",
            "description": f"رطوبت هوا بسیار بالا است: {humidity:.1f}%",
            "recommended_action": "تهویه مناسب را فراهم کنید تا از بیماری‌های قارچی جلوگیری شود.",
            "sensor_value": humidity,
            "threshold_value": thresholds.get("humidity_high", 90),
        })

    if light > thresholds.get("light_intensity_high", 90000):
        decisions.append({
            "field_id": field_id,
            "decision_type": "light_alert",
            "priority": "low",
            "title": "شدت نور بالا",
            "description": f"شدت نور بیش از حد مطلوب است: {light:.0f} لوکس",
            "recommended_action": "سایه‌بان برای محصولات حساس نصب کنید.",
            "sensor_value": light,
            "threshold_value": thresholds.get("light_intensity_high", 90000),
        })

    return decisions


async def create_decisions_from_readings(field_id: str, sensor_data: dict, thresholds: dict = None) -> list:
    db = get_db()
    decisions_data = await analyze_and_decide(field_id, sensor_data, thresholds)
    created_decisions = []

    for decision in decisions_data:
        decision["is_read"] = False
        decision["is_resolved"] = False
        decision["created_at"] = datetime.utcnow()
        result = await db.decisions.insert_one(decision)
        decision["id"] = str(result.inserted_id)
        created_decisions.append(decision)

    return created_decisions


async def get_field_decisions(field_id: str, limit: int = 50) -> list:
    db = get_db()
    decisions = await db.decisions.find(
        {"field_id": field_id}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    for d in decisions:
        d["id"] = str(d.pop("_id"))
    return decisions


async def get_unresolved_decisions(field_id: str = None) -> list:
    db = get_db()
    query = {"is_resolved": False}
    if field_id:
        query["field_id"] = field_id

    decisions = await db.decisions.find(query).sort("created_at", -1).to_list(100)
    for d in decisions:
        d["id"] = str(d.pop("_id"))
    return decisions


async def resolve_decision(decision_id: str) -> bool:
    db = get_db()
    result = await db.decisions.update_one(
        {"_id": ObjectId(decision_id)},
        {"$set": {"is_resolved": True}}
    )
    return result.modified_count > 0


async def mark_decision_read(decision_id: str) -> bool:
    db = get_db()
    result = await db.decisions.update_one(
        {"_id": ObjectId(decision_id)},
        {"$set": {"is_read": True}}
    )
    return result.modified_count > 0


async def get_all_decisions(limit: int = 100) -> list:
    db = get_db()
    decisions = await db.decisions.find().sort("created_at", -1).limit(limit).to_list(limit)
    for d in decisions:
        d["id"] = str(d.pop("_id"))
    return decisions
