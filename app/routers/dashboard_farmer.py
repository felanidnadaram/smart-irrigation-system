from fastapi import APIRouter, Depends
from app.routers.auth import require_farmer
from app.services.farmer_service import get_farmer_fields_with_status
from app.services.analytics import get_field_stats, predict_next_day, get_sensor_trend

router = APIRouter(prefix="/dashboard/farmer", tags=["داشبورد کشاورز"])


@router.get("/overview", summary="نمای کلی داشبورد کشاورز")
async def farmer_overview(current_user: dict = Depends(require_farmer)):
    fields_status = await get_farmer_fields_with_status(current_user["id"])

    total_alerts = sum(f["alert_count"] for f in fields_status)
    active_fields = sum(1 for f in fields_status if f["field"].get("is_active", True))

    return {
        "user": {
            "full_name": current_user["full_name"],
            "role": current_user["role"],
        },
        "total_fields": len(fields_status),
        "active_fields": active_fields,
        "total_alerts": total_alerts,
        "fields": fields_status,
    }


@router.get("/field/{field_id}/stats", summary="آمار مزرعه")
async def field_stats(
    field_id: str,
    hours: int = 24,
    current_user: dict = Depends(require_farmer),
):
    stats = await get_field_stats(field_id, hours)
    return stats or {"message": "داده‌ای موجود نیست"}


@router.get("/field/{field_id}/prediction", summary="پیش‌بینی وضعیت مزرعه")
async def field_prediction(
    field_id: str,
    current_user: dict = Depends(require_farmer),
):
    prediction = await predict_next_day(field_id)
    if not prediction:
        return {"message": "داده کافی برای پیش‌بینی موجود نیست"}
    return prediction


@router.get("/field/{field_id}/trend", summary="روند داده‌ها")
async def field_trend(
    field_id: str,
    metric: str = "soil_moisture",
    hours: int = 24,
    current_user: dict = Depends(require_farmer),
):
    trend = await get_sensor_trend(field_id, hours, metric)
    return trend
