from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import timedelta
import os
from .database import engine, Base, SessionLocal
from .crud.user import authenticate_user
from .auth.auth import create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .schemas.user import Token, User
from .routers.users import router
from .routers.tasks import router as tasks_router
from .routers.predictions import router as predictions_router
from .routers.reports import router as reports_router
from .dependencies import get_db

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "uploads")), name="uploads")

app.include_router(router, prefix="/api", tags=["users"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(predictions_router, prefix="/api", tags=["predictions"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user