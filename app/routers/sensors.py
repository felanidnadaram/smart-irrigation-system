from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.database import get_db
from app.routers.auth import get_current_user, require_farmer
from app.services.sensor_generator import generate_sensor_reading, generate_historical_data
from app.services.decisions import create_decisions_from_readings
from app.services.farmer_service import get_farmer_fields
from app.models.sensor_data import SensorDataResponse

router = APIRouter(prefix="/sensors", tags=["داده‌های سنسور"])


@router.get("/{field_id}/latest", response_model=SensorDataResponse, summary="آخرین داده سنسور مزرعه")
async def get_latest_reading(field_id: str, current_user: dict = Depends(require_farmer)):
    if current_user["role"] != "admin":
        fields = await get_farmer_fields(current_user["id"])
        field_ids = [f["id"] for f in fields]
        if field_id not in field_ids:
            raise HTTPException(status_code=403, detail="دسترسی به این مزرعه ندارید")

    db = get_db()
    reading = await db.sensor_data.find_one(
        {"field_id": field_id},
        sort=[("timestamp", -1)]
    )
    if not reading:
        raise HTTPException(status_code=404, detail="داده‌ای برای این مزرعه یافت نشد")
    reading["id"] = str(reading.pop("_id"))
    return reading


@router.get("/{field_id}/history", response_model=List[SensorDataResponse], summary="تاریخچه داده‌های سنسور")
async def get_history(
    field_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_farmer),
):
    if current_user["role"] != "admin":
        fields = await get_farmer_fields(current_user["id"])
        field_ids = [f["id"] for f in fields]
        if field_id not in field_ids:
            raise HTTPException(status_code=403, detail="دسترسی به این مزرعه ندارید")

    db = get_db()
    query = {"field_id": field_id}
    if start_time:
        query["timestamp"] = {"$gte": start_time}
    if end_time:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = end_time
        else:
            query["timestamp"] = {"$lte": end_time}

    readings = await db.sensor_data.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
    for r in readings:
        r["id"] = str(r.pop("_id"))
    return readings


@router.post("/{field_id}/generate", summary="تولید داده سنسور جدید")
async def trigger_generation(field_id: str, current_user: dict = Depends(require_farmer)):
    if current_user["role"] != "admin":
        fields = await get_farmer_fields(current_user["id"])
        field_ids = [f["id"] for f in fields]
        if field_id not in field_ids:
            raise HTTPException(status_code=403, detail="دسترسی به این مزرعه ندارید")

    reading = await generate_sensor_reading(field_id)
    await create_decisions_from_readings(field_id, reading)
    return {"message": "داده جدید با موفقیت تولید شد", "reading": reading}


@router.post("/{field_id}/generate-historical", summary="تولید داده‌های تاریخچه")
async def trigger_historical_generation(
    field_id: str,
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(require_farmer),
):
    if current_user["role"] != "admin":
        fields = await get_farmer_fields(current_user["id"])
        field_ids = [f["id"] for f in fields]
        if field_id not in field_ids:
            raise HTTPException(status_code=403, detail="دسترسی به این مزرعه ندارید")

    count = await generate_historical_data(field_id, days=days)
    return {"message": f"{count} داده تاریخچه تولید شد"}
