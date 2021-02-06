import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackContext,
)
import sqlalchemy as sqa
from sqlalchemy import func
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import User, StudentsGroup, Faculty, Lesson, LessonTeacher, LessonSubgroupMember
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states
from assistant.bot.dictionaries.phrases import *
from assistant.bot.keyboards import build_keyboard_menu

logger = logging.getLogger(__name__)


# @db_session
# @acquire_user
# def approve_request(update: Update, ctx: CallbackContext, session: Session, user: User):

