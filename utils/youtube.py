import yt_dlp
import os
import re
import logging
from config import Config

logger = logging.getLogger(__name__)

# Ensure download directory exists
os.makedirs(Config.DOWNLOAD_PATH, exist_ok=True)

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def get_video_info(url):
    """Get video information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown')
            }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise Exception("Failed to get video information")

def download_video(url, quality):
    """Download video with specified quality"""
    try:
        # Get video info for filename
        info = get_video_info(url)
        title = sanitize_filename(info['title'])
        
        # Format quality mapping
        quality_map = {
            '360': '360',
            '720': '720',
            '1080': '1080'
        }
        
        ydl_opts = {
            'format': f'bestvideo[height<={quality_map[quality]}]+bestaudio/best[height<={quality_map[quality]}]',
            'outtmpl': os.path.join(Config.DOWNLOAD_PATH, f'{title}_%(height)sp.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Handle different extensions
            if not os.path.exists(filename):
                # Try with .mp4 extension
                base, ext = os.path.splitext(filename)
                if ext != '.mp4':
                    mp4_filename = base + '.mp4'
                    if os.path.exists(mp4_filename):
                        filename = mp4_filename
            
            return filename
            
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise Exception(f"Failed to download video: {str(e)}")

def download_audio(url, format='mp3'):
    """Download audio in specified format"""
    try:
        # Get video info for filename
        info = get_video_info(url)
        title = sanitize_filename(info['title'])
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(Config.DOWNLOAD_PATH, f'{title}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Change extension to the chosen format
            base, _ = os.path.splitext(filename)
            filename = f"{base}.{format}"
            
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
