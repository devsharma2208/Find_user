import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from app.config.db import connect_db, close_db, users_collection, slots_collection, companions_collection, bookings_collection
from app.routes.user import router as user_router
from app.routes.slot import router as slot_router
from app.routes.companion import router as companion_router
from app.routes.booking import router as booking_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    try:
        await connect_db()
        await users_collection.create_index("email", unique=True)
        await slots_collection.create_index(
            [("provider_user_id", 1), ("date", 1), ("time", 1), ("status", 1)]
        )
        await companions_collection.create_index("user_id", unique=True)
        await bookings_collection.create_index(
            [("participant_user_id", 1), ("date", 1), ("time", 1), ("status", 1)]
        )
        await bookings_collection.create_index(
            [("companion_user_id", 1), ("status", 1)]
        )
        app.state.db_connected = True
        print("✅ Database connected successfully")
    except Exception as e:
        app.state.db_connected = False
        print("❌ Database connection failed:", str(e))

    yield

    # ── Shutdown ──
    if app.state.db_connected:
        await close_db()
        print("🔌 Database disconnected")


app = FastAPI(lifespan=lifespan)
app.state.db_connected = False

# ── Static files (uploaded photos & ID documents) ──
os.makedirs("uploads/photos", exist_ok=True)
os.makedirs("uploads/ids", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ──
app.include_router(user_router)
app.include_router(slot_router)
app.include_router(companion_router)
app.include_router(booking_router)


# ── Health APIs ──
@app.get("/live")
async def live():
    return {"status": "alive"}


@app.get("/ready")
async def ready(request: Request):
    if not request.app.state.db_connected:
        raise HTTPException(
            status_code=503, detail={"status": "error", "database": "disconnected"}
        )
    try:
        await users_collection.database.command("ping")
        return {"status": "ready", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503, detail={"status": "error", "database": "unreachable"}
        )


@app.get("/health")
async def health(request: Request):
    if not request.app.state.db_connected:
        return {"status": "error", "database": "disconnected"}
    try:
        await users_collection.database.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "error", "database": "unreachable"}
