FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем последнюю версию yt-dlp
RUN pip install --upgrade pip && \
    pip install --upgrade yt-dlp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

CMD ["python", "main.py"]
