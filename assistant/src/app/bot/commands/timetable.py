import datetime as dt
import logging
import random
import re

import telegram as tg
from sqlalchemy.orm import Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext

from app.bot.commands.moderation import send_request
from app.bot.commands.utils import end
from app.bot.decorators import acquire_user, db_session
from app.bot.dictionaries import states, week
from app.bot.dictionaries.phrases import *
from app.bot.keyboards import build_keyboard_menu
from app.database import Lesson, LessonSubgroupMember, Request, SingleLesson, User
from app.utils import get_monday

logger = logging.getLogger(__name__)
__all__ = ["show_week_timetable", "show_day_timetable", "link", "set_lesson_link", "build_timetable_day"]

ENDING_SPACES_MASK = re.compile(r"^(.*)(?<!\s)(\s+)$", flags=re.S)


def build_timetable_lesson(session: Session, user: User, lesson: SingleLesson):
    teachers_names = [t.short_name for t in lesson.lesson.teachers]
    teachers_formatted = "{emoji} {teachers}".format(emoji=E_TEACHER,
                                                     teachers=f"{E_TEACHER} ".join(teachers_names))
    result_str = """\
{starts_at} - {ends_at}
{e_books} <b>{name}</b> ({format})
{teachers}\n\
""".format(
        e_clock=E_CLOCK, starts_at=lesson.starts_at.strftime("%H:%M"),
        ends_at=lesson.ends_at.strftime("%H:%M"),
        e_books=E_BOOKS, name=lesson.lesson.name, format=lesson.lesson.represent_lesson_format(),
        teachers=teachers_formatted
    )
    if lesson.lesson.link:
        result_str += "<a href=\"{}\"><u><i>Посилання на урок</i></u></a>. Змінити: /link@{}\n" \
            .format(lesson.lesson.link, lesson.lesson_id)
    else:
        result_str += "Встановити посилання: /link@{}\n" \
            .format(lesson.lesson_id)

    # if lesson.comment:
    #     result_str += "<i>{} (/comment@{})</i>".format(lesson.comment, lesson.id)
    # else:
    #     result_str += "Додати коментар: /comment@{}".format(lesson.id)
    result_str = ENDING_SPACES_MASK.sub(r"\1", result_str)  # remove \n in the ending
    return result_str


def build_timetable_day(session: Session, user: User, date: dt.date):
    lessons = (
        session.query(SingleLesson)
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
                day=week.LIST[date.weekday()].name,
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
        requested_date = states.TimetableWeekSelection.parse(update.callback_query.data)
        if requested_date is None:
            return None
        requested_date = requested_date.group(1)
        requested_date = dt.datetime.strptime(requested_date, "%Y-%m-%d").date()

    requested_monday = get_monday(requested_date)
    previous_monday = requested_monday - dt.timedelta(days=7)
    next_monday = requested_monday + dt.timedelta(days=7)

    kb_buttons = [
        InlineKeyboardButton(
            text="< {}".format(previous_monday.strftime("%d.%m.%Y")),
            callback_data=states.TimetableWeekSelection.build(
                previous_monday.isoformat()),
        ),
        InlineKeyboardButton(
            text="Сьогодні",
            callback_data=states.TimetableWeekSelection.build(
                dt.date.today().isoformat()),
        ),
        InlineKeyboardButton(
            text="{} >".format(next_monday.strftime("%d.%m.%Y")),
            callback_data=states.TimetableWeekSelection.build(
                next_monday.isoformat()),
        ),
    ]
    keyboard = build_keyboard_menu(kb_buttons, 3)

    timetable_str = build_timetable_week(session, user, requested_monday)
    if timetable_str.strip() == "":
        timetable_str = "На цьому тижні немає занять"

    if not update.callback_query:
        update.message.reply_text(
            text=timetable_str,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )
    else:
        update.callback_query.answer()
        try:
            update.callback_query.edit_message_text(
                text=timetable_str,
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
        requested_date = states.TimetableDaySelection.parse(update.callback_query.data)
        if requested_date is None:
            return None
        requested_date = requested_date.group(1)
        requested_date = dt.datetime.strptime(requested_date, "%Y-%m-%d").date()

    yesterday = requested_date - dt.timedelta(days=1)
    tomorrow = requested_date + dt.timedelta(days=1)

    kb_buttons = [
        InlineKeyboardButton(
            text="< {}".format(yesterday.strftime("%d.%m.%Y")),
            callback_data=states.TimetableDaySelection.build(yesterday.isoformat()),
        ),
        InlineKeyboardButton(
            text="Сьогодні",
            callback_data=states.TimetableDaySelection.build(
                dt.date.today().isoformat()),
        ),
        InlineKeyboardButton(
            text="{} >".format(tomorrow.strftime("%d.%m.%Y")),
            callback_data=states.TimetableDaySelection.build(tomorrow.isoformat()),
        ),
    ]
    keyboard = build_keyboard_menu(kb_buttons, 3)

    header = "<b>{day_name}</b> ({date})".format(day_name=week.LIST[requested_date.weekday()].name,
                                                 date=requested_date.strftime("%d.%m"))
    timetable_str = build_timetable_day(session, user, requested_date)
    if timetable_str.strip() == "":
        timetable_str = "Заняття відсутні"
    timetable_str = "{header}\n\n{body}".format(header=header, body=timetable_str)

    if not update.callback_query:
        update.message.reply_text(
            text=timetable_str,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )
    else:
        update.callback_query.answer()
        try:
            update.callback_query.edit_message_text(
                text=timetable_str,
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
        session.query(Lesson)
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
            text=random.choice(answers),
            parse_mode=ParseMode.HTML,
        )
        return end(update=update, ctx=ctx)

    moderator = (
        session.query(User)
        .filter(
            (User.students_group_id == user.students_group.id) &
            (User.is_group_moderator == True)
        )
        .first()
    )
    if moderator is None:
        update.message.reply_text(
            text=f"{E_CANCEL} Ваша група наразі не має модератора! Будь ласка, зверніться до "
                 f"@iterlace!",
            parse_mode=ParseMode.HTML,
        )
        return end(update=update, ctx=ctx)

    ctx.user_data["lesson_id"] = lesson_id
    ctx.user_data["init"] = True
    return set_lesson_link(update=update, ctx=ctx, session=session, user=user)


@db_session
@acquire_user
def set_lesson_link(update: Update, ctx: CallbackContext, session: Session, user: User):
    lesson_id = ctx.user_data["lesson_id"]
    lesson = session.query(Lesson).get(lesson_id)

    if ctx.user_data.setdefault("init", False):
        ctx.user_data["init"] = False
        update.message.reply_text(
            text="Введіть посилання:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text=P_CANCEL, callback_data=states.END)
            ]]),
        )
        return states.LinkWait

    link = update.message.text.strip()
    message = "@{user} хоче встановити нове посилання для <b>{lesson}</b>:\n{link}" \
        .format(user=user.tg_username, lesson=str(lesson), link=link)
    if lesson.link:
        message += "\nзамість\n{}".format(lesson.link)

    request = Request(
        initiator=user,
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
