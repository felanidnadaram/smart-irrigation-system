from bson import ObjectId
from datetime import datetime
from app.database import get_db


async def get_farmer_fields(owner_id: str) -> list:
    db = get_db()
    fields = await db.fields.find({"owner_id": owner_id}).to_list(100)
    for f in fields:
        f["id"] = str(f.pop("_id"))
    return fields


async def create_field(owner_id: str, field_data: dict) -> dict:
    db = get_db()
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


async def update_field(field_id: str, owner_id: str, update_data: dict) -> dict:
    db = get_db()
    update_data["updated_at"] = datetime.utcnow()
    result = await db.fields.update_one(
        {"_id": ObjectId(field_id), "owner_id": owner_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        return None
    field = await db.fields.find_one({"_id": ObjectId(field_id)})
    if field:
        field["id"] = str(field.pop("_id"))
    return field


async def delete_field(field_id: str, owner_id: str) -> bool:
    db = get_db()
    result = await db.fields.delete_one(
        {"_id": ObjectId(field_id), "owner_id": owner_id}
    )
    return result.deleted_count > 0


async def get_field_by_id(field_id: str) -> dict:
    db = get_db()
    field = await db.fields.find_one({"_id": ObjectId(field_id)})
    if field:
        field["id"] = str(field.pop("_id"))
    return field


async def get_field_latest_reading(field_id: str) -> dict:
    db = get_db()
    reading = await db.sensor_data.find_one(
        {"field_id": field_id},
        sort=[("timestamp", -1)]
    )
    if reading:
        reading["id"] = str(reading.pop("_id"))
    return reading


async def get_farmer_fields_with_status(owner_id: str) -> list:
    db = get_db()
    fields = await db.fields.find({"owner_id": owner_id}).to_list(100)

    result = []
    for field in fields:
        field_id = str(field["_id"])
        field["id"] = field_id
        del field["_id"]

        latest_reading = await get_field_latest_reading(field_id)

        alert_count = await db.decisions.count_documents({
            "field_id": field_id,
            "is_resolved": False
        })

        result.append({
            "field": field,
            "latest_reading": latest_reading,
            "alert_count": alert_count,
        })

    return result
