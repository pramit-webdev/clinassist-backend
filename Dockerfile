FROM python:3.10-slim

# Avoid interactive installs
ENV DEBIAN_FRONTEND=noninteractive

# System deps required by FAISS + Torch
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the repo
COPY . .

# Hugging Face Spaces expects port 7860
EXPOSE 7860

# Start FastAPI
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
