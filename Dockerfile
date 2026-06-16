FROM python:3.12-slim

WORKDIR /app

# Install dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (no db file — that lives on the mounted PVC)
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
COPY assets/ assets/
COPY sharpei.py .

# Persistent data directory for SQLite db
RUN mkdir -p /data

EXPOSE 8000

CMD ["python", "sharpei.py", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
