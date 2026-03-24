from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_message = (
        f"🎬 Привет, {user.first_name}!\n\n"
        "Я бот для скачивания видео с YouTube!\n\n"
        "📌 Просто отправь мне ссылку на YouTube видео, и я помогу его скачать.\n\n"
        "Доступные форматы:\n"
        "• Видео: 360p, 720p, 1080p\n"
        "• Аудио: MP3, M4A\n\n"
        "💡 Используй /help для получения справки"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 *Инструкция по использованию:*\n\n"
        "1. Отправь ссылку на YouTube видео\n"
        "2. Выбери нужный формат из предложенных\n"
        "3. Дождись загрузки файла\n\n"
        "*Доступные форматы:*\n"
        "🎥 Видео:\n"
        "• 360p - для быстрой загрузки\n"
        "• 720p - оптимальное качество\n"
        "• 1080p - высокое качество\n\n"
        "🎵 Аудио:\n"
        "• MP3 - для музыки\n"
        "• M4A - высокое качество звука\n\n"
        "*Ограничения:*\n"
        "• Максимальный размер файла: 50 МБ\n"
        "• Поддерживаются только YouTube ссылки\n\n"
        "*Команды:*\n"
        "/start - начать работу\n"
        "/help - показать справку"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')
