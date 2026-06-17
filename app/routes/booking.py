from fastapi import APIRouter, HTTPException
from app.schemas.booking import (
    BookingCreate, BookingCancelRequest, BookingCheckin,
    LocationUpdate, SOSRequest
)
from app.models.booking import booking_mongo_schema, booking_helper
from app.config.db import (
    bookings_collection, slots_collection,
    users_collection, companions_collection
)
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ── Internal helpers ──────────────────────────────────────────────────────────

def _user_mini(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
        "number": user.get("number"),
    }


def _companion_mini(companion: dict) -> dict:
    photos = companion.get("photos", [])
    return {
        "companion_id": str(companion["_id"]),
        "user_id": companion.get("user_id"),
        "rating": companion.get("rating", 0.0),
        "total_reviews": companion.get("total_reviews", 0),
        "photo": photos[0] if photos else None,
        "hourly_rate": companion.get("hourly_rate"),
        "skills": companion.get("skills", []),
        "is_verified": companion.get("is_verified", False),
    }


async def _get_booking_or_404(booking_id: str) -> dict:
    try:
        booking = await bookings_collection.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid booking_id format")
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


# ─────────────────────────────────────────────────────────────────────────────
# POST /bookings
# Create a booking from an available slot
# ─────────────────────────────────────────────────────────────────────────────
@router.post("")
async def create_booking(data: BookingCreate):

    # Validate slot
    try:
        slot = await slots_collection.find_one({"_id": ObjectId(data.slot_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid slot_id format")

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot["status"] == "booked":
        raise HTTPException(status_code=409, detail="Slot is already booked")
    if slot["status"] != "available":
        raise HTTPException(status_code=400, detail=f"Slot is '{slot['status']}' and cannot be booked")

    # Validate participant
    try:
        participant = await users_collection.find_one({"_id": ObjectId(data.participant_user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid participant_user_id format")

    if not participant:
        raise HTTPException(status_code=404, detail="Participant user not found")

    # Prevent companion booking their own slot
    if slot["provider_user_id"] == data.participant_user_id:
        raise HTTPException(status_code=400, detail="You cannot book your own slot")

    # Prevent participant double-booking same date+time
    conflicting = await bookings_collection.find_one({
        "participant_user_id": data.participant_user_id,
        "date": slot["date"],
        "time": slot["time"],
        "status": {"$in": ["pending", "active"]}
    })
    if conflicting:
        raise HTTPException(
            status_code=409,
            detail="You already have a booking at this date and time"
        )

    # Create booking document
    booking_data = booking_mongo_schema(slot, data.participant_user_id, data.activity)
    result = await bookings_collection.insert_one(booking_data)

    # Lock the slot
    await slots_collection.update_one(
        {"_id": ObjectId(data.slot_id)},
        {"$set": {
            "status": "booked",
            "participant_user_id": data.participant_user_id,
            "updatedAt": datetime.utcnow()
        }}
    )

    new_booking = await bookings_collection.find_one({"_id": result.inserted_id})

    companion_user = await users_collection.find_one({"_id": ObjectId(slot["provider_user_id"])})
    companion_profile = await companions_collection.find_one({"user_id": slot["provider_user_id"]})

    return {
        "message": "Booking created successfully",
        "booking": booking_helper(new_booking),
        "companion": {
            "name": companion_user.get("name") if companion_user else None,
            **(  _companion_mini(companion_profile) if companion_profile else {}  )
        },
        "participant": _user_mini(participant)
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /bookings/user/{user_id}
# Get all bookings for a user — split into upcoming and past
# NOTE: must be defined BEFORE /{booking_id} to avoid route conflict
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/user/{user_id}")
async def get_user_bookings(user_id: str):

    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_bookings = await bookings_collection.find({
        "$or": [
            {"participant_user_id": user_id},
            {"companion_user_id": user_id}
        ]
    }).sort("createdAt", -1).to_list(length=None)

    upcoming = []
    past = []

    for booking in all_bookings:
        is_seeker = booking["participant_user_id"] == user_id
        companion_user_id = booking["companion_user_id"]

        companion_user = await users_collection.find_one({"_id": ObjectId(companion_user_id)})
        companion_profile = await companions_collection.find_one({"user_id": companion_user_id})

        photos = companion_profile.get("photos", []) if companion_profile else []

        card = {
            "booking_id": str(booking["_id"]),
            "slot_id": booking.get("slot_id"),
            "activity": booking.get("activity"),
            "date": booking.get("date"),
            "time": booking.get("time"),
            "status": booking.get("status"),
            "role": "seeker" if is_seeker else "companion",
            "companion": {
                "user_id": companion_user_id,
                "name": companion_user.get("name") if companion_user else None,
                "photo": photos[0] if photos else None,
                "rating": companion_profile.get("rating", 0.0) if companion_profile else 0.0,
                "hourly_rate": companion_profile.get("hourly_rate") if companion_profile else None,
                "is_verified": companion_profile.get("is_verified", False) if companion_profile else False,
            }
        }

        if booking["status"] in ("pending", "active"):
            upcoming.append(card)
        else:
            past.append({**card, "can_review": booking["status"] == "completed"})

    return {
        "user_id": user_id,
        "total_upcoming": len(upcoming),
        "total_past": len(past),
        "upcoming": upcoming,
        "past": past,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /bookings/{booking_id}
# Get single booking with full companion + participant details
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{booking_id}")
async def get_booking(booking_id: str):

    booking = await _get_booking_or_404(booking_id)

    companion_user = await users_collection.find_one({"_id": ObjectId(booking["companion_user_id"])})
    participant_user = await users_collection.find_one({"_id": ObjectId(booking["participant_user_id"])})
    companion_profile = await companions_collection.find_one({"user_id": booking["companion_user_id"]})

    return {
        "booking": booking_helper(booking),
        "companion": {
            "name": companion_user.get("name") if companion_user else None,
            **(  _companion_mini(companion_profile) if companion_profile else {}  )
        },
        "participant": _user_mini(participant_user) if participant_user else None
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /bookings/{booking_id}/cancel
# Cancel a pending booking and release the slot
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: str, data: BookingCancelRequest):

    booking = await _get_booking_or_404(booking_id)

    status = booking["status"]
    if status == "cancelled":
        raise HTTPException(status_code=409, detail="Booking is already cancelled")
    if status == "active":
        raise HTTPException(status_code=400, detail="Cannot cancel an active session. Use end session instead.")
    if status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed session")

    now = datetime.utcnow()

    await bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "status": "cancelled",
            "cancel_reason": data.reason,
            "updatedAt": now
        }}
    )

    # Release the slot back to available
    await slots_collection.update_one(
        {"_id": ObjectId(booking["slot_id"])},
        {"$set": {
            "status": "available",
            "participant_user_id": None,
            "updatedAt": now
        }}
    )

    updated = await bookings_collection.find_one({"_id": ObjectId(booking_id)})
    return {
        "message": "Booking cancelled successfully. Slot is now available again.",
        "booking": booking_helper(updated)
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /bookings/{booking_id}/start
# Start a session: pending → active
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{booking_id}/start")
async def start_session(booking_id: str):

    booking = await _get_booking_or_404(booking_id)

    status = booking["status"]
    if status == "active":
        raise HTTPException(status_code=409, detail="Session is already active")
    if status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start a '{status}' booking. Only pending bookings can be started."
        )

    now = datetime.utcnow()

    await bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "status": "active",
            "start_time": now,
            "location_sharing_active": True,
            "updatedAt": now
        }}
    )

    updated = await bookings_collection.find_one({"_id": ObjectId(booking_id)})
    return {
        "message": "Session started successfully. Live tracking is now active.",
        "booking": booking_helper(updated)
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /bookings/{booking_id}/checkin
# Record check-in location for an active session
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{booking_id}/checkin")
async def checkin_session(booking_id: str, data: BookingCheckin):

    booking = await _get_booking_or_404(booking_id)

    if booking["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot check-in for a '{booking['status']}' session. Session must be active first."
        )
    if booking.get("checkin_time"):
        raise HTTPException(status_code=409, detail="Already checked in to this session")

    now = datetime.utcnow()

    await bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "checkin_time": now,
            "checkin_location_name": data.location_name,
            "checkin_lat": data.lat,
            "checkin_long": data.long,
            "updatedAt": now
        }}
    )

    updated = await bookings_collection.find_one({"_id": ObjectId(booking_id)})
    return {
        "message": f"Checked in at {data.location_name}",
        "checkin_time": str(now),
        "booking": booking_helper(updated)
    }


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /bookings/{booking_id}/location
# Update live location of companion or participant during active session
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/{booking_id}/location")
async def update_location(booking_id: str, data: LocationUpdate):

    booking = await _get_booking_or_404(booking_id)

    if booking["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail="Location sharing is only available during active sessions"
        )

    if data.user_id == booking["companion_user_id"]:
        location_field = "companion_location"
    elif data.user_id == booking["participant_user_id"]:
        location_field = "participant_location"
    else:
        raise HTTPException(status_code=403, detail="You are not part of this session")

    location_data = {
        "lat": data.lat,
        "long": data.long,
        "updated_at": str(datetime.utcnow())
    }

    await bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {location_field: location_data, "updatedAt": datetime.utcnow()}}
    )

    updated = await bookings_collection.find_one({"_id": ObjectId(booking_id)})
    return {
        "message": "Location updated",
        "updated_field": location_field,
        "booking": booking_helper(updated)
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /bookings/{booking_id}/end
# End an active session: active → completed
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{booking_id}/end")
async def end_session(booking_id: str):

    booking = await _get_booking_or_404(booking_id)

    status = booking["status"]
    if status == "completed":
        raise HTTPException(status_code=409, detail="Session is already completed")
    if status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot end a '{status}' session. Session must be active."
        )

    now = datetime.utcnow()
    start_time = booking.get("start_time")
    duration_seconds = int((now - start_time).total_seconds()) if start_time else None

    await bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "status": "completed",
            "end_time": now,
            "duration_seconds": duration_seconds,
            "location_sharing_active": False,
            "updatedAt": now
        }}
    )

    # Increment companion's total sessions count
    await companions_collection.update_one(
        {"user_id": booking["companion_user_id"]},
        {"$inc": {"total_sessions": 1}}
    )

    updated = await bookings_collection.find_one({"_id": ObjectId(booking_id)})

    hours = (duration_seconds // 3600) if duration_seconds else 0
    minutes = ((duration_seconds % 3600) // 60) if duration_seconds else 0

    return {
        "message": "Session ended successfully",
        "duration": f"{hours}h {minutes}m" if duration_seconds else None,
        "duration_seconds": duration_seconds,
        "next_step": f"Submit a review → POST /reviews",
        "booking": booking_helper(updated)
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /bookings/{booking_id}/sos
# Trigger SOS emergency alert during active session
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{booking_id}/sos")
async def trigger_sos(booking_id: str, data: SOSRequest):

    booking = await _get_booking_or_404(booking_id)

    if booking["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail="SOS can only be triggered during an active session"
        )

    if data.user_id not in [booking["companion_user_id"], booking["participant_user_id"]]:
        raise HTTPException(status_code=403, detail="You are not part of this session")

    now = datetime.utcnow()

    await bookings_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "sos_triggered": True,
            "sos_time": now,
            "sos_message": data.message,
            "sos_lat": data.lat,
            "sos_long": data.long,
            "sos_triggered_by": data.user_id,
            "updatedAt": now
        }}
    )

    updated = await bookings_collection.find_one({"_id": ObjectId(booking_id)})

    return {
        "message": "SOS alert triggered. Support team has been notified.",
        "sos_time": str(now),
        "booking": booking_helper(updated)
    }
