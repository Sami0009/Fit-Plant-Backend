from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from .database import engine, Base, SessionLocal
from .routers.users import router
from .routers.tasks import router as tasks_router
from .routers.predictions import router as predictions_router
from .routers.reports import router as reports_router
from .routers.dashboard import router as dashboard_router
from .routers.auth import router as auth_router
from .routers.workers import router as workers_router
from .dependencies import get_db

app = FastAPI()
origins = [
    "https://plant-disease-portal-r4b2.vercel.app",   # your Vercel frontend
    "https://plantlens.online",
    "https://www.plantlens.online",
    "https://api.plantlens.online",
    "http://localhost:8000",                         # optional for local dev
]
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API is running"}

# Mount static files for uploads
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Mount static files for processed images
processed_dir = os.path.join(os.path.dirname(__file__), "..", "processed_images")
if os.path.exists(processed_dir):
    app.mount("/processed_images", StaticFiles(directory=processed_dir), name="processed_images")

app.include_router(router, prefix="/api", tags=["users"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(predictions_router, prefix="/api", tags=["predictions"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(workers_router, prefix="/api", tags=["workers"])
