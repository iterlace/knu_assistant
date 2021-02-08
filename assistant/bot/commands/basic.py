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
    ParseMode,
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

import assistant
from assistant.config import bot
from assistant.database import User, StudentsGroup
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states
from assistant.bot.commands.user import change_group
from assistant.bot.keyboards import build_keyboard_menu
from assistant.bot.commands.utils import end

logger = logging.getLogger(__name__)
__all__ = ["start", "help", "end_callback"]

HELLO_MESSAGE = """
<b>КНУ.Органайзер</b> збере в купу твій розклад та домашні завдання, полегшить життя старостам \
та не дасть забути нічого важливого. 

<b>Команди:</b>
   <b>[ Власні налаштування ]</b>
   /change_group - перейти в іншу групу/підгрупу

   <b>[ Розклад ]</b>
   /week - на тиждень
   /day - на день

<b>Ти - староста?</b>
Повідом про це @iterlace та отримай привілеї.

Якщо бажаєш підтримати проєкт: https://github.com/iterlace/knu_assistant
Оригінальний розклад було завантажено з https://mytimetable.live
Фідбек: @iterlace

v{}
""".format(assistant.__version__)


@db_session
@acquire_user
def start(update: Update, ctx: CallbackContext, session: Session, user: User):
    if user.students_group_id is None:
        bot.send_message(update.effective_user.id, HELLO_MESSAGE)
        bot.send_message(update.effective_user.id, "Давай розпочнемо.")
        return change_group(update=update, ctx=ctx, session=session, user=user)
    else:
        responses = ["Що як?", "Як тебе досі не відрахували?", "/start",
                     "Не можна повернутися в минуле і змінити свій старт, "
                     "але можна стартувати зараз і змінити свій фініш. © Мыслитель.инфо"]
        bot.send_message(update.effective_user.id, random.choice(responses))
        return end(update=update, ctx=ctx)


def end_callback(update: Update, ctx: CallbackContext, delete: bool = False):
    if update.callback_query is not None:
        update.callback_query.answer()
        # bot.edit_message_text(
        #     chat_id=update.effective_user.id,
        #     message_id=update.callback_query.message.message_id,
        #     text=update.callback_query.message.text,
        #     parse_mode=ParseMode.HTML,
        #     reply_markup=None,
        # )
        bot.delete_message(
            chat_id=update.effective_user.id,
            message_id=update.callback_query.message.message_id,
        )
    ctx.user_data.clear()
    return states.END


def help(update: Update, ctx: CallbackContext):
    update.message.reply_text(
        HELLO_MESSAGE,
        parse_mode=ParseMode.HTML,
    )
