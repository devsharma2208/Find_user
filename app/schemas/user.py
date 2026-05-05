from pydantic import BaseModel, EmailStr
from typing import Optional


class Address(BaseModel):
    city: str
    state: str
    country: str
    currentlocation: str
    lat: float
    long: float
    landmark: str


class UserSignup(BaseModel):
    name: str
    number: str
    email: EmailStr
    password: str
    aadhar: str
    gender: str
    dob: str
    address: Address


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
