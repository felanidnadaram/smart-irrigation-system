from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from typing import Optional
from app.routers.auth import require_admin
from app.services.analytics import get_system_stats
from app.services.admin_service import (
    get_all_users, update_user, delete_user,
    get_all_fields, admin_create_field, admin_update_field, admin_delete_field,
    get_events, update_thresholds, get_thresholds
)
from app.services.decisions import get_all_decisions
from app.services.sensor_generator import generate_sensor_reading, generate_historical_data
from app.services.decisions import create_decisions_from_readings

router = APIRouter(prefix="/dashboard/admin", tags=["داشبورد مدیر"])


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminFieldCreate(BaseModel):
    owner_id: str
    field_name: str
    location: str
    crop_type: str
    area_hectares: Optional[float] = None
    notes: Optional[str] = None
    irrigation_schedule: Optional[str] = None


class AdminFieldUpdate(BaseModel):
    field_name: Optional[str] = None
    location: Optional[str] = None
    crop_type: Optional[str] = None
    area_hectares: Optional[float] = None
    notes: Optional[str] = None
    irrigation_schedule: Optional[str] = None
    is_active: Optional[bool] = None
    owner_id: Optional[str] = None


class ThresholdUpdate(BaseModel):
    soil_moisture_low: Optional[float] = None
    soil_moisture_high: Optional[float] = None
    temperature_high: Optional[float] = None
    temperature_low: Optional[float] = None
    humidity_low: Optional[float] = None
    humidity_high: Optional[float] = None
    light_intensity_high: Optional[float] = None


@router.get("/stats", summary="آمار کلی سیستم")
async def system_stats(current_user: dict = Depends(require_admin)):
    stats = await get_system_stats()
    return stats


@router.get("/users", response_model=List[dict], summary="لیست کاربران")
async def list_users(current_user: dict = Depends(require_admin)):
    users = await get_all_users()
    return users


@router.put("/users/{user_id}", summary="ویرایش کاربر")
async def edit_user(
    user_id: str,
    data: AdminUserUpdate,
    current_user: dict = Depends(require_admin),
):
    update_dict = {k: v for k, v in data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="هیچ داده‌ای برای بروزرسانی ارسال نشد")

    user = await update_user(user_id, update_dict)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    return user


@router.delete("/users/{user_id}", summary="حذف کاربر")
async def remove_user(user_id: str, current_user: dict = Depends(require_admin)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="نمی‌توانید حساب خود را حذف کنید")

    success = await delete_user(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="حذف کاربر امکان‌پذیر نیست")
    return {"message": "کاربر با موفقیت حذف شد"}


@router.get("/fields", response_model=List[dict], summary="لیست تمام مزارع")
async def list_all_fields(current_user: dict = Depends(require_admin)):
    fields = await get_all_fields()
    return fields


@router.post("/fields", summary="افزودن مزرعه توسط مدیر")
async def create_field_admin(
    data: AdminFieldCreate,
    current_user: dict = Depends(require_admin),
):
    field = await admin_create_field(data.owner_id, data.dict(exclude={"owner_id"}))
    if not field:
        raise HTTPException(status_code=400, detail="کشاورز مورد نظر یافت نشد")

    await generate_historical_data(field["id"], days=7, readings_per_day=12)
    return field


@router.put("/fields/{field_id}", summary="ویرایش مزرعه توسط مدیر")
async def edit_field_admin(
    field_id: str,
    data: AdminFieldUpdate,
    current_user: dict = Depends(require_admin),
):
    update_dict = {k: v for k, v in data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="هیچ داده‌ای برای بروزرسانی ارسال نشد")

    field = await admin_update_field(field_id, update_dict)
    if not field:
        raise HTTPException(status_code=404, detail="مزرعه یافت نشد")
    return field


@router.delete("/fields/{field_id}", summary="حذف مزرعه توسط مدیر")
async def remove_field(field_id: str, current_user: dict = Depends(require_admin)):
    success = await admin_delete_field(field_id)
    if not success:
        raise HTTPException(status_code=404, detail="مزرعه یافت نشد")
    return {"message": "مزرعه با موفقیت حذف شد"}


@router.get("/decisions", summary="تمام تصمیمات سیستم")
async def list_decisions(current_user: dict = Depends(require_admin)):
    decisions = await get_all_decisions()
    return decisions


@router.get("/events", summary="رویدادهای سیستم")
async def list_events(current_user: dict = Depends(require_admin)):
    events = await get_events()
    return events


@router.get("/thresholds", summary="آستانه‌های جهانی")
async def get_current_thresholds(current_user: dict = Depends(require_admin)):
    thresholds = await get_thresholds()
    return thresholds


@router.put("/thresholds", summary="بروزرسانی آستانه‌ها")
async def update_global_thresholds(
    data: ThresholdUpdate,
    current_user: dict = Depends(require_admin),
):
    update_dict = {k: v for k, v in data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="هیچ داده‌ای برای بروزرسانی ارسال نشد")

    result = await update_thresholds(update_dict)
    return {"message": "آستانه‌ها با موفقیت بروزرسانی شدند", "thresholds": result}


@router.post("/generate-all", summary="تولید داده برای تمام مزارع")
async def generate_for_all(current_user: dict = Depends(require_admin)):
    from app.database import get_db
    db = get_db()
    fields = await db.fields.find({"is_active": True}).to_list(100)

    count = 0
    for field in fields:
        fid = str(field["_id"])
        reading = await generate_sensor_reading(fid)
        await create_decisions_from_readings(fid, reading)
        count += 1

    return {"message": f"داده برای {count} مزرعه تولید شد"}
