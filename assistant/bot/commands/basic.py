
import datetime as dt
import logging
import re
import random

import telegram as tg
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext,
)
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import User, StudentsGroup
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states
from assistant.bot.commands.user import change_group
from assistant.bot.keyboards import build_keyboard_menu


logger = logging.getLogger(__name__)
__all__ = ["start", "help"]

HELLO_MESSAGE = """
Привіт!

Якщо бажаєш підтримати проєкт: https://github.com/VolkoffMary/K14_helper_bot.git
Чат: @iterlace
"""


@db_session
@acquire_user
def start(update: Update, ctx: CallbackContext, session: Session, user: User):
    if user.students_group_id is None:
        bot.sendMessage(update.effective_user.id, HELLO_MESSAGE)
        bot.sendMessage(update.effective_user.id, "Давай розпочнемо.")
        change_group(update=update, ctx=ctx, session=session, user=user)
        return states.UserSelectCourse
    else:
        responses = ["Що як?", "Я тебе досі не відрахували?", "/start",
                     "Не можна повернутися в минуле і змінити свій старт, "
                     "але можна стартувати зараз і змінити свій фініш. © Мыслитель.инфо"]
        bot.sendMessage(update.effective_user.id, random.choice(responses))


def help(update: Update, ctx: CallbackContext):
    update.message.reply_text(HELLO_MESSAGE)
