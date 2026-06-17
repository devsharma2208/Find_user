import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("⚠️  MONGO_URI environment variable is not set")

# Create client — short timeouts so a bad connection fails fast instead of
# hanging the app's startup (which would otherwise delay port binding on
# platforms like Render and trigger a port-scan timeout)
client = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
)

# Use DB name from your URI (findUser)
db = client["findUser"]

# Collections
users_collection = db["users"]
activities_collection = db["activities"]
subscriptions_collection = db["subscriptions"]
slots_collection = db["slots"]
companions_collection = db["companions"]
bookings_collection = db["bookings"]


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