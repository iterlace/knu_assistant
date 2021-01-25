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
from assistant.database import User, StudentsGroup, Lesson, TimetableLesson, Teacher
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states, days_of_week
from assistant.bot.dictionaries import timetable
from assistant.bot.keyboards import build_keyboard_menu
from assistant.bot.dictionaries.phrases import *

logger = logging.getLogger(__name__)
__all__ = ["show_timetable"]


def build_timetable_lesson(lesson: TimetableLesson):
    result_str = ""
    result_str += "{} {} - {}\n{} <b>{}</b>  {} {}\n".format(
        e_clock, lesson.starts_at.strftime("%H:%M"), lesson.ends_at.strftime("%H:%M"),
        e_books, lesson.lesson.name,
        e_person, lesson.teacher.short_name
    )
    return result_str


def build_timetable_day(group: StudentsGroup, session: Session, day: int):
    lessons = (
        session
        .query(TimetableLesson)
        .filter(
            (TimetableLesson.students_group_id == group.id) &
            (TimetableLesson.day_of_week == day)
        )
        .order_by("starts_at", "teacher_id")
        .all()
    )
    result_str = ""
    for lesson in lessons:
        result_str += "{}\n".format(build_timetable_lesson(lesson))
    return result_str


def build_timetable_week(group: StudentsGroup, session: Session):
    lessons_str = ""
    for day in days_of_week.DAYS_OF_WEEK:
        lessons_str += "[ <b>{}</b> ]\n\n{}\n".format(day.name, build_timetable_day(group, session, day))
    return lessons_str


# Buttons
cancel_add_lesson_button = InlineKeyboardButton(
    text="{} Скасувати".format(e_cancel),
    callback_data=states.CancelAddLessonToTimetable.build_pattern,
)


@db_session
@acquire_user
def show_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        bot.send_message(update.effective_user.id,
                         text=build_timetable_week(user.students_group, session),
                         parse_mode=ParseMode.HTML)

# @db_session
# @acquire_user
# def edit_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
#     if not update.callback_query:
#         kb_buttons = []
#         for day in days_of_week.DAYS_OF_WEEK:
#             kb_buttons.append(InlineKeyboardButton(
#                 # todo: pencil emoji
#                 text="{} {}".format(e_pencil, day.name),
#                 callback_data=states.EditTimetableDay.build_pattern.format(day),
#             ))
#         bot.send_message(update.effective_user.id,
#                         text=build_timetable_week(user.students_group, session),
#                         reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 2)),
#                         parse_mode=ParseMode.HTML)
#
#
# @db_session
# @acquire_user
# def edit_timetable_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     kb_buttons = []
#     for day in days_of_week.DAYS_OF_WEEK:
#         kb_buttons.append(InlineKeyboardButton(
#             text="{} {}".format(e_pencil, day.name),
#             callback_data=states.EditTimetableDay.build_pattern.format(day),
#         ))
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text=build_timetable_week(user.students_group, session),
#         reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 2)),
#         parse_mode=ParseMode.HTML,
#     )
#
#
# @db_session
# @acquire_user
# def edit_timetable_day_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     match = states.EditTimetableDay.parse_pattern.match(update.callback_query.data)
#     day = int(match.group(1))
#     kb_buttons = []
#     keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#         kb_buttons,
#         footer_buttons=[
#             InlineKeyboardButton(text="{} Додати".format(e_new),
#                                  callback_data=states.AddLessonToTimetable.build_pattern.format(day)),
#             InlineKeyboardButton(text="<<", callback_data=states.EditTimetable.build_pattern),
#         ],
#         n_cols=2,
#     ))
#     # TODO: iterate over existing lessons
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text=build_timetable_day(user.students_group, session, day) or "Пари відсутні",
#         reply_markup=keyboard,
#         parse_mode=ParseMode.HTML,
#     )
#
#
# @db_session
# @acquire_user
# def add_lesson_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     match = states.AddLessonToTimetable.parse_pattern.match(update.callback_query.data)
#     ctx.user_data["day"] = match.group(1)
#     kb_buttons = []
#     for lesson in session.query(Lesson).order_by("name"):
#         kb_buttons.append(InlineKeyboardButton(
#             text=lesson.name,
#             callback_data=lesson.id,
#         ))
#     keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#         kb_buttons,
#         footer_buttons=[cancel_add_lesson_button],
#         n_cols=2,
#     ))
#     # TODO: iterate over existing lessons
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text="{} Який предмет додамо?".format(e_books),
#         reply_markup=keyboard,
#         parse_mode=ParseMode.HTML,
#     )
#     return "read_lesson"
#
#
# @db_session
# @acquire_user
# def add_lesson_lesson_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     lesson_id = update.callback_query.data
#     lesson = session.query(Lesson).get(lesson_id)
#     if lesson is None:
#         # TODO
#         return ConversationHandler.END
#     ctx.user_data["lesson_id"] = lesson_id
#
#     kb_buttons = []
#     for lesson_type in timetable.LESSON_TYPES.values():
#         kb_buttons.append(InlineKeyboardButton(
#             text=lesson_type.name,
#             callback_data=lesson_type.keyword,
#         ))
#     keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#         kb_buttons,
#         footer_buttons=[cancel_add_lesson_button],
#         n_cols=2,
#     ))
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text="Предмет - {}".format(lesson.name),
#         reply_markup=None,
#         parse_mode=ParseMode.HTML,
#     )
#     bot.send_message(
#         chat_id=update.effective_user.id,
#         text="{} Який вид заняття?".format(e_person),
#         reply_markup=keyboard,
#         parse_mode=ParseMode.HTML,
#     )
#     return "read_lesson_type"
#
#
# @db_session
# @acquire_user
# def add_lesson_lesson_type_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     lesson_type = update.callback_query.data
#     ctx.user_data["lesson_type"] = lesson_type
#
#     kb_buttons = []
#     for teacher in session.query(Teacher).order_by("last_name"):
#         kb_buttons.append(InlineKeyboardButton(
#             text=teacher.short_name,
#             callback_data=teacher.id,
#         ))
#     keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#         kb_buttons,
#         footer_buttons=[cancel_add_lesson_button],
#         n_cols=2,
#     ))
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text="Тип предмету - {}".format(timetable.LESSON_TYPES[lesson_type].name),
#         reply_markup=None,
#         parse_mode=ParseMode.HTML,
#     )
#     bot.send_message(
#         chat_id=update.effective_user.id,
#         text="{} Хто викладає?".format(e_person),
#         reply_markup=keyboard,
#         parse_mode=ParseMode.HTML,
#     )
#     return "read_teacher"
#
#
# @db_session
# @acquire_user
# def add_lesson_teacher_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     teacher_id = update.callback_query.data
#     teacher = session.query(Teacher).get(teacher_id)
#     if teacher is None:
#         # TODO
#         pass
#     ctx.user_data["teacher_id"] = teacher_id
#
#     keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#         [],
#         # FIXME
#         # footer_buttons=[cancel_add_lesson_button],
#         n_cols=2,
#     ))
#
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text="Викладач - {}".format(teacher.full_name),
#         reply_markup=None,
#         parse_mode=ParseMode.HTML,
#     )
#     # TODO: iterate over existing lessons
#     bot.send_message(
#         chat_id=update.effective_user.id,
#         text="{} О котрій проводиться пара?\n"
#              "Записуйте розклад у вигляді \"8:40 - 10:15\".".format(e_clock),
#         reply_markup=keyboard,
#         parse_mode=ParseMode.HTML,
#     )
#     return "read_time"
#
#
# @db_session
# @acquire_user
# def add_lesson_time(update: Update, ctx: CallbackContext, session: Session, user: User):
#     if (match := timetable.time_span_pattern.match(update.message.text)) is None:
#         keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#             [],
#             footer_buttons=[cancel_add_lesson_button],
#             n_cols=2,
#         ))
#         bot.send_message(
#             chat_id=update.effective_user.id,
#             text="Некоректний формат!\nЗаписуйте розклад у вигляді \"8:40 - 10:15\".",
#             reply_markup=keyboard,
#             parse_mode=ParseMode.HTML,
#         )
#         return "read_time"
#     else:
#         _, start_hour, start_minute, _, end_hour, end_minute = match.groups()
#         # TODO: filter start_hour, start_minute, end_hour, end_minute
#         # TODO: timezone
#         ctx.user_data["starts_at"] = dt.time(hour=int(start_hour), minute=int(start_minute))
#         ctx.user_data["ends_at"] = dt.time(hour=int(end_hour), minute=int(end_minute))
#
#     keyboard = InlineKeyboardMarkup(build_keyboard_menu(
#         [],
#         n_cols=2,
#     ))
#
#     created_lesson = TimetableLesson(
#         students_group_id=user.students_group_id,
#         lesson_id=ctx.user_data["lesson_id"],
#         teacher_id=ctx.user_data["teacher_id"],
#         day_of_week=ctx.user_data["day"],
#         starts_at=ctx.user_data["starts_at"],
#         ends_at=ctx.user_data["ends_at"],
#     )
#
#     session.add(created_lesson)
#     session.commit()
#
#     # TODO: iterate over existing lessons
#     bot.send_message(
#         chat_id=update.effective_user.id,
#         text="Предмет додано:\n{}".format(build_timetable_lesson(created_lesson)),
#         reply_markup=keyboard,
#         parse_mode=ParseMode.HTML,
#     )
#
#
# @db_session
# @acquire_user
# def cancel_add_lesson_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
#     ctx.user_data.clear()
#
#     bot.edit_message_text(
#         chat_id=update.effective_user.id,
#         message_id=update.callback_query.message.message_id,
#         text="Скасовано",
#         reply_markup=None,
#     )
#     return ConversationHandler.END
