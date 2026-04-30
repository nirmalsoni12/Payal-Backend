# Base image
FROM python:3.11-slim

# System dependencies (OCR + Barcode)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libzbar0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Work directory
WORKDIR /app

# Copy files
COPY . .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Port expose
EXPOSE 10000

# Run server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
