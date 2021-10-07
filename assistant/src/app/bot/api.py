from telegram import Bot as _Bot

from app.core.config import settings

bot = _Bot(token=settings.TELEGRAM_BOT_TOKEN)
