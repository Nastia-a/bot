import requests
import logging
import os

logger = logging.getLogger(__name__)

# Используем бесплатный API для получения информации
def get_video_info_api(url):
    """Get video info using external API"""
    try:
        # Извлекаем ID видео
        video_id = url.split('v=')[-1].split('&')[0]
        if 'youtu.be' in url:
            video_id = url.split('/')[-1].split('?')[0]
        
        # Используем invidious API (бесплатный, без авторизации)
        api_url = f"https://invidious.snopyta.org/api/v1/videos/{video_id}"
        
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', 'Unknown'),
                'duration': data.get('lengthSeconds', 0),
                'thumbnail': data.get('videoThumbnails', [{}])[0].get('url', ''),
                'uploader': data.get('author', 'Unknown')
            }
        else:
            raise Exception(f"API returned {response.status_code}")
            
    except Exception as e:
        logger.error(f"API error: {e}")
        raise Exception("Failed to get video info")
