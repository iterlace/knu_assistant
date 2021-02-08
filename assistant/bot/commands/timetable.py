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
    ParseMode,
)
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
)
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import (
    User,
    StudentsGroup,
    Lesson,
    SingleLesson,
    Teacher,
    LessonSubgroupMember,
    Request,
)
from assistant.bot.decorators import acquire_user, db_session, moderators_only, admins_only
from assistant.bot.dictionaries import states, days_of_week
from assistant.bot.dictionaries import timetable
from assistant.bot.keyboards import build_keyboard_menu
from assistant.bot.dictionaries.phrases import *
from assistant.utils import get_monday
from assistant.bot.commands.moderation import send_request
from assistant.bot.commands.utils import end

logger = logging.getLogger(__name__)
__all__ = ["show_week_timetable", "show_day_timetable", "link", "set_lesson_link"]

ENDING_SPACES_MASK = re.compile(r"^(.*)(?<!\s)(\s+)$", flags=re.S)


def build_timetable_lesson(session: Session, user: User, lesson: SingleLesson):
    teachers_names = [t.short_name for t in lesson.lesson.teachers]
    teachers_formatted = "{emoji} {teachers}".format(emoji=e_teacher,
                                                     teachers=f"{e_teacher} ".join(teachers_names))
    result_str = """\
{starts_at} - {ends_at}
{e_books} <b>{name}</b> ({format})
{teachers}\n\
""".format(
        e_clock=e_clock, starts_at=lesson.starts_at.strftime("%H:%M"), ends_at=lesson.ends_at.strftime("%H:%M"),
        e_books=e_books, name=lesson.lesson.name, format=lesson.lesson.represent_lesson_format(),
        teachers=teachers_formatted
    )
    if lesson.lesson.link:
        result_str += "<a href=\"{}\"><u><i>Посилання на урок</i></u></a>. Змінити: /link@{}\n"\
            .format(lesson.lesson.link, lesson.lesson_id)
    else:
        result_str += "Встановити посилання: /link@{}\n"\
            .format(lesson.lesson_id)

    # if lesson.comment:
    #     result_str += "<i>{} (/comment@{})</i>".format(lesson.comment, lesson.id)
    # else:
    #     result_str += "Додати коментар: /comment@{}".format(lesson.id)
    result_str = ENDING_SPACES_MASK.sub(r"\1", result_str)  # remove \n in the ending
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
    result_str = ENDING_SPACES_MASK.sub(r"\1", result_str)  # remove \n in the ending
    return result_str


def build_timetable_week(session: Session, user: User, monday: dt.date):
    result_str = ""
    for day_idx in range(7):
        date = monday + dt.timedelta(days=day_idx)
        lesson_details = build_timetable_day(session, user, date)
        if lesson_details:
            result_str += "[ <b>{day}</b> ]\n{lesson_details}\n\n".format(
                day=days_of_week.DAYS_OF_WEEK[date.weekday()].name,
                lesson_details=lesson_details,
            )
    result_str = ENDING_SPACES_MASK.sub(r"\1", result_str)  # remove \n in the ending
    return result_str


@db_session
@acquire_user
def show_week_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        requested_date = dt.date.today()
    else:
        requested_date = states.TimetableWeekSelection.parse_pattern.match(update.callback_query.data)
        if requested_date is None:
            return None
        else:
            requested_date = requested_date.group(1)
        requested_date = dt.datetime.strptime(requested_date, "%Y-%m-%d").date()

    requested_monday = get_monday(requested_date)
    previous_monday = requested_monday - dt.timedelta(days=7)
    next_monday = requested_monday + dt.timedelta(days=7)

    kb_buttons = [
        InlineKeyboardButton(
            text="< {}".format(previous_monday.strftime("%d.%m.%Y")),
            callback_data=states.TimetableWeekSelection.build_pattern.format(previous_monday.isoformat()),
        ),
        InlineKeyboardButton(
            text="Сьогодні",
            callback_data=states.TimetableWeekSelection.build_pattern.format(dt.date.today().isoformat()),
        ),
        InlineKeyboardButton(
            text="{} >".format(next_monday.strftime("%d.%m.%Y")),
            callback_data=states.TimetableWeekSelection.build_pattern.format(next_monday.isoformat()),
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
            disable_web_page_preview=True,
        )
    else:
        update.callback_query.answer()
        try:
            update.callback_query.edit_message_text(
                timetable_str,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
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
        requested_date = states.TimetableDaySelection.parse_pattern.match(update.callback_query.data)
        if requested_date is None:
            return None
        else:
            requested_date = requested_date.group(1)
        requested_date = dt.datetime.strptime(requested_date, "%Y-%m-%d").date()

    yesterday = requested_date - dt.timedelta(days=1)
    tomorrow = requested_date + dt.timedelta(days=1)

    kb_buttons = [
        InlineKeyboardButton(
            text="< {}".format(yesterday.strftime("%d.%m.%Y")),
            callback_data=states.TimetableDaySelection.build_pattern.format(yesterday.isoformat()),
        ),
        InlineKeyboardButton(
            text="Сьогодні",
            callback_data=states.TimetableDaySelection.build_pattern.format(dt.date.today().isoformat()),
        ),
        InlineKeyboardButton(
            text="{} >".format(tomorrow.strftime("%d.%m.%Y")),
            callback_data=states.TimetableDaySelection.build_pattern.format(tomorrow.isoformat()),
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
            disable_web_page_preview=True,
        )
    else:
        update.callback_query.answer()
        try:
            update.callback_query.edit_message_text(
                timetable_str,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except tg.TelegramError as e:
            # FIXME
            if "Message is not modified" not in str(e):
                raise e
    return states.TimetableDaySelection


@db_session
@acquire_user
def link(update: Update, ctx: CallbackContext, session: Session, user: User):
    lesson_id = int(ctx.match.group(1))
    lesson = (
        session
        .query(Lesson)
        # join user's subgroups
        .outerjoin(
            LessonSubgroupMember,
            LessonSubgroupMember.c.user_id == user.tg_id
        )
        .filter(
            (Lesson.id == lesson_id) &
            ((Lesson.subgroup == None) | (Lesson.id == LessonSubgroupMember.c.lesson_id)) &
            (Lesson.students_group_id == user.students_group_id)
        )
        .first()
    )
    if lesson is None:
        answers = ["???", "Це ж не твій предмет!", "Знущаєшся з мене?",
                   "Введіть посилання:\n<i>жартую. як і ти.</i>"]
        update.message.reply_text(
            random.choice(answers),
            parse_mode=ParseMode.HTML,
        )
        return end(update=update, ctx=ctx)

    ctx.user_data["lesson"] = lesson
    ctx.user_data["init"] = True
    return set_lesson_link(update=update, ctx=ctx, session=session, user=user)


@db_session
@acquire_user
def set_lesson_link(update: Update, ctx: CallbackContext, session: Session, user: User):
    lesson = ctx.user_data["lesson"]

    if ctx.user_data.setdefault("init", False):
        ctx.user_data["init"] = False
        bot.send_message(
            update.effective_user.id,
            "Введіть посилання:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text=p_cancel, callback_data=states.END)
            ]]),
        )
        return states.LinkWait
    else:
        link = update.message.text.strip()
        message = "@{user} хоче встановити нове посилання для <b>{lesson}</b>:\n{link}"\
            .format(user=user.tg_username, lesson=str(lesson), link=link)
        if lesson.link:
            message += "\nзамість\n{}".format(lesson.link)

        request = Request(
            initiator_id=user.tg_id,
            message=message,
            meta={
                "lesson_id": lesson.id,
                "link": link,
            },
            students_group=user.students_group,
        )
        send_request(
            request=request,
            session=session,
            accept_callback=states.ModeratorAcceptLink,
            reject_callback=states.ModeratorRejectLink,
        )
        return end(update=update, ctx=ctx)


