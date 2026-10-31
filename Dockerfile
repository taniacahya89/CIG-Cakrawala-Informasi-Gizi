
# Python 3.12 untuk CIG
FROM python:3.12-slim-bookworm

WORKDIR /app

# Konfigurasi Python dan Ultralytics
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    YOLO_CONFIG_DIR=/tmp/ultralytics

# Library sistem untuk OpenCV / YOLO
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Instal PyTorch khusus CPU, tanpa CUDA
RUN python -m pip install --no-cache-dir \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Instal dependensi CIG
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Salin source code
COPY . .

EXPOSE 8080

# Jalankan Flask menggunakan Gunicorn
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 180 run:app"]
