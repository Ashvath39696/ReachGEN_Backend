# --------------------------------------------------------
# BUILDER STAGE — Install dependencies
# --------------------------------------------------------
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install OS-level deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------
# RUNTIME STAGE — lightweight image
# --------------------------------------------------------
FROM python:3.10-slim

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your full backend code
COPY . /app

# Expose FastAPI port
EXPOSE 8000

# Environment (optional but recommended)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Start FastAPI with uvicorn
CMD ["uvicorn", "api.api_main:app", "--host", "0.0.0.0", "--port", "8000"]

