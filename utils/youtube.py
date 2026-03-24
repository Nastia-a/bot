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
    
    # Настройки для обхода PO Token требований
    ydl_opts = {
        'quiet': True,
        'no_warnings': False,
        'ignoreerrors': True,
        'extract_flat': False,
        'geo_bypass': True,
        # Используем только web клиент, который требует меньше токенов
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],  # Используем web вместо android
                'player_skip': ['webpage', 'configs', 'js'],  # Пропускаем проблемные части
            }
        },
        'format': 'best[height<=720]/best',  # Простой формат
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            }
            
            logger.info(f"Success! Title: {result['title']}")
            return result
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        
        # Вторая попытка с другими настройками
        try:
            logger.info("Trying alternative method...")
            alt_opts = {
                'quiet': True,
                'no_warnings': False,
                'ignoreerrors': True,
                'geo_bypass': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                        'player_skip': ['webpage', 'configs'],
                    }
                },
                'format': 'best',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            with yt_dlp.YoutubeDL(alt_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', 'Unknown')
                    }
        except Exception as e2:
            logger.error(f"Alternative method failed: {e2}")
            
        raise Exception("Failed to get video information. Try again later.")

def download_video(url, quality):
    """Download video with specified quality"""
    try:
        video_info = get_video_info(url)
        title = sanitize_filename(video_info['title'])
        
        quality_map = {
            '360': '360',
            '720': '720',
            '1080': '1080'
        }
        
        target_height = quality_map.get(quality, '720')
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
            'ignoreerrors': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'format': f'best[height<={target_height}]/best',
            'outtmpl': os.path.join(Config.DOWNLOAD_PATH, f'{title}.%(ext)s'),
            'merge_output_format': 'mp4',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        logger.info(f"Downloading video with quality {quality}p")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Проверяем существование файла
            if not os.path.exists(filename):
                base, _ = os.path.splitext(filename)
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = base + ext
                    if os.path.exists(test_file):
                        filename = test_file
                        break
            
            if not os.path.exists(filename):
                # Пробуем найти любой видеофайл
                files = [f for f in os.listdir(Config.DOWNLOAD_PATH) if f.startswith(title)]
                if files:
                    filename = os.path.join(Config.DOWNLOAD_PATH, files[0])
                else:
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
            'ignoreerrors': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(Config.DOWNLOAD_PATH, f'{title}.%(ext)s'),
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
