# ---- Base Image ----
FROM python:3.11-slim

ARG GITHUB_TOKEN

WORKDIR /app

# ---- System Dependencies + git + git-lfs ----
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    git \
    git-lfs \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# ---- Python Dependencies ----
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ---- Fetch Only the Model File from GitHub (LFS) ----
RUN git init model_repo \
    && cd model_repo \
    && git remote add origin https://${GITHUB_TOKEN}@github.com/Sami0009/Fit-Plant-Backend.git \
    && git config core.sparseCheckout true \
    && echo "models/efficientnetb3-PlantVillageDisease-weights.h5" >> .git/info/sparse-checkout \
    && git pull origin main \
    && git lfs pull \
    && mkdir -p /app/models \
    && mv models/efficientnetb3-PlantVillageDisease-weights.h5 /app/models/ \
    && cd .. && rm -rf model_repo

# ---- Copy the Rest of Your App ----
COPY . .

# ---- Run the App ----
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "1", \
     "--timeout", "180", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
