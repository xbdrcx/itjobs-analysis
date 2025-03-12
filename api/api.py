from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid, time

app = FastAPI()

# Allow access from any origin (adjust as necessary)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your Streamlit domain here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use in-memory storage for simplicity (replace with database in production)
user_data = {
    "total_visits": 0,
    "unique_users": set(),
    "current_users": 0,
}

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

# Use in-memory storage for simplicity (replace with database in production)
user_data = {
    "total_visits": 0,
    "unique_users": set(),
    "current_users": 0,
}

# In-memory session tracking (replace with more persistent storage in production)
user_sessions = {}

@app.get("/track_visit")
async def track_visit(request: Request):
    # Increment total visits
    user_data["total_visits"] += 1
    
    # Track unique users via user-agent, IP, or session ID (using UUID for simplicity)
    user_id = str(uuid.uuid4())  # Generate a unique identifier for each user visit
    user_data["unique_users"].add(user_id)

    # Track current users (naive method using user-agent or session)
    user_data["current_users"] += 1

    # Save session (track that this user visited)
    user_sessions[user_id] = time.time()

    # Simulate delay for tracking (could be replaced with actual database operations)
    time.sleep(0.5)  # Simulate processing time

    return JSONResponse(content={
        "total_visits": user_data["total_visits"],
        "unique_users": len(user_data["unique_users"]),
        "current_users": user_data["current_users"]
    })

@app.get("/track_exit")
async def track_exit(request: Request):
    # Track exit (remove user session)
    user_id = request.cookies.get("user_id")

    if user_id and user_id in user_sessions:
        user_data["current_users"] -= 1
        del user_sessions[user_id]
        return {"message": "Exit tracked"}
    return {"message": "No session found"}
