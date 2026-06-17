from datetime import datetime


def companion_mongo_schema(data) -> dict:
    return {
        "user_id": data.user_id,
        "bio": data.bio,
        "skills": [s.value for s in data.skills],
        "hourly_rate": data.hourly_rate,
        "photos": [],
        "id_document_path": None,
        "id_document_type": None,
        "id_verification_status": "not_submitted",
        "is_verified": False,
        "is_profile_complete": False,
        "is_active": True,
        "rating": 0.0,
        "total_reviews": 0,
        "total_sessions": 0,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }


def companion_helper(companion) -> dict:
    return {
        "id": str(companion["_id"]),
        "user_id": companion.get("user_id"),
        "bio": companion.get("bio"),
        "skills": companion.get("skills", []),
        "hourly_rate": companion.get("hourly_rate"),
        "photos": companion.get("photos", []),
        "id_document_type": companion.get("id_document_type"),
        "id_verification_status": companion.get("id_verification_status", "not_submitted"),
        "is_verified": companion.get("is_verified", False),
        "is_profile_complete": companion.get("is_profile_complete", False),
        "is_active": companion.get("is_active", True),
        "rating": companion.get("rating", 0.0),
        "total_reviews": companion.get("total_reviews", 0),
        "total_sessions": companion.get("total_sessions", 0),
        "createdAt": str(companion.get("createdAt")),
        "updatedAt": str(companion.get("updatedAt")),
    }
