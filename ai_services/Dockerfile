FROM python:3.10-slim

WORKDIR /app

# Install system dependencies + build tools for insightface
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    g++ \
    gcc \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data

# Use Railway's dynamic PORT
EXPOSE 8000

CMD ["python", "-c", "import os, uvicorn; port = int(os.environ.get('PORT', 8000)); uvicorn.run('app.main:app', host='0.0.0.0', port=port)"]