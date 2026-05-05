import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Create client
client = AsyncIOMotorClient(MONGO_URI)

# Use DB name from your URI (findUser)
db = client["findUser"]

# Collections
users_collection = db["users"]
activities_collection = db["activities"]
subscriptions_collection = db["subscriptions"]


# ✅ Test Connection
async def connect_db():
    try:
        await client.admin.command("ping")
        print("✅ MongoDB Atlas Connected")
    except Exception as e:
        print("❌ Connection Error:", e)


# ✅ Close Connection
async def close_db():
    client.close()