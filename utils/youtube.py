import yt_dlp
import os
import re
import logging
from config import Config

logger = logging.getLogger(__name__)

os.makedirs(Config.DOWNLOAD_PATH, exist_ok=True)

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def get_video_info(url):
    """Get video information without downloading"""
    logger.info(f"Getting info for: {url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': False,
        'extract_flat': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'geo_bypass': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("No video info received")
            
            result = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'formats': info.get('formats', [])  # Сохраняем доступные форматы
            }
            
            logger.info(f"Success! Title: {result['title']}, Duration: {result['duration']}s")
            return result
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise Exception(f"Failed to get video information: {str(e)}")

def download_video(url, quality):
    """Download video with specified quality"""
    try:
        # Сначала получаем информацию о видео
        video_info = get_video_info(url)
        title = sanitize_filename(video_info['title'])
        
        # Карта качества для выбора формата
        quality_map = {
            '360': '360',
            '720': '720',
            '1080': '1080'
        }
        
        target_height = quality_map.get(quality, '720')
        
        # Обновленные настройки для yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
            'outtmpl': os.path.join(Config.DOWNLOAD_PATH, f'{title}.%(ext)s'),
            'merge_output_format': 'mp4',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'geo_bypass': True,
            # Новый способ выбора формата
            'format': f'bestvideo[height<={target_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={target_height}]/best',
            'format_sort': ['res', 'codec:avc:m4a'],  # Сортировка форматов
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        logger.info(f"Downloading video with quality {quality}p")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Проверяем существование файла
            if not os.path.exists(filename):
                # Пробуем другие расширения
                base, _ = os.path.splitext(filename)
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = base + ext
                    if os.path.exists(test_file):
                        filename = test_file
                        logger.info(f"Found file: {filename}")
                        break
            
            if not os.path.exists(filename):
                raise Exception("Downloaded file not found")
            
            logger.info(f"Download complete: {filename}")
            return filename
            
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise Exception(f"Failed to download video: {str(e)}")

def download_audio(url, format='mp3'):
    """Download audio in specified format"""
    try:
        video_info = get_video_info(url)
        title = sanitize_filename(video_info['title'])
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(Config.DOWNLOAD_PATH, f'{title}.%(ext)s'),
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'geo_bypass': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '192',
            }],
        }
        
        logger.info(f"Downloading audio as {format.upper()}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Меняем расширение на нужный формат
            base, _ = os.path.splitext(filename)
            filename = f"{base}.{format}"
            
            if not os.path.exists(filename):
                raise Exception(f"Audio file not found: {filename}")
            
            logger.info(f"Audio download complete: {filename}")
            return filename
            
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        raise Exception(f"Failed to download audio: {str(e)}")

def cleanup_file(filepath):
    """Delete file after sending"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted file: {filepath}")
    except Exception as e:
        logger.error(f"Error deleting file {filepath}: {e}")
