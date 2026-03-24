FROM python:3.10-slim

WORKDIR /app

# Устанавливаем ffmpeg и зависимости
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    ca-certificates \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Обновляем yt-dlp до последней версии
RUN pip install --upgrade pip && \
    pip install --upgrade yt-dlp

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем папку для загрузок
RUN mkdir -p downloads

# Проверяем установку
RUN python -c "import yt_dlp; print(f'yt-dlp version: {yt_dlp.version.__version__}')"

# Запускаем бота
CMD ["python", "main.py"]
