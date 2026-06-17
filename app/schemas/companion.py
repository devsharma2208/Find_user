from pydantic import BaseModel, validator
from typing import Optional, List
from enum import Enum


class SkillEnum(str, Enum):
    GYM_TRAINING = "Gym Training"
    YOGA = "Yoga"
    RUNNING = "Running"
    TRAVEL = "Travel"
    STUDY = "Study"
    MUSIC = "Music"
    PHOTOGRAPHY = "Photography"
    COOKING = "Cooking"
    ADVENTURE = "Adventure"
    HIKING = "Hiking"
    MEDITATION = "Meditation"
    NUTRITION = "Nutrition"
    TECH = "Tech"
    CODING = "Coding"
    EVENTS = "Events"
    FITNESS = "Fitness"


class CompanionSetup(BaseModel):
    user_id: str
    bio: str
    skills: List[SkillEnum]
    hourly_rate: float

    @validator("bio")
    def validate_bio(cls, v):
        v = v.strip()
        if len(v) < 20:
            raise ValueError("Bio must be at least 20 characters")
        if len(v) > 500:
            raise ValueError("Bio cannot exceed 500 characters")
        return v

    @validator("skills")
    def validate_skills(cls, v):
        if not v:
            raise ValueError("At least one skill is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 skills allowed")
        return list(set(v))

    @validator("hourly_rate")
    def validate_hourly_rate(cls, v):
        if v < 10 or v > 100:
            raise ValueError("Hourly rate must be between $10 and $100")
        return round(v, 2)


class CompanionUpdate(BaseModel):
    bio: Optional[str] = None
    skills: Optional[List[SkillEnum]] = None
    hourly_rate: Optional[float] = None

    @validator("bio")
    def validate_bio(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 20:
                raise ValueError("Bio must be at least 20 characters")
            if len(v) > 500:
                raise ValueError("Bio cannot exceed 500 characters")
        return v

    @validator("skills")
    def validate_skills(cls, v):
        if v is not None:
            if not v:
                raise ValueError("At least one skill is required")
            if len(v) > 10:
                raise ValueError("Maximum 10 skills allowed")
            return list(set(v))
        return v

    @validator("hourly_rate")
    def validate_hourly_rate(cls, v):
        if v is not None:
            if v < 10 or v > 100:
                raise ValueError("Hourly rate must be between $10 and $100")
            return round(v, 2)
        return v
