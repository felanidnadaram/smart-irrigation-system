from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SensorDataCreate(BaseModel):
    field_id: str
    soil_moisture: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=-40, le=60)
    humidity: float = Field(..., ge=0, le=100)
    light_intensity: float = Field(..., ge=0, le=120000)
    soil_ph: Optional[float] = Field(None, ge=0, le=14)
    wind_speed: Optional[float] = Field(None, ge=0)
    rainfall: Optional[float] = Field(None, ge=0)


class SensorDataInDB(BaseModel):
    id: str
    field_id: str
    timestamp: datetime
    soil_moisture: float
    temperature: float
    humidity: float
    light_intensity: float
    soil_ph: Optional[float] = None
    wind_speed: Optional[float] = None
    rainfall: Optional[float] = None


class SensorDataResponse(BaseModel):
    id: str
    field_id: str
    timestamp: datetime
    soil_moisture: float
    temperature: float
    humidity: float
    light_intensity: float
    soil_ph: Optional[float] = None
    wind_speed: Optional[float] = None
    rainfall: Optional[float] = None


class SensorDataQuery(BaseModel):
    field_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)


class SensorStats(BaseModel):
    field_id: str
    field_name: str
    avg_soil_moisture: float
    avg_temperature: float
    avg_humidity: float
    avg_light_intensity: float
    min_soil_moisture: float
    max_soil_moisture: float
    min_temperature: float
    max_temperature: float
    reading_count: int
