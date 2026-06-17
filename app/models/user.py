from datetime import datetime


def user_mongo_schema(user) -> dict:
    return {
        "name": user.name,
        "number": user.number,
        "email": user.email,
        "password": user.password,
        "aadhar": user.aadhar,
        "gender": user.gender,
        "dob": user.dob,
        "address": {
            "city": user.address.city,
            "state": user.address.state,
            "country": user.address.country,
            "currentlocation": user.address.currentlocation,
            "lat": user.address.lat,
            "long": user.address.long,
            "landmark": user.address.landmark,
        },
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "isActive": True,
        "motive": user.motive.motive,
        "role": user.role
    }
