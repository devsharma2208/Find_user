from pydantic import BaseModel, validator
from typing import Optional


class BookingCreate(BaseModel):
    slot_id: str
    participant_user_id: str
    activity: Optional[str] = None

    @validator("activity")
    def validate_activity(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 100:
                raise ValueError("Activity name cannot exceed 100 characters")
        return v


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = None

    @validator("reason")
    def validate_reason(cls, v):
        if v is not None and len(v.strip()) > 500:
            raise ValueError("Cancel reason cannot exceed 500 characters")
        return v.strip() if v else v


class BookingCheckin(BaseModel):
    location_name: str
    lat: float
    long: float

    @validator("location_name")
    def validate_location_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Location name cannot be empty")
        if len(v) > 200:
            raise ValueError("Location name cannot exceed 200 characters")
        return v

    @validator("lat")
    def validate_lat(cls, v):
        if v < -90 or v > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("long")
    def validate_long(cls, v):
        if v < -180 or v > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class LocationUpdate(BaseModel):
    user_id: str
    lat: float
    long: float

    @validator("lat")
    def validate_lat(cls, v):
        if v < -90 or v > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("long")
    def validate_long(cls, v):
        if v < -180 or v > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class SOSRequest(BaseModel):
    user_id: str
    lat: Optional[float] = None
    long: Optional[float] = None
    message: Optional[str] = "I feel unsafe"

    @validator("message")
    def validate_message(cls, v):
        if v and len(v) > 500:
            raise ValueError("SOS message cannot exceed 500 characters")
        return v

    @validator("lat")
    def validate_lat(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator("long")
    def validate_long(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v
