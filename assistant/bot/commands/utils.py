from telegram import Update
from telegram.ext import CallbackContext
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)

from assistant.config import bot
from assistant.bot.dictionaries import states


def end(update: Update, ctx: CallbackContext):
    # if update.callback_query is not None:
    #     update.callback_query.answer()
    #     bot.edit_message_text(
    #         chat_id=update.effective_user.id,
    #         message_id=update.callback_query.message.message_id,
    #         text=update.callback_query.message.text,
    #         parse_mode=ParseMode.HTML,
    #         reply_markup=None,
    #     )
    ctx.user_data.clear()
    return states.END


