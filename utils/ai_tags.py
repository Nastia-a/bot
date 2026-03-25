import google.generativeai as genai
import logging
import os
from config import Config

logger = logging.getLogger(__name__)

# Настройка Gemini AI
try:
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini AI initialized successfully")
    else:
        logger.warning("GEMINI_API_KEY not found, AI features disabled")
        model = None
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {e}")
    model = None

async def generate_tags(video_title, video_description="", duration=0):
    """Generate hashtags and keywords for video using AI"""
    
    if not model:
        logger.warning("AI model not available")
        return None
    
    try:
        # Формируем промпт для AI
        prompt = f"""
        You are a social media marketing expert. Generate relevant hashtags and keywords for this YouTube video:
        
        Title: {video_title}
        Description: {video_description[:500]}...
        Duration: {duration} seconds
        
        Please provide:
        1. 10-15 relevant hashtags (with #)
        2. 5-7 keywords (without #)
        
        Format your response like this:
        HASHTAGS: #tag1 #tag2 #tag3
        KEYWORDS: keyword1, keyword2, keyword3
        
        Make hashtags specific to the content, popular but not overly generic.
        """
        
        # Запрашиваем у AI
        response = model.generate_content(prompt)
        
        # Парсим ответ
        text = response.text
        
        # Извлекаем хэштеги
        hashtags = []
        keywords = []
        
        lines = text.split('\n')
        for line in lines:
            if line.startswith('HASHTAGS:'):
                hashtags = line.replace('HASHTAGS:', '').strip().split(' ')
            elif line.startswith('KEYWORDS:'):
                keywords = line.replace('KEYWORDS:', '').strip().split(', ')
        
        return {
            'hashtags': hashtags[:15],  # Максимум 15 тегов
            'keywords': keywords[:7],    # Максимум 7 ключевых слов
            'full_response': text
        }
        
    except Exception as e:
        logger.error(f"Error generating tags with AI: {e}")
        return None

async def generate_tags_simple(video_title):
    """Simple tag generation without API (fallback)"""
    
    # Простая генерация тегов из названия
    words = video_title.lower().split()
    
    # Очищаем слова
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with']
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Создаем хэштеги
    hashtags = ['#' + w for w in keywords[:5]]
    
    return {
        'hashtags': hashtags,
        'keywords': keywords[:5],
        'full_response': ' '.join(hashtags)
    }
