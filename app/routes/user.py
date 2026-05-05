from fastapi import APIRouter, HTTPException
from app.schemas.user import UserSignup, UserLogin, UserUpdate
from app.models.user import user_mongo_schema
from app.config.db import users_collection
from app.utils.hash import hash_password, verify_password
from app.utils.jwt import create_token
from bson import ObjectId
from datetime import datetime

router = APIRouter()


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "number": user.get("number"),
        "email": user.get("email"),
        "aadhar": user.get("aadhar"),
        "gender": user.get("gender"),
        "dob": user.get("dob"),
        "address": user.get("address"),
        "createdAt": user.get("createdAt"),
        "updatedAt": user.get("updatedAt"),
    }


@router.post("/signup")
async def signup(user: UserSignup):

    # Check existing user
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)

    # ✅ timestamps add karo
    user_dict["createdAt"] = datetime.utcnow()
    user_dict["updatedAt"] = datetime.utcnow()

    result = await users_collection.insert_one(user_dict)

    # ✅ user fetch karo
    new_user = await users_collection.find_one({"_id": result.inserted_id})

    # ✅ token generate
    token = create_token({"user_id": str(new_user["_id"])})

    return {
        "message": "User created successfully",
        "token": token,
        "user": user_helper(new_user),
    }


@router.post("/login")
async def login(user: UserLogin):

    db_user = await users_collection.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_token({"user_id": str(db_user["_id"])})

    return {"message": "Login successful", "token": token}


@router.put("/update/{user_id}")
async def update_user(user_id: str, user: UserUpdate):

    update_data = {k: v for k, v in user.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    return {"message": "Profile updated"}
