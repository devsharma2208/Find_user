from datetime import datetime


def booking_mongo_schema(slot: dict, participant_user_id: str, activity: str = None) -> dict:
    return {
        "slot_id": str(slot["_id"]),
        "companion_user_id": slot["provider_user_id"],
        "participant_user_id": participant_user_id,
        "activity": activity,
        "date": slot["date"],
        "time": slot["time"],
        "status": "pending",       # pending | active | completed | cancelled
        "checkin_time": None,
        "checkin_location_name": None,
        "checkin_lat": None,
        "checkin_long": None,
        "start_time": None,
        "end_time": None,
        "duration_seconds": None,
        "companion_location": None,
        "participant_location": None,
        "location_sharing_active": False,
        "sos_triggered": False,
        "sos_time": None,
        "sos_message": None,
        "sos_lat": None,
        "sos_long": None,
        "sos_triggered_by": None,
        "cancel_reason": None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }


def booking_helper(booking: dict) -> dict:
    return {
        "id": str(booking["_id"]),
        "slot_id": booking.get("slot_id"),
        "companion_user_id": booking.get("companion_user_id"),
        "participant_user_id": booking.get("participant_user_id"),
        "activity": booking.get("activity"),
        "date": booking.get("date"),
        "time": booking.get("time"),
        "status": booking.get("status"),
        "checkin_time": str(booking["checkin_time"]) if booking.get("checkin_time") else None,
        "checkin_location_name": booking.get("checkin_location_name"),
        "checkin_lat": booking.get("checkin_lat"),
        "checkin_long": booking.get("checkin_long"),
        "start_time": str(booking["start_time"]) if booking.get("start_time") else None,
        "end_time": str(booking["end_time"]) if booking.get("end_time") else None,
        "duration_seconds": booking.get("duration_seconds"),
        "companion_location": booking.get("companion_location"),
        "participant_location": booking.get("participant_location"),
        "location_sharing_active": booking.get("location_sharing_active", False),
        "sos_triggered": booking.get("sos_triggered", False),
        "sos_time": str(booking["sos_time"]) if booking.get("sos_time") else None,
        "sos_message": booking.get("sos_message"),
        "sos_lat": booking.get("sos_lat"),
        "sos_long": booking.get("sos_long"),
        "cancel_reason": booking.get("cancel_reason"),
        "createdAt": str(booking.get("createdAt")),
        "updatedAt": str(booking.get("updatedAt")),
    }
