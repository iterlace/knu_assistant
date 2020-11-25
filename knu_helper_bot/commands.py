
import logging

import telegram as tg
from telegram import Bot, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext,
)

from knu_helper_bot.config import bot
from knu_helper_bot.database import Session, User
from knu_helper_bot.decorators import acquire_user, db_session

logger = logging.getLogger(__name__)


@db_session
@acquire_user
def start(update: Update, ctx: CallbackContext, session: Session, user: User):
    bot.sendMessage(update.effective_user.id, """
Раді вітати тебе в нашому боті!
    """)


def help(update: Update, ctx: CallbackContext):
    bot.message.reply_text("Со всеми вопросами пока обращаться к @the_Yttra или @iterlace")

