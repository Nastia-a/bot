import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from telegram.constants import ChatAction
from config import Config
from utils.youtube import download_video, download_audio, get_video_info, cleanup_file

logger = logging.getLogger(__name__)

# Store user states and video info
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
    
    # Send "processing" message
    processing_msg = await message.reply_text(
        "🔍 Получаю информацию о видео..."
    )
    
    try:
        # Get video info with better error handling
        video_info = get_video_info(url)
        
        # Store video info for this user
        user_videos[user_id] = {
            'url': url,
            'title': video_info['title'],
            'duration': video_info['duration']
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
        
        # Format message with video info
        duration_min = int(video_info['duration']) // 60
        duration_sec = int(video_info['duration']) % 60
        
        info_text = (
            f"📹 *{video_info['title']}*\n\n"
            f"⏱ Длительность: {duration_min}:{duration_sec:02d}\n\n"
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
        
        # Показываем понятную ошибку
        error_message = (
            "❌ Не удалось получить информацию о видео.\n\n"
            "Возможные причины:\n"
            "• Видео недоступно в вашем регионе\n"
            "• Видео имеет возрастное ограничение\n"
            "• Ссылка недействительна\n\n"
            "Попробуйте другую ссылку или подождите несколько минут и повторите попытку."
        )
        await message.reply_text(error_message)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback from inline keyboard"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Get video info for this user
    video_data = user_videos.get(user_id)
    if not video_data:
        await query.edit_message_text(
            "❌ Информация о видео устарела. Пожалуйста, отправь ссылку заново."
        )
        return
    
    # Parse format
    format_type, quality = callback_data.split('_')
    
    # Notify user about download start
    await query.edit_message_text(
        f"⏬ Начинаю скачивание...\n\n"
        f"Формат: {'Видео ' + quality if format_type == 'video' else 'Аудио ' + quality.upper()}\n"
        f"Пожалуйста, подожди..."
    )
    
    try:
        # Send typing action
        await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.UPLOAD_DOCUMENT)
        
        if format_type == 'video':
            # Download video
            file_path = download_video(video_data['url'], quality)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            # Check file size limit
            if file_size > Config.MAX_FILE_SIZE:
                await query.edit_message_text(
                    f"❌ Файл слишком большой ({file_size:.1f} МБ).\n"
                    f"Telegram ограничивает размер файлов {Config.MAX_FILE_SIZE} МБ.\n"
                    f"Попробуй выбрать более низкое качество."
                )
                cleanup_file(file_path)
                return
            
            # Send video
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video_file,
                    caption=f"📹 {video_data['title']}\nКачество: {quality}p",
                    supports_streaming=True
                )
                
        else:  # audio
            # Download audio
            file_path = download_audio(video_data['url'], quality)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            # Check file size limit
            if file_size > Config.MAX_FILE_SIZE:
                await query.edit_message_text(
                    f"❌ Файл слишком большой ({file_size:.1f} МБ).\n"
                    f"Telegram ограничивает размер файлов {Config.MAX_FILE_SIZE} МБ."
                )
                cleanup_file(file_path)
                return
            
            # Send audio
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=audio_file,
                    title=video_data['title'],
                    performer="YouTube"
                )
        
        # Clean up file
        cleanup_file(file_path)
        
        # Send success message
        await query.message.reply_text(
            "✅ Готово! Файл успешно загружен.\n\n"
            "📌 Можешь отправить другую ссылку для продолжения."
        )
        
        # Remove stored video info
        del user_videos[user_id]
        
    except Exception as e:
        logger.error(f"Error downloading: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при скачивании.\n"
            "Пожалуйста, попробуй другую ссылку или формат."
        )
