import datetime as dt
import logging
import re

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
    ConversationHandler,
    CallbackContext,
)
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import User, StudentsGroup, Lesson, SingleLesson, Teacher, LessonSubgroupMember
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states, days_of_week
from assistant.bot.dictionaries import timetable
from assistant.bot.keyboards import build_keyboard_menu
from assistant.bot.dictionaries.phrases import *
from assistant.utils import get_monday

logger = logging.getLogger(__name__)
__all__ = ["show_week_timetable", "show_day_timetable"]


def build_timetable_lesson(session: Session, user: User, lesson: SingleLesson):
    teachers_names = [t.short_name for t in lesson.lesson.teachers]
    teachers_formatted = "{emoji} {teachers}".format(emoji=e_teacher,
                                                     teachers=f"{e_teacher} ".join(teachers_names))
    result_str = "{starts_at} - {ends_at}\n{e_books} <b>{name}</b> ({format})\n{teachers}".format(
        e_clock=e_clock, starts_at=lesson.starts_at.strftime("%H:%M"), ends_at=lesson.ends_at.strftime("%H:%M"),
        e_books=e_books, name=lesson.lesson.name, format=lesson.lesson.represent_lesson_format(),
        teachers=teachers_formatted
    )
    return result_str


def build_timetable_day(session: Session, user: User, date: dt.date):
    lessons = (
        session
        .query(SingleLesson)
        # join user's subgroups
        .outerjoin(
            LessonSubgroupMember,
            LessonSubgroupMember.c.user_id == user.tg_id
        )
        # join user's not subdivided lessons
        .join(
            Lesson,
            (Lesson.id == SingleLesson.lesson_id) &
            ((Lesson.subgroup == None) | (Lesson.id == LessonSubgroupMember.c.lesson_id)) &
            (Lesson.students_group_id == user.students_group_id)
        )
        .filter(
            SingleLesson.date == date
        )
        .order_by("starts_at")
        .all()
    )
    result_str = ""
    for lesson in lessons:
        result_str += "{}\n\n".format(build_timetable_lesson(session, user, lesson))
    result_str = result_str[:-2]  # remove two last \n
    return result_str


def build_timetable_week(session: Session, user: User, monday: dt.date):
    result_str = ""
    for day_idx in range(7):
        date = monday + dt.timedelta(days=day_idx)
        result_str += "[ <b>{day}</b> ]\n{lesson_details}\n\n".format(
            day=days_of_week.DAYS_OF_WEEK[date.weekday()].name,
            lesson_details=build_timetable_day(session, user, date)
        )
    result_str = result_str[:-2]  # remove two last \n
    return result_str


@db_session
@acquire_user
def show_week_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        requested_date = dt.date.today()
    else:
        requested_date = dt.datetime.strptime(update.callback_query.data, "%Y-%m-%d").date()

    requested_monday = get_monday(requested_date)
    previous_monday = requested_monday - dt.timedelta(days=7)
    next_monday = requested_monday + dt.timedelta(days=7)

    kb_buttons = [
        InlineKeyboardButton(
            text="< {}".format(previous_monday.strftime("%d.%m.%Y")),
            callback_data=previous_monday.isoformat(),
        ),
        InlineKeyboardButton(
            text="Сьогодні".format(dt.date.today().strftime("%d.%m.%Y")),
            callback_data=dt.date.today().isoformat(),
        ),
        InlineKeyboardButton(
            text="{} >".format(next_monday.strftime("%d.%m.%Y")),
            callback_data=next_monday.isoformat(),
        ),
    ]
    keyboard = build_keyboard_menu(kb_buttons, 3)

    timetable_str = build_timetable_week(session, user, requested_monday)

    if not update.callback_query:
        bot.send_message(
            update.effective_user.id,
            text=timetable_str,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        update.callback_query.answer()
        try:
            update.callback_query.edit_message_text(
                timetable_str,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except tg.TelegramError as e:
            # FIXME
            if "Message is not modified" not in str(e):
                raise e
    return states.TimetableWeekSelection


@db_session
@acquire_user
def show_day_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        requested_date = dt.date.today()
    else:
        requested_date = dt.datetime.strptime(update.callback_query.data, "%Y-%m-%d").date()

    yesterday = requested_date - dt.timedelta(days=1)
    tomorrow = requested_date + dt.timedelta(days=1)

    kb_buttons = [
        InlineKeyboardButton(
            text="< {}".format(yesterday.strftime("%d.%m.%Y")),
            callback_data=yesterday.isoformat(),
        ),
        InlineKeyboardButton(
            text="Сьогодні".format(dt.date.today().strftime("%d.%m.%Y")),
            callback_data=dt.date.today().isoformat(),
        ),
        InlineKeyboardButton(
            text="{} >".format(tomorrow.strftime("%d.%m.%Y")),
            callback_data=tomorrow.isoformat(),
        ),
    ]
    keyboard = build_keyboard_menu(kb_buttons, 3)

    header = "<b>{day_name}</b> ({date})".format(day_name=days_of_week.DAYS_OF_WEEK[requested_date.weekday()].name,
                                                 date=requested_date.strftime("%d.%m"))
    timetable_str = build_timetable_day(session, user, requested_date)
    timetable_str = "{header}\n\n{body}".format(header=header, body=timetable_str)

    if not update.callback_query:
        bot.send_message(
            update.effective_user.id,
            text=timetable_str,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        update.callback_query.answer()
        try:
            update.callback_query.edit_message_text(
                timetable_str,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except tg.TelegramError as e:
            # FIXME
            if "Message is not modified" not in str(e):
                raise e
    return states.TimetableDaySelection


