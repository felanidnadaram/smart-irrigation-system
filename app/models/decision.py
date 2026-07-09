from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DecisionType(str, Enum):
    irrigation = "irrigation"
    temperature_alert = "temperature_alert"
    humidity_alert = "humidity_alert"
    light_alert = "light_alert"
    general_recommendation = "general_recommendation"
    prediction = "prediction"


class DecisionPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DecisionCreate(BaseModel):
    field_id: str
    decision_type: DecisionType
    priority: DecisionPriority = DecisionPriority.medium
    title: str
    description: str
    recommended_action: str
    sensor_value: Optional[float] = None
    threshold_value: Optional[float] = None


class DecisionInDB(BaseModel):
    id: str
    field_id: str
    decision_type: DecisionType
    priority: DecisionPriority
    title: str
    description: str
    recommended_action: str
    sensor_value: Optional[float] = None
    threshold_value: Optional[float] = None
    is_read: bool = False
    is_resolved: bool = False
    created_at: datetime


class DecisionResponse(BaseModel):
    id: str
    field_id: str
    decision_type: DecisionType
    priority: DecisionPriority
    title: str
    description: str
    recommended_action: str
    sensor_value: Optional[float] = None
    threshold_value: Optional[float] = None
    is_read: bool = False
    is_resolved: bool = False
    created_at: datetime


class ThresholdUpdate(BaseModel):
    soil_moisture_low: Optional[float] = Field(None, ge=0, le=100)
    soil_moisture_high: Optional[float] = Field(None, ge=0, le=100)
    temperature_high: Optional[float] = Field(None, ge=-40, le=60)
    temperature_low: Optional[float] = Field(None, ge=-40, le=60)
    humidity_low: Optional[float] = Field(None, ge=0, le=100)
    humidity_high: Optional[float] = Field(None, ge=0, le=100)
    light_intensity_high: Optional[float] = Field(None, ge=0)


class Prediction(BaseModel):
    field_id: str
    field_name: str
    predicted_soil_moisture: float
    predicted_temperature: float
    predicted_humidity: float
    confidence: float
    prediction_date: datetime
    trend: str
