from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.routers.auth import get_current_user, require_farmer
from app.services.decisions import get_field_decisions, get_unresolved_decisions, resolve_decision, mark_decision_read
from app.services.farmer_service import get_farmer_fields

router = APIRouter(prefix="/decisions", tags=["تصمیمات و توصیه‌ها"])


@router.get("/{field_id}", response_model=List[dict], summary="تصمیمات مزرعه")
async def get_decisions(
    field_id: str,
    current_user: dict = Depends(require_farmer),
):
    if current_user["role"] != "admin":
        fields = await get_farmer_fields(current_user["id"])
        field_ids = [f["id"] for f in fields]
        if field_id not in field_ids:
            raise HTTPException(status_code=403, detail="دسترسی به این مزرعه ندارید")

    decisions = await get_field_decisions(field_id)
    return decisions


@router.get("/alerts/all", response_model=List[dict], summary="تمام هشدارهای فعال")
async def get_all_alerts(current_user: dict = Depends(require_farmer)):
    if current_user["role"] == "admin":
        decisions = await get_unresolved_decisions()
    else:
        fields = await get_farmer_fields(current_user["id"])
        field_ids = [f["id"] for f in fields]
        all_decisions = []
        for fid in field_ids:
            d = await get_unresolved_decisions(fid)
            all_decisions.extend(d)
        decisions = all_decisions
    return decisions


@router.put("/{decision_id}/resolve", summary="حل تصمیم")
async def resolve(decision_id: str, current_user: dict = Depends(require_farmer)):
    success = await resolve_decision(decision_id)
    if not success:
        raise HTTPException(status_code=404, detail="تصمیم یافت نشد")
    return {"message": "تصمیم با موفقیت حل شد"}


@router.put("/{decision_id}/read", summary="خواندن تصمیم")
async def mark_read(decision_id: str, current_user: dict = Depends(require_farmer)):
    success = await mark_decision_read(decision_id)
    if not success:
        raise HTTPException(status_code=404, detail="تصمیم یافت نشد")
    return {"message": "تصمیم به عنوان خوانده شده علامت‌گذاری شد"}
