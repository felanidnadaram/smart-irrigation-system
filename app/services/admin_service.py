from bson import ObjectId
from datetime import datetime
from app.database import get_db


async def get_all_users(skip: int = 0, limit: int = 100) -> list:
    db = get_db()
    users = await db.users.find().skip(skip).limit(limit).to_list(limit)
    result = []
    for u in users:
        u["id"] = str(u.pop("_id"))
        u.pop("password_hash", None)
        result.append(u)
    return result


async def get_user_by_id(user_id: str) -> dict:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user["id"] = str(user.pop("_id"))
        user.pop("password_hash", None)
    return user


async def update_user(user_id: str, update_data: dict) -> dict:
    db = get_db()
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        return None
    return await get_user_by_id(user_id)


async def delete_user(user_id: str) -> bool:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user and user.get("role") == "admin":
        admin_count = await db.users.count_documents({"role": "admin"})
        if admin_count <= 1:
            return False

    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count > 0:
        await db.fields.delete_many({"owner_id": user_id})
        return True
    return False


async def get_all_fields(skip: int = 0, limit: int = 100) -> list:
    db = get_db()
    fields = await db.fields.find().skip(skip).limit(limit).to_list(limit)
    for f in fields:
        f["id"] = str(f.pop("_id"))
    return fields


async def admin_create_field(owner_id: str, field_data: dict) -> dict:
    db = get_db()
    owner = await db.users.find_one({"_id": ObjectId(owner_id)})
    if not owner:
        return None

    field = {
        "owner_id": owner_id,
        "field_name": field_data["field_name"],
        "location": field_data["location"],
        "crop_type": field_data["crop_type"],
        "area_hectares": field_data.get("area_hectares"),
        "notes": field_data.get("notes"),
        "irrigation_schedule": field_data.get("irrigation_schedule"),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.fields.insert_one(field)
    field["id"] = str(result.inserted_id)
    del field["_id"]
    return field


async def admin_update_field(field_id: str, update_data: dict) -> dict:
    db = get_db()
    update_data["updated_at"] = datetime.utcnow()
    result = await db.fields.update_one(
        {"_id": ObjectId(field_id)},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        return None
    field = await db.fields.find_one({"_id": ObjectId(field_id)})
    if field:
        field["id"] = str(field.pop("_id"))
    return field


async def admin_delete_field(field_id: str) -> bool:
    db = get_db()
    result = await db.fields.delete_one({"_id": ObjectId(field_id)})
    if result.deleted_count > 0:
        await db.sensor_data.delete_many({"field_id": field_id})
        await db.decisions.delete_many({"field_id": field_id})
        return True
    return False


async def get_events(limit: int = 100) -> list:
    db = get_db()
    events = await db.events.find().sort("timestamp", -1).limit(limit).to_list(limit)
    for e in events:
        e["id"] = str(e.pop("_id"))
    return events


async def log_event(event_type: str, message: str, details: dict = None):
    db = get_db()
    event = {
        "event_type": event_type,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow(),
    }
    await db.events.insert_one(event)


async def update_thresholds(thresholds: dict) -> dict:
    db = get_db()
    await db.settings.update_one(
        {"_id": "global_thresholds"},
        {"$set": thresholds},
        upsert=True,
    )
    return thresholds


async def get_thresholds() -> dict:
    db = get_db()
    settings = await db.settings.find_one({"_id": "global_thresholds"})
    if settings:
        settings.pop("_id", None)
    return settings or {}
