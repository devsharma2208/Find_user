# Find User — API Documentation

Activity companion booking platform backend built with FastAPI + MongoDB.

---

## Tech Stack

- **Framework:** FastAPI (Python)
- **Database:** MongoDB (Motor async driver)
- **Auth:** JWT (python-jose)
- **Password Hashing:** bcrypt

---

## Base URL

```
http://localhost:8000
```

---

## API Progress Summary

| Category              | Completed | Pending | Total |
|-----------------------|-----------|---------|-------|
| Health                | 3         | 0       | 3     |
| Auth & User           | 3         | 0       | 3     |
| Slots                 | 4         | 0       | 4     |
| Companion Profile     | 7         | 0       | 7     |
| Companion Discovery   | 1         | 3       | 4     |
| Bookings & Sessions   | 9         | 0       | 9     |
| Reviews & Reports     | 0         | 2       | 2     |
| User Profile          | 0         | 4       | 4     |
| **Total**             | **27**    | **9**   | **36**|

---

---

# ✅ Completed APIs

---

## Health

| Method | Endpoint  | Description              |
|--------|-----------|--------------------------|
| GET    | `/live`   | Liveness check           |
| GET    | `/ready`  | Readiness + DB check     |
| GET    | `/health` | Full health status       |

---

## Auth & User

| Method | Endpoint            | Description                 |
|--------|---------------------|-----------------------------|
| POST   | `/signup`           | Register a new user         |
| POST   | `/login`            | Login with email & password |
| PUT    | `/update/{user_id}` | Update user profile fields  |

### POST `/signup`

**Request body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "number": "9876543210",
  "password": "secret123",
  "gender": "male",
  "dob": "1998-01-15",
  "aadhar": "1234-5678-9012",
  "address": {
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "currentlocation": "Andheri West",
    "lat": 19.1136,
    "long": 72.8697,
    "landmark": "Near Station"
  },
  "motive": "find"
}
```

> `motive` values: `find` | `earn` | `find and earn`
> Either `email` or `number` is required (both is fine too).

**Response:**
```json
{
  "message": "User created successfully",
  "token": "<jwt_token>",
  "user": { ... }
}
```

---

### POST `/login`

```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "token": "<jwt_token>"
}
```

---

### PUT `/update/{user_id}`

```json
{
  "name": "John Updated",
  "gender": "male",
  "dob": "1998-01-15",
  "about": "I love gym and hiking",
  "skills_interests": "Gym, Yoga, Running"
}
```

> All fields are optional. Only provided fields are updated.

---

## Slots

| Method | Endpoint                     | Description                             |
|--------|------------------------------|-----------------------------------------|
| POST   | `/slots/create`              | Create or toggle a slot's availability  |
| GET    | `/slots/available/{user_id}` | Get available slots for a companion     |
| POST   | `/slots/book`                | Book an available slot                  |
| GET    | `/slots/all/{user_id}`       | Get all slots created by a user         |

### POST `/slots/create`

```json
{
  "provider_user_id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "date": "2026-07-10",
  "time": "09:00"
}
```

> Toggle logic: if the slot already exists and is `available` → sets to `unavailable` (and vice versa). Cannot toggle a `booked` slot.

---

### GET `/slots/available/{user_id}`

```
GET /slots/available/{user_id}?start_date=2026-07-01&days=7
```

| Param        | Type | Default | Description                         |
|--------------|------|---------|-------------------------------------|
| `start_date` | date | today   | Start of date range (YYYY-MM-DD)    |
| `days`       | int  | 7       | Days to look ahead (1–30)           |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-07-10",
      "times": [
        { "slot_id": "abc123", "time": "09:00" },
        { "slot_id": "def456", "time": "11:00" }
      ]
    }
  ]
}
```

---

### POST `/slots/book`

```json
{
  "slot_id": "64f1a2b3c4d5e6f7a8b9c0d2",
  "participant_user_id": "64f1a2b3c4d5e6f7a8b9c0d3"
}
```

---

### GET `/slots/all/{user_id}`

Returns all slots (available / unavailable / booked) created by the provider, including participant details if booked.

---

## Companion Profile

| Method | Endpoint                            | Description                                    |
|--------|-------------------------------------|------------------------------------------------|
| GET    | `/companions/`                      | Get all companion profiles                     |
| POST   | `/companions/setup`                 | Create companion profile (bio, skills, rate)   |
| PUT    | `/companions/{companion_id}`        | Update bio / skills / hourly rate              |
| POST   | `/companions/{companion_id}/photos` | Upload up to 3 profile photos                  |
| DELETE | `/companions/{companion_id}/photos` | Delete a specific photo by URL                 |
| POST   | `/companions/{companion_id}/verify-id` | Upload government ID for verification       |
| GET    | `/companions/{companion_id}`        | Get single companion profile + user details    |

### POST `/companions/setup`

```json
{
  "user_id": "64f1a2b3c4d5e6f7a8b9c0d1",
  "bio": "Fitness enthusiast with 5+ years of experience. Certified personal trainer.",
  "skills": ["Gym Training", "Yoga", "Running"],
  "hourly_rate": 25
}
```

> Skills allowed: `Gym Training` `Yoga` `Running` `Travel` `Study` `Music` `Photography` `Cooking` `Adventure` `Hiking` `Meditation` `Nutrition` `Tech` `Coding` `Events` `Fitness`
> `hourly_rate` must be between $10 and $100.
> `bio` must be 20–500 characters.
> Creates companion profile and upgrades user motive to `find and earn` if previously `find`.

---

### PUT `/companions/{companion_id}`

```json
{
  "bio": "Updated bio here...",
  "skills": ["Travel", "Adventure"],
  "hourly_rate": 35
}
```

> All fields optional. Re-evaluates `is_profile_complete` after update.

---

### POST `/companions/{companion_id}/photos`

- **Content-Type:** `multipart/form-data`
- **Field name:** `photos` (supports multiple files in one request)
- **Allowed types:** JPEG, PNG, WEBP
- **Max size per photo:** 5 MB
- **Max total photos:** 3

---

### DELETE `/companions/{companion_id}/photos`

```
DELETE /companions/{companion_id}/photos?photo_url=/uploads/photos/abc.jpg
```

> Deletes the file from disk and removes it from the companion's photos array.

---

### POST `/companions/{companion_id}/verify-id`

- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `id_document` — file (JPEG / PNG / WEBP / PDF, max 10 MB)
  - `document_type` — `passport` | `drivers_license` | `national_id`

> Sets `id_verification_status` to `pending`. Cannot re-upload if already `verified`.

---

## Bookings & Sessions

All booking and session lifecycle endpoints live under `/bookings`.

**Session Status Flow:**
```
pending  →  active  →  completed
   └──────────────→  cancelled
```

| Method | Endpoint                            | Description                                      |
|--------|-------------------------------------|--------------------------------------------------|
| POST   | `/bookings`                         | Create a booking from an available slot          |
| GET    | `/bookings/user/{user_id}`          | Get all bookings for a user (upcoming + past)    |
| GET    | `/bookings/{booking_id}`            | Get single booking with full details             |
| POST   | `/bookings/{booking_id}/cancel`     | Cancel a pending booking (releases the slot)     |
| POST   | `/bookings/{booking_id}/start`      | Start session: `pending` → `active`              |
| POST   | `/bookings/{booking_id}/checkin`    | Record check-in location for active session      |
| PATCH  | `/bookings/{booking_id}/location`   | Update live location during active session       |
| POST   | `/bookings/{booking_id}/end`        | End session: `active` → `completed`              |
| POST   | `/bookings/{booking_id}/sos`        | Trigger SOS Emergency alert                      |

---

### POST `/bookings`

```json
{
  "slot_id": "64f1a2b3c4d5e6f7a8b9c0d2",
  "participant_user_id": "64f1a2b3c4d5e6f7a8b9c0d3",
  "activity": "Gym Training"
}
```

> Validates slot is available, prevents self-booking, prevents double-booking same time slot. Locks the slot to `booked`.

---

### GET `/bookings/user/{user_id}`

**Response:**
```json
{
  "user_id": "...",
  "total_upcoming": 2,
  "total_past": 1,
  "upcoming": [
    {
      "booking_id": "...",
      "activity": "Gym Training",
      "date": "2026-04-24",
      "time": "09:00",
      "status": "pending",
      "role": "seeker",
      "companion": {
        "user_id": "...",
        "name": "Sarah Chen",
        "photo": "/uploads/photos/abc.jpg",
        "rating": 4.9,
        "hourly_rate": 25,
        "is_verified": true
      }
    }
  ],
  "past": [
    {
      "booking_id": "...",
      "activity": "Study Session",
      "date": "2026-04-20",
      "status": "completed",
      "can_review": true,
      "companion": { ... }
    }
  ]
}
```

---

### POST `/bookings/{booking_id}/cancel`

```json
{
  "reason": "Plans changed"
}
```

> Only cancels `pending` bookings. Releases the slot back to `available`.

---

### POST `/bookings/{booking_id}/checkin`

```json
{
  "location_name": "Downtown Gym",
  "lat": 19.1136,
  "long": 72.8697
}
```

> Session must be `active`. Can only check-in once per session.

---

### PATCH `/bookings/{booking_id}/location`

```json
{
  "user_id": "64f1a2b3c4d5e6f7a8b9c0d3",
  "lat": 19.1140,
  "long": 72.8700
}
```

> Updates `companion_location` or `participant_location` based on which user is calling. Session must be `active`.

---

### POST `/bookings/{booking_id}/sos`

```json
{
  "user_id": "64f1a2b3c4d5e6f7a8b9c0d3",
  "lat": 19.1136,
  "long": 72.8697,
  "message": "I feel unsafe"
}
```

> Session must be `active`. Caller must be part of the session (companion or participant).

---

---

# ❌ Pending APIs

> Required by Figma design. Not yet implemented.

---

## Companion Discovery

| Method | Endpoint                  | Description                                        | Priority   |
|--------|---------------------------|----------------------------------------------------|------------|
| GET    | `/companions/recommended` | Recommended companions for Home screen             | 🔴 High    |
| GET    | `/companions/trending`    | Trending companions for Explore screen             | 🔴 High    |
| GET    | `/companions/search`      | Search by activity, location, name                 | 🔴 High    |

### GET `/companions/search` (expected params)
```
GET /companions/search?q=gym&category=Gym Training&lat=19.1&long=72.8&limit=20&skip=0
```

| Param      | Type   | Description                         |
|------------|--------|-------------------------------------|
| `q`        | string | Free-text search (name / bio)       |
| `category` | string | Filter by skill/activity            |
| `lat`      | float  | User latitude for distance sort     |
| `long`     | float  | User longitude for distance sort    |
| `limit`    | int    | Results per page (default 20)       |
| `skip`     | int    | Offset for pagination (default 0)   |

---

## Reviews & Reports

| Method | Endpoint    | Description                                    | Priority   |
|--------|-------------|------------------------------------------------|------------|
| POST   | `/reviews`  | Submit star rating, review text, and tip       | 🔴 High    |
| POST   | `/reports`  | Report an issue with a companion or session    | 🟡 Medium  |

### POST `/reviews` (expected body)
```json
{
  "booking_id": "...",
  "reviewer_id": "...",
  "companion_id": "...",
  "rating": 5,
  "review_text": "Amazing session! Very professional.",
  "tip": 10
}
```

### POST `/reports` (expected body)
```json
{
  "booking_id": "...",
  "reporter_id": "...",
  "reported_user_id": "...",
  "reason": "Inappropriate behavior",
  "description": "..."
}
```

---

## User Profile

| Method | Endpoint                           | Description                       | Priority  |
|--------|------------------------------------|-----------------------------------|-----------|
| GET    | `/users/{user_id}`                 | Get profile with stats            | 🔴 High   |
| PUT    | `/users/{user_id}/payment-methods` | Add / update payment methods      | 🟡 Medium |
| PUT    | `/users/{user_id}/notifications`   | Update notification preferences   | 🟢 Low    |
| PUT    | `/users/{user_id}/privacy`         | Update privacy & safety settings  | 🟢 Low    |

### GET `/users/{user_id}` (expected response)
```json
{
  "id": "...",
  "name": "John Doe",
  "member_since": "Jan 2026",
  "is_online": true,
  "stats": {
    "sessions": 24,
    "rating": 4.8,
    "earned": 1250
  }
}
```

---

---

# Known Issues

| # | Issue | Status |
|---|-------|--------|
| 1 | **No JWT auth middleware** — Token is generated on login/signup but never verified on any route. All endpoints are publicly accessible. | 🔴 Open |
| 2 | **`auth.py` is empty** — Auth routes live in `user.py`. The file is unused dead code. | 🟡 Minor |
| 3 | **Motive field bug** — `models/user.py` line 25 does `user.motive.motive` but `motive` is already a string enum, not an object. Causes `AttributeError` on signup. | 🔴 Open |

---

# Folder Structure

```
app/
├── config/
│   └── db.py                   # MongoDB connection + all collections
├── models/
│   ├── user.py                 # User mongo schema helper
│   ├── slot.py                 # Slot mongo schema + helper
│   ├── companion.py            # Companion mongo schema + helper
│   ├── booking.py              # Booking mongo schema + helper
│   └── activity.py             # (unused)
├── routes/
│   ├── user.py                 # POST /signup, POST /login, PUT /update
│   ├── slot.py                 # Slot CRUD + availability + booking
│   ├── companion.py            # Companion profile setup + photos + ID
│   ├── booking.py              # Booking create + full session lifecycle
│   ├── auth.py                 # (empty — unused)
│   └── activity.py             # (pending)
├── schemas/
│   ├── user.py                 # Pydantic: UserSignup, UserLogin, UserUpdate
│   ├── slot.py                 # Pydantic: SlotCreate, SlotBook
│   ├── companion.py            # Pydantic: CompanionSetup, CompanionUpdate
│   ├── booking.py              # Pydantic: BookingCreate, SOSRequest, etc.
│   └── activity.py             # (pending)
├── services/
│   └── recommendation.py       # (pending — needed for /recommended)
├── utils/
│   ├── hash.py                 # bcrypt password hashing
│   └── jwt.py                  # JWT token create/verify
└── main.py                     # App entry, lifespan, routers, static files
```

---

# Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload

# Interactive API docs
http://localhost:8000/docs

# Static uploads served at
http://localhost:8000/uploads/photos/<filename>
http://localhost:8000/uploads/ids/<filename>
```

---

# MongoDB Collections

| Collection    | Purpose                                      |
|---------------|----------------------------------------------|
| `users`       | All user accounts (seekers + companions)     |
| `slots`       | Availability slots created by companions     |
| `companions`  | Companion profile data (bio, photos, rate)   |
| `bookings`    | Bookings + full session lifecycle            |
| `activities`  | (pending)                                    |
| `subscriptions` | (pending)                                  |

