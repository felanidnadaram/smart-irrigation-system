from pydantic import BaseModel, Field
from typing import Optional


class FieldCreate(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    crop_type: str = Field(..., min_length=1, max_length=100)
    area_hectares: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None
    irrigation_schedule: Optional[str] = None


class FieldUpdate(BaseModel):
    field_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    crop_type: Optional[str] = Field(None, min_length=1, max_length=100)
    area_hectares: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None
    irrigation_schedule: Optional[str] = None
    is_active: Optional[bool] = None


class FieldInDB(BaseModel):
    id: str
    owner_id: str
    field_name: str
    location: str
    crop_type: str
    area_hectares: Optional[float] = None
    notes: Optional[str] = None
    irrigation_schedule: Optional[str] = None
    is_active: bool = True


class FieldResponse(BaseModel):
    id: str
    owner_id: str
    field_name: str
    location: str
    crop_type: str
    area_hectares: Optional[float] = None
    notes: Optional[str] = None
    irrigation_schedule: Optional[str] = None
    is_active: bool = True


class FieldWithSensorData(BaseModel):
    field: FieldResponse
    latest_reading: Optional[dict] = None
    alert_count: int = 0
