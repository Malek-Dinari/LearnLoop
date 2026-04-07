FROM python:3.12-slim

WORKDIR /app

# System deps: libgomp for PyMuPDF, gcc only if a wheel is missing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
