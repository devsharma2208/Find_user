from fastapi import FastAPI, HTTPException, Request
from app.config.db import connect_db, close_db, users_collection
from app.routes.user import router as user_router  # ✅ ADD THIS

app = FastAPI()

app.state.db_connected = False


# ================= STARTUP =================
@app.on_event("startup")
async def startup():
    try:
        await connect_db()
        await users_collection.create_index("email", unique=True)

        app.state.db_connected = True
        print("✅ Database connected successfully")

    except Exception as e:
        app.state.db_connected = False
        print("❌ Database connection failed:", str(e))


# ================= SHUTDOWN =================
@app.on_event("shutdown")
async def shutdown():
    if app.state.db_connected:
        await close_db()
        print("🔌 Database disconnected")


# ================= ROUTES =================
app.include_router(user_router)  # ✅ THIS LINE IS IMPORTANT


# ================= HEALTH APIs =================
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
    except:
        return {"status": "error", "database": "unreachable"}
