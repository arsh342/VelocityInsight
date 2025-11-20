from pydantic import BaseModel
from typing import Optional


class TelemetryRow(BaseModel):
    expire_at: Optional[str] = None
    lap: Optional[int] = None
    meta_event: Optional[str] = None
    meta_session: Optional[str] = None
    meta_source: Optional[str] = None
    meta_time: Optional[str] = None
    original_vehicle_id: Optional[str] = None
    outing: Optional[int] = None
    telemetry_name: str
    telemetry_value: float
    timestamp: str
    vehicle_id: str
    vehicle_number: Optional[int] = None


class LapTimeRow(BaseModel):
    expire_at: Optional[str] = None
    lap: Optional[int] = None
    meta_event: Optional[str] = None
    meta_session: Optional[str] = None
    meta_source: Optional[str] = None
    meta_time: Optional[str] = None
    original_vehicle_id: Optional[str] = None
    outing: Optional[int] = None
    timestamp: str
    vehicle_id: str
    vehicle_number: Optional[int] = None
