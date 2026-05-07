from pydantic import BaseModel, EmailStr, root_validator
from typing import Optional
from enum import Enum


class Address(BaseModel):
    city: str
    state: str
    country: str
    currentlocation: str
    lat: float
    long: float
    landmark: str


class MotiveEnum(str, Enum):
    FIND = "find"
    FIND_AND_EARN = "find and earn"
    EARN = "earn"


class UserSignup(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    number: Optional[str] = None
    password: Optional[str] = None
    aadhar: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[Address] = None
    motive: MotiveEnum = MotiveEnum.FIND
    verified: bool = False
    about: Optional[str] = None
    skills_interests: Optional[str] = None

    @root_validator(pre=True)
    def require_email_or_number(cls, values):
        email = values.get("email")
        number = values.get("number")
        if not email and not number:
            raise ValueError("Either email or number is required for signup")
        return values


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str]
    number: Optional[str]
    aadhar: Optional[str]
    gender: Optional[str]
    dob: Optional[str]
    address: Optional[Address]
    verified: Optional[bool]
    about: Optional[str]
    skills_interests: Optional[str]