from telegram import Update
from telegram.ext import CallbackContext

from app.bot.dictionaries import states


def end(update: Update, ctx: CallbackContext):
    ctx.user_data.clear()
    return states.END
