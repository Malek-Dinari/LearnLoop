FROM python:3.12-slim

WORKDIR /app

# System deps: libgomp for PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Create uploads directory and ensure entrypoint is executable
RUN mkdir -p uploads && chmod +x entrypoint.sh

EXPOSE 8000

# Railway injects PORT env var — honour it, fall back to 8000
CMD ["sh", "-c", "./entrypoint.sh"]
