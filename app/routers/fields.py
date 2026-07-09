from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.field import FieldCreate, FieldUpdate, FieldResponse
from app.routers.auth import get_current_user, require_farmer
from app.services import farmer_service
from app.services.sensor_generator import generate_historical_data

router = APIRouter(prefix="/fields", tags=["مدیریت مزارع"])


@router.get("/", response_model=List[FieldResponse], summary="لیست مزارع کشاورز")
async def list_my_fields(current_user: dict = Depends(require_farmer)):
    fields = await farmer_service.get_farmer_fields(current_user["id"])
    return fields


@router.post("/", response_model=FieldResponse, summary="افزودن مزرعه جدید")
async def create_field(
    field_data: FieldCreate,
    current_user: dict = Depends(require_farmer),
):
    field = await farmer_service.create_field(current_user["id"], field_data.dict())

    await generate_historical_data(field["id"], days=7, readings_per_day=12)

    return field


@router.get("/{field_id}", response_model=FieldResponse, summary="دریافت اطلاعات مزرعه")
async def get_field(field_id: str, current_user: dict = Depends(require_farmer)):
    field = await farmer_service.get_field_by_id(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="مزرعه یافت نشد")
    if current_user["role"] != "admin" and field["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="دسترسی به این مزرعه ندارید")
    return field


@router.put("/{field_id}", response_model=FieldResponse, summary="ویرایش اطلاعات مزرعه")
async def update_field(
    field_id: str,
    field_data: FieldUpdate,
    current_user: dict = Depends(require_farmer),
):
    update_dict = {k: v for k, v in field_data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="هیچ داده‌ای برای بروزرسانی ارسال نشد")

    field = await farmer_service.update_field(field_id, current_user["id"], update_dict)
    if not field:
        raise HTTPException(status_code=404, detail="مزرعه یافت نشد یا دسترسی ندارید")
    return field


@router.delete("/{field_id}", summary="حذف مزرعه")
async def delete_field(field_id: str, current_user: dict = Depends(require_farmer)):
    success = await farmer_service.delete_field(field_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="مزرعه یافت نشد یا دسترسی ندارید")
    return {"message": "مزرعه با موفقیت حذف شد"}
