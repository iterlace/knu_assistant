
import logging

import telegram as tg
from telegram import *
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from telegram.error import BadRequest

import config

logger = logging.getLogger(__name__)


def start(bot: Bot, update: Update):
    bot.message.reply_text("Привет!")


def help(bot: Bot, update: Update):
    bot.message.reply_text("Со всеми вопросами пока обращаться к @the_Yttra или @iterlace")

