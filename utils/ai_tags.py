import google.generativeai as genai
import logging
import os
import asyncio
from config import Config

logger = logging.getLogger(__name__)

# Настройка Gemini AI
model = None
try:
    if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != 'your_gemini_api_key_here':
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        logger.info("✅ Gemini AI initialized successfully")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not found or invalid, AI features disabled")
except Exception as e:
    logger.error(f"❌ Failed to initialize Gemini: {e}")

async def generate_tags(video_title, video_description="", duration=0):
    """Generate hashtags and keywords for video using AI with timeout"""
    
    if not model:
        logger.warning("AI model not available")
        return None
    
    try:
        # Ограничиваем время выполнения AI запроса
        result = await asyncio.wait_for(
            _generate_tags_async(video_title, video_description, duration),
            timeout=10.0  # 10 секунд максимум
        )
        return result
        
    except asyncio.TimeoutError:
        logger.error("AI request timed out after 10 seconds")
        return None
    except Exception as e:
        logger.error(f"Error generating tags with AI: {e}")
        return None

async def _generate_tags_async(video_title, video_description, duration):
    """Actual AI generation function"""
    
    try:
        # Формируем короткий и понятный промпт
        prompt = f"""
        Generate 8-10 relevant hashtags for this YouTube video:
        
        Title: {video_title}
        
        Return ONLY hashtags separated by spaces, nothing else.
        Example: #tech #youtube #viral
        
        Make hashtags specific to the content.
        """
        
        # Запрашиваем у AI
        response = model.generate_content(prompt)
        
        # Извлекаем хэштеги
        text = response.text.strip()
        
        # Разбиваем на хэштеги
        hashtags = []
        for word in text.split():
            if word.startswith('#') and len(word) > 1:
                hashtags.append(word)
            elif word.startswith('#'):
                hashtags.append(word)
        
        # Если нет хэштегов, создаем из названия
        if not hashtags:
            words = video_title.lower().split()[:5]
            hashtags = ['#' + w for w in words if len(w) > 3]
        
        return {
            'hashtags': hashtags[:10],  # Максимум 10 тегов
            'keywords': [],
            'full_response': ' '.join(hashtags[:5])
        }
        
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return None

async def generate_tags_simple(video_title):
    """Simple tag generation without API (fallback)"""
    
    # Простая генерация тегов из названия
    import re
    words = re.sub(r'[^\w\s]', '', video_title).lower().split()
    
    # Убираем стоп-слова
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'of', 'is', 'it']
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Создаем хэштеги
    hashtags = ['#' + w for w in keywords[:5]]
    
    return {
        'hashtags': hashtags,
        'keywords': keywords[:5],
        'full_response': ' '.join(hashtags)
    }
