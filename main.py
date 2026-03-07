from app.main import app
from fastapi.middleware.cors import CORSMiddleware
import os

# ----------------------
# CORS setup
# ----------------------
origins = [
    "https://plant-disease-portal-r4b2.vercel.app",   # your Vercel frontend
    "https://plantlens.online",
    "https://www.plantlens.online",
    "https://api.plantlens.online",
    "http://localhost:8000",                         # optional for local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],    # allow headers like Content-Type, Authorization
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
