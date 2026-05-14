from fastapi import APIRouter, HTTPException, Query
from app.schemas.slot import SlotCreate, SlotBook, AvailableSlotDate
from app.models.slot import slot_mongo_schema, slot_helper
from app.config.db import slots_collection, users_collection
from bson import ObjectId
from datetime import datetime, date, timedelta
from typing import List, Optional

router = APIRouter(prefix="/slots", tags=["slots"])


def parse_slot_datetime(slot_date: date, slot_time: str) -> datetime:
    hours, minutes = slot_time.split(":")
    return datetime(slot_date.year, slot_date.month, slot_date.day, int(hours), int(minutes))


def validate_future_slot(slot_date: date, slot_time: str):
    now = datetime.utcnow()
    slot_dt = parse_slot_datetime(slot_date, slot_time)
    threshold = now + timedelta(minutes=15)
    if slot_dt < threshold:
        raise HTTPException(
            status_code=400,
            detail="Slot must be at least 15 minutes in the future and cannot be in the past",
        )


@router.post("/create")
async def create_slot(slot: SlotCreate):
    provider = await users_collection.find_one({"_id": ObjectId(slot.provider_user_id)})

    if not provider:
        raise HTTPException(status_code=404, detail="Provider user not found")

    validate_future_slot(slot.date, slot.time)

    existing = await slots_collection.find_one(
        {
            "provider_user_id": slot.provider_user_id,
            "date": slot.date.isoformat(),
            "time": slot.time,
        }
    )
    if existing:
        if existing["status"] == "booked":
            raise HTTPException(
                status_code=400,
                detail="Slot is already booked and cannot be changed",
            )

        new_status = (
            "unavailable"
            if existing["status"] == "available"
            else "available"
        )

        await slots_collection.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "updatedAt": datetime.utcnow(),
                    "status": new_status
                }
            }
        )

        updated_slot = await slots_collection.find_one(
            {"_id": existing["_id"]}
        )

        return {
            "message": f"Slot status changed to {new_status}",
            "slot": slot_helper(updated_slot)
        }

    slot_data = slot_mongo_schema(slot)
    result = await slots_collection.insert_one(slot_data)
    new_slot = await slots_collection.find_one({"_id": result.inserted_id})
    return {"message": "Slot created successfully", "slot": slot_helper(new_slot)}


@router.get("/available/{user_id}")
async def get_available_slots(
    user_id: str,
    start_date: Optional[date] = Query(default=None),
    days: int = Query(default=7, gt=0, le=30),
):
    # Check user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if start_date is None:
        start_date = date.today()

    today = date.today()
    end_date = start_date + timedelta(days=days - 1)

    query = {
        "provider_user_id": user_id,   # Match slots created by this provider
        "status": "available",
        "date": {
            "$gte": max(start_date, today).isoformat(),
            "$lte": end_date.isoformat(),
        },
    }

    cursor = slots_collection.find(query).sort([
        ("date", 1),
        ("time", 1)
    ])

    now = datetime.utcnow()
    threshold = now + timedelta(minutes=15)

    grouped = {}

    async for slot in cursor:
        slot_date = date.fromisoformat(slot["date"])
        slot_time = slot["time"]

        slot_dt = parse_slot_datetime(slot_date, slot_time)

        if slot_date == today and slot_dt < threshold:
            continue

        if slot_date < today:
            continue

        grouped.setdefault(slot["date"], []).append({
            "slot_id": str(slot["_id"]),
            "time": slot_time
        })

    if not grouped:
        return {
            "success": False,
            "message": "No available slots found",
            "data": []
        }

    return {
        "success": True,
        "message": "Available slots fetched successfully",
        "user_id": user_id,
        "data": [
            {
                "date": key,
                "times": values
            }
            for key, values in grouped.items()
        ]
    }

@router.post("/book")
async def book_slot(booking: SlotBook):
    slot = await slots_collection.find_one({"_id": ObjectId(booking.slot_id)})
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot["status"] != "available":
        if slot["status"] == "booked":
            raise HTTPException(status_code=400, detail="Slot is already booked")
        if slot["status"] == "unavailable":
            raise HTTPException(status_code=400, detail="Slot is unavailable")
        raise HTTPException(status_code=400, detail="Slot cannot be booked")

    participant = await users_collection.find_one({"_id": ObjectId(booking.participant_user_id)})
    if not participant:
        raise HTTPException(status_code=404, detail="Participant user not found")

    existing_participant_booking = await slots_collection.find_one(
        {
            "participant_user_id": booking.participant_user_id,
            "date": slot["date"],
            "time": slot["time"],
            "status": "booked",
        }
    )
    if existing_participant_booking:
        raise HTTPException(
            status_code=400,
            detail="Participant already has a booked slot at the same date and time",
        )

    await slots_collection.update_one(
        {"_id": ObjectId(booking.slot_id)},
        {
            "$set": {
                "participant_user_id": booking.participant_user_id,
                "status": "booked",
                "updatedAt": datetime.utcnow(),
            }
        },
    )

    booked_slot = await slots_collection.find_one({"_id": ObjectId(booking.slot_id)})
    provider_user_id = booked_slot["provider_user_id"]
    provider = await users_collection.find_one({"_id": ObjectId(provider_user_id)})
    participant = await users_collection.find_one({"_id": ObjectId(booked_slot["participant_user_id"])})

    return {
        "message": "Slot booked successfully",
        "slot": slot_helper(booked_slot),
        "provider_user": {
            "id": str(provider["_id"]),
            "name": provider.get("name"),
            "email": provider.get("email"),
            "number": provider.get("number"),
        },
        "participant_user": {
            "id": str(participant["_id"]),
            "name": participant.get("name"),
            "email": participant.get("email"),
            "number": participant.get("number"),
        },
    }

@router.get("/all/{user_id}")
async def get_all_slots_of_user(user_id: str):
    # Check user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all slots created by this user
    cursor = slots_collection.find(
        {"provider_user_id": user_id}
    ).sort([
        ("date", 1),
        ("time", 1)
    ])

    slots = []

    async for slot in cursor:

        participant_data = None

        # Fetch participant user details if booked
        if slot.get("participant_user_id"):

            participant = await users_collection.find_one({
                "_id": ObjectId(slot["participant_user_id"])
            })

            if participant:
                participant_data = {
                    "id": str(participant["_id"]),
                    "name": participant.get("name"),
                    "email": participant.get("email"),
                    "number": participant.get("number"),
                }

        slots.append({
            "slot_id": str(slot["_id"]),
            "date": slot["date"],
            "time": slot["time"],
            "status": slot["status"],
            "participant_user": participant_data,
            "createdAt": slot.get("createdAt"),
            "updatedAt": slot.get("updatedAt"),
        })

    return {
        "success": True,
        "message": "User slots fetched successfully",
        "user_id": user_id,
        "total_slots": len(slots),
        "data": slots
    }
