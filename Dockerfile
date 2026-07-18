FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install build dependencies just in case numpy-stl/pillow need compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY src/requirements.txt /app/src/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r src/requirements.txt

# Copy application source code
COPY src/ /app/src/

# Expose server port
EXPOSE 8000

# Start FastAPI server via uvicorn
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
