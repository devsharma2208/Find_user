from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import date


class SlotCreate(BaseModel):
    provider_user_id: str
    date: date
    time: str

    @validator("time")
    def validate_time_format(cls, value):
        if len(value) not in (4, 5):
            raise ValueError("Time must be in HH:MM format")
        hours, sep, minutes = value.partition(":")
        if sep != ":" or not hours.isdigit() or not minutes.isdigit():
            raise ValueError("Time must be in HH:MM format")
        hour = int(hours)
        minute = int(minutes)
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Time must be a valid 24-hour time")
        return f"{hour:02d}:{minute:02d}"


class SlotBook(BaseModel):
    slot_id: str
    participant_user_id: str


class SlotResponse(BaseModel):
    id: str
    provider_user_id: str
    participant_user_id: Optional[str] = None
    date: date
    time: str
    status: str
    createdAt: str
    updatedAt: str


class AvailableSlotDate(BaseModel):
    date: date
    times: List[str]
