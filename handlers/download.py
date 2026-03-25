import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from telegram.constants import ChatAction
from config import Config
from utils.youtube import download_video, download_audio, get_video_info, cleanup_file

logger = logging.getLogger(__name__)

user_states = {}
user_videos = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    message = update.message
    text = message.text
    
    # Check if message is YouTube URL
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
        "🔍 Получаю информацию о видео...\n\n"
        "⚠️ YouTube может обрабатывать запрос до 30 секунд. Пожалуйста, подожди."
    )
    
    try:
        # Get video info
        video_info = get_video_info(url)
        
        # Store video info for this user
        user_videos[user_id] = {
            'url': url,
            'title': video_info['title'],
            'duration': video_info['duration']
        }
        
        # Create inline keyboard
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
        
        # Format message with video info
        duration_min = int(video_info['duration']) // 60
        duration_sec = int(video_info['duration']) % 60
        
        info_text = (
            f"📹 *{video_info['title']}*\n\n"
            f"👤 {video_info['uploader']}\n"
            f"⏱ {duration_min}:{duration_sec:02d}\n\n"
            f"Выбери формат для скачивания:"
        )
        
        await processing_msg.delete()
        await message.reply_text(
            info_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error processing YouTube URL: {e}")
        await processing_msg.delete()
        
        error_message = (
            "❌ Не удалось получить информацию о видео.\n\n"
            "Возможные причины:\n"
            "• Видео недоступно\n"
            "• YouTube временно блокирует запросы\n"
            "• Ссылка недействительна\n\n"
            "Попробуй:\n"
            "• Подождать 1-2 минуты\n"
            "• Использовать другое видео\n"
            "• Скачать аудио вместо видео"
        )
        await message.reply_text(error_message)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback from inline keyboard"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
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
                    caption=f"📹 {video_data['title']}\nКачество: {quality}p\n\n⬇️ Скачано с помощью YouTube Downloader Bot",
                    supports_streaming=True
                )
                
        else:
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
                    caption="⬇️ Скачано с помощью YouTube Downloader Bot"
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
            f"• Использовать другую ссылку\n"
            f"• Подождать 5-10 минут"
        )
