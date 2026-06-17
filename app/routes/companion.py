import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.companion import CompanionSetup, CompanionUpdate
from app.models.companion import companion_mongo_schema, companion_helper
from app.config.db import companions_collection, users_collection
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/companions", tags=["companions"])

UPLOAD_DIR = "uploads"
PHOTOS_DIR = os.path.join(UPLOAD_DIR, "photos")
IDS_DIR = os.path.join(UPLOAD_DIR, "ids")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_ID_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_ID_SIZE_BYTES = 10 * 1024 * 1024     # 10 MB
MAX_PHOTOS = 3

VALID_DOCUMENT_TYPES = ["passport", "drivers_license", "national_id"]


def ensure_upload_dirs():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    os.makedirs(IDS_DIR, exist_ok=True)


def is_profile_complete(companion: dict) -> bool:
    return (
        bool(companion.get("bio"))
        and bool(companion.get("skills"))
        and companion.get("hourly_rate") is not None
        and len(companion.get("photos", [])) > 0
    )

# ─────────────────────────────────────────────
# GET /companions/get-all-campaion
# Get all companion profiles
# Must be defined BEFORE /{companion_id} so FastAPI
# doesn't treat "get-all-campaion" as an ObjectId param
# ─────────────────────────────────────────────
@router.get("/")
async def get_all_companions():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": {
                    "path": "$user",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]

        all_companions = await companions_collection.aggregate(
            pipeline
        ).to_list(length=None)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )

    return {
        "total": len(all_companions),
        "companions": [companion_helper(c) for c in all_companions]
    }


# ─────────────────────────────────────────────
# POST /companions/setup
# Create companion profile (bio, skills, hourly rate)
# ─────────────────────────────────────────────
@router.post("/setup")
async def setup_companion(data: CompanionSetup):

    # Validate user exists
    try:
        user = await users_collection.find_one({"_id": ObjectId(data.user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Block duplicate companion profile for same user
    existing = await companions_collection.find_one({"user_id": data.user_id})
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Companion profile already exists for this user. Use PUT /companions/{id} to update."
        )

    companion_data = companion_mongo_schema(data)
    result = await companions_collection.insert_one(companion_data)
    new_companion = await companions_collection.find_one({"_id": result.inserted_id})

    # Upgrade motive to "find and earn" if user was only "find"
    if user.get("motive") == "find":
        await users_collection.update_one(
            {"_id": ObjectId(data.user_id)},
            {"$set": {"motive": "find and earn", "updatedAt": datetime.utcnow()}}
        )

    return {
        "message": "Companion profile created successfully",
        "next_steps": [
            f"Upload photos → POST /companions/{str(new_companion['_id'])}/photos",
            f"Upload ID for verification → POST /companions/{str(new_companion['_id'])}/verify-id"
        ],
        "companion": companion_helper(new_companion),
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
        }
    }


# ─────────────────────────────────────────────
# PUT /companions/{companion_id}
# Update companion profile
# ─────────────────────────────────────────────
@router.put("/{companion_id}")
async def update_companion(companion_id: str, data: CompanionUpdate):

    try:
        companion = await companions_collection.find_one({"_id": ObjectId(companion_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid companion_id format")

    if not companion:
        raise HTTPException(status_code=404, detail="Companion profile not found")

    update_fields = {k: v for k, v in data.dict().items() if v is not None}

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    # Convert SkillEnum list to string values
    if "skills" in update_fields:
        update_fields["skills"] = [s.value for s in update_fields["skills"]]

    update_fields["updatedAt"] = datetime.utcnow()

    await companions_collection.update_one(
        {"_id": ObjectId(companion_id)},
        {"$set": update_fields}
    )

    updated = await companions_collection.find_one({"_id": ObjectId(companion_id)})

    # Re-check profile completeness
    complete = is_profile_complete(updated)
    if complete != updated.get("is_profile_complete"):
        await companions_collection.update_one(
            {"_id": ObjectId(companion_id)},
            {"$set": {"is_profile_complete": complete}}
        )
        updated["is_profile_complete"] = complete

    return {
        "message": "Companion profile updated successfully",
        "companion": companion_helper(updated)
    }


# ─────────────────────────────────────────────
# POST /companions/{companion_id}/photos
# Upload up to 3 profile photos
# ─────────────────────────────────────────────
@router.post("/{companion_id}/photos")
async def upload_photos(
    companion_id: str,
    photos: List[UploadFile] = File(...)
):
    ensure_upload_dirs()

    try:
        companion = await companions_collection.find_one({"_id": ObjectId(companion_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid companion_id format")

    if not companion:
        raise HTTPException(status_code=404, detail="Companion profile not found")

    if not photos:
        raise HTTPException(status_code=400, detail="No photos provided")

    current_photos = companion.get("photos", [])

    if len(current_photos) >= MAX_PHOTOS:
        raise HTTPException(
            status_code=400,
            detail=f"Already at maximum of {MAX_PHOTOS} photos. Delete one before uploading."
        )

    slots_remaining = MAX_PHOTOS - len(current_photos)
    if len(photos) > slots_remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Too many photos. You can only add {slots_remaining} more photo(s)."
        )

    saved_paths = []

    for photo in photos:
        # Validate content type
        if photo.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"'{photo.filename}' has unsupported type '{photo.content_type}'. Allowed: JPEG, PNG, WEBP"
            )

        content = await photo.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"'{photo.filename}' is empty")

        if len(content) > MAX_PHOTO_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"'{photo.filename}' exceeds the 5 MB size limit"
            )

        ext = (photo.filename or "photo.jpg").rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(PHOTOS_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        saved_paths.append(f"/uploads/photos/{filename}")

    updated_photos = current_photos + saved_paths
    complete = is_profile_complete({**companion, "photos": updated_photos})

    await companions_collection.update_one(
        {"_id": ObjectId(companion_id)},
        {
            "$set": {
                "photos": updated_photos,
                "is_profile_complete": complete,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    updated = await companions_collection.find_one({"_id": ObjectId(companion_id)})

    return {
        "message": f"{len(saved_paths)} photo(s) uploaded successfully",
        "uploaded": saved_paths,
        "total_photos": len(updated_photos),
        "is_profile_complete": complete,
        "companion": companion_helper(updated)
    }


# ─────────────────────────────────────────────
# DELETE /companions/{companion_id}/photos
# Remove a specific photo by URL
# ─────────────────────────────────────────────
@router.delete("/{companion_id}/photos")
async def delete_photo(companion_id: str, photo_url: str):

    try:
        companion = await companions_collection.find_one({"_id": ObjectId(companion_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid companion_id format")

    if not companion:
        raise HTTPException(status_code=404, detail="Companion profile not found")

    current_photos = companion.get("photos", [])

    if photo_url not in current_photos:
        raise HTTPException(status_code=404, detail="Photo not found in this companion's profile")

    # Delete file from disk
    filename = photo_url.split("/")[-1]
    file_path = os.path.join(PHOTOS_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    updated_photos = [p for p in current_photos if p != photo_url]
    complete = is_profile_complete({**companion, "photos": updated_photos})

    await companions_collection.update_one(
        {"_id": ObjectId(companion_id)},
        {
            "$set": {
                "photos": updated_photos,
                "is_profile_complete": complete,
                "updatedAt": datetime.utcnow()
            }
        }
    )

    updated = await companions_collection.find_one({"_id": ObjectId(companion_id)})

    return {
        "message": "Photo deleted successfully",
        "total_photos": len(updated_photos),
        "companion": companion_helper(updated)
    }


# ─────────────────────────────────────────────
# POST /companions/{companion_id}/verify-id
# Upload government ID for identity verification
# ─────────────────────────────────────────────
@router.post("/{companion_id}/verify-id")
async def upload_id_document(
    companion_id: str,
    id_document: UploadFile = File(...),
    document_type: str = Form(...)
):
    ensure_upload_dirs()

    try:
        companion = await companions_collection.find_one({"_id": ObjectId(companion_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid companion_id format")

    if not companion:
        raise HTTPException(status_code=404, detail="Companion profile not found")

    if document_type not in VALID_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document_type. Allowed values: {', '.join(VALID_DOCUMENT_TYPES)}"
        )

    if companion.get("id_verification_status") == "verified":
        raise HTTPException(
            status_code=400,
            detail="Identity is already verified. Upload not required."
        )

    if id_document.content_type not in ALLOWED_ID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{id_document.content_type}'. Allowed: JPEG, PNG, WEBP, PDF"
        )

    content = await id_document.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > MAX_ID_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="ID document exceeds the 10 MB size limit")

    # Remove old ID file from disk if it exists
    old_path = companion.get("id_document_path")
    if old_path:
        old_filename = old_path.split("/")[-1]
        old_file_path = os.path.join(IDS_DIR, old_filename)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    ext = (id_document.filename or "id.jpg").rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(IDS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    document_url = f"/uploads/ids/{filename}"

    await companions_collection.update_one(
        {"_id": ObjectId(companion_id)},
        {
            "$set": {
                "id_document_path": document_url,
                "id_document_type": document_type,
                "id_verification_status": "pending",
                "updatedAt": datetime.utcnow()
            }
        }
    )

    updated = await companions_collection.find_one({"_id": ObjectId(companion_id)})

    return {
        "message": "ID document uploaded. Verification is pending admin review.",
        "document_type": document_type,
        "verification_status": "pending",
        "companion": companion_helper(updated)
    }

# ─────────────────────────────────────────────
# GET /companions/{companion_id}
# Get full companion profile with user details
# ─────────────────────────────────────────────
@router.get("/{companion_id}")
async def get_companion_profile(companion_id: str):

    try:
        companion = await companions_collection.find_one({"_id": ObjectId(companion_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid companion_id format")

    if not companion:
        raise HTTPException(status_code=404, detail="Companion profile not found")

    user = await users_collection.find_one({"_id": ObjectId(companion.get("user_id"))})
    if not user:
        raise HTTPException(status_code=404, detail="Linked user account not found")

    return {
        "companion": companion_helper(companion),
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "gender": user.get("gender"),
            "dob": user.get("dob"),
            "address": user.get("address"),
            "motive": user.get("motive"),
        }
    }

