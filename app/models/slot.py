from datetime import datetime


def slot_mongo_schema(slot) -> dict:
    return {
        "provider_user_id": slot.provider_user_id,
        "participant_user_id": None,
        "date": slot.date.isoformat(),
        "time": slot.time,
        "status": "available",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }


def slot_helper(slot) -> dict:
    return {
        "id": str(slot["_id"]),
        "provider_user_id": str(slot.get("provider_user_id")),
        "participant_user_id": str(slot.get("participant_user_id")) if slot.get("participant_user_id") else None,
        "date": slot.get("date"),
        "time": slot.get("time"),
        "status": slot.get("status"),
        "createdAt": slot.get("createdAt"),
        "updatedAt": slot.get("updatedAt"),
    }
