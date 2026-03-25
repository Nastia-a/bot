import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
from utils.youtube import download_video, download_audio, get_video_info, cleanup_file
from utils.ai_tags import generate_tags, generate_tags_simple

logger = logging.getLogger(__name__)

user_videos = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    message = update.message
    text = message.text
    
    if 'youtube.com' in text or 'youtu.be' in text:
        await process_youtube_url(update, context, text)
    else:
        await message.reply_text(
            "❌ Пожалуйста, отправь корректную ссылку на YouTube видео.\n"
            "Пример: https://www.youtube.com/watch?v=...\n\n"
            "Используй /help для справки."
        )

async def process_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Process YouTube URL and show format selection"""
    message = update.message
    user_id = update.effective_user.id
    
    processing_msg = await message.reply_text(
        "🔍 Получаю информацию о видео..."
    )
    
    try:
        # Get video info
        video_info = get_video_info(url)
        
        # Генерируем теги с помощью ИИ
        ai_msg = await message.reply_text(
            "🤖 ИИ анализирует видео и генерирует теги..."
        )
        
        tags = None
        if Config.GEMINI_API_KEY:
            tags = await generate_tags(
                video_info['title'], 
                video_info.get('description', ''),
                video_info.get('duration', 0)
            )
        else:
            tags = await generate_tags_simple(video_info['title'])
        
        # Store video info for this user
        user_videos[user_id] = {
            'url': url,
            'title': video_info['title'],
            'duration': video_info['duration'],
            'uploader': video_info.get('uploader', 'YouTube'),
            'tags': tags  # Сохраняем теги
        }
        
        # Create inline keyboard for format selection
        keyboard = [
            [
                InlineKeyboardButton("🎥 360p", callback_data="video_360"),
                InlineKeyboardButton("🎥 720p", callback_data="video_720"),
                InlineKeyboardButton("🎥 1080p", callback_data="video_1080")
            ],
            [
                InlineKeyboardButton("🎵 MP3", callback_data="audio_mp3"),
                InlineKeyboardButton("🎵 M4A", callback_data="audio_m4a")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format message with video info and AI tags
        duration_min = int(video_info['duration']) // 60
        duration_sec = int(video_info['duration']) % 60
        
        # Формируем текст с тегами
        tags_text = ""
        if tags and tags.get('hashtags'):
            tags_text = f"\n\n🏷 *Популярные теги:*\n{' '.join(tags['hashtags'][:10])}"
            
            if tags.get('keywords'):
                tags_text += f"\n\n🔑 *Ключевые слова:*\n{', '.join(tags['keywords'][:5])}"
        
        info_text = (
            f"📹 *{video_info['title']}*\n\n"
            f"👤 {video_info.get('uploader', 'YouTube')}\n"
            f"⏱ {duration_min}:{duration_sec:02d}\n"
            f"{tags_text}\n\n"
            f"✨ *Выбери формат для скачивания:*"
        )
        
        await processing_msg.delete()
        await ai_msg.delete()
        
        await message.reply_text(
            info_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error processing YouTube URL: {e}")
        await processing_msg.delete()
        await message.reply_text(
            "❌ Не удалось получить информацию о видео.\n"
            "Проверь ссылку и попробуй снова."
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback from inline keyboard"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    callback_data = query.data
    
    video_data = user_videos.get(user_id)
    if not video_data:
        await query.edit_message_text(
            "❌ Информация о видео устарела. Пожалуйста, отправь ссылку заново."
        )
        return
    
    format_type, quality = callback_data.split('_')
    
    await query.edit_message_text(
        f"⏬ Начинаю скачивание...\n\n"
        f"📹 {video_data['title'][:50]}...\n"
        f"📀 Формат: {'Видео ' + quality if format_type == 'video' else 'Аудио ' + quality.upper()}\n\n"
        f"⏳ Пожалуйста, подожди. Это может занять до минуты."
    )
    
    try:
        await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.UPLOAD_DOCUMENT)
        
        caption_text = f"📹 {video_data['title']}\nКачество: {quality}p\n\n"
        
        # Добавляем теги в описание
        if video_data.get('tags') and video_data['tags'].get('hashtags'):
            caption_text += f"🏷 {' '.join(video_data['tags']['hashtags'][:10])}\n\n"
        
        if format_type == 'video':
            file_path = download_video(video_data['url'], quality)
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size > Config.MAX_FILE_SIZE:
                await query.edit_message_text(
                    f"❌ Файл слишком большой ({file_size:.1f} МБ).\n"
                    f"Telegram ограничивает размер файлов {Config.MAX_FILE_SIZE} МБ.\n"
                    f"Попробуй выбрать более низкое качество или аудио."
                )
                cleanup_file(file_path)
                return
            
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video_file,
                    caption=caption_text,
                    supports_streaming=True
                )
                
        else:  # audio
            file_path = download_audio(video_data['url'], quality)
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            
            if file_size > Config.MAX_FILE_SIZE:
                await query.edit_message_text(
                    f"❌ Файл слишком большой ({file_size:.1f} МБ).\n"
                    f"Telegram ограничивает размер файлов {Config.MAX_FILE_SIZE} МБ."
                )
                cleanup_file(file_path)
                return
            
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=audio_file,
                    title=video_data['title'],
                    performer=video_data.get('uploader', 'YouTube'),
                    caption=caption_text
                )
        
        cleanup_file(file_path)
        
        await query.message.reply_text(
            "✅ Готово! Файл успешно загружен.\n\n"
            "📌 Можешь отправить другую ссылку для продолжения."
        )
        
        del user_videos[user_id]
        
    except Exception as e:
        logger.error(f"Error downloading: {e}")
        await query.edit_message_text(
            f"❌ Произошла ошибка при скачивании.\n\n"
            f"Ошибка: {str(e)[:150]}\n\n"
            f"Попробуй:\n"
            f"• Выбрать другое качество\n"
            f"• Скачать аудио вместо видео\n"
            f"• Использовать другую ссылку"
        )
