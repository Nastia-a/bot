import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50))  # MB
    DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', 'downloads')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Добавляем AI ключ
    # Video formats
    VIDEO_QUALITIES = {
        '360p': '360',
        '720p': '720',
        '1080p': '1080'
    }
    
    # Audio formats
    AUDIO_FORMATS = {
        'mp3': 'mp3',
        'm4a': 'm4a'
    }
    
    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN not found in environment variables")
        if not cls.GEMINI_API_KEY:
            print("⚠️  Warning: GEMINI_API_KEY not set. AI features will be disabled.")
