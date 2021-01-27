import datetime as dt

from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from assistant import config
from assistant.bot.dictionaries.phrases import *
from assistant.database import User
from assistant.bot.commands.tests.utils import flatten_keyboard
from assistant.database import StudentsGroup, Faculty, SingleLesson

from assistant.bot.commands.timetable import build_timetable_lesson, build_timetable_day


class TestTimetable:

    def test_build_timetable_lesson(self, db_session, fill_lessons, fill_users):
        # TODO: use a SingleLesson from a fixture
        single_lesson = SingleLesson(
            lesson=fill_lessons[0],
            date=dt.datetime.strptime("2021-01-26", "%Y-%m-%d").date(),
            starts_at=dt.time(hour=10, minute=0, second=0),
            ends_at=dt.time(hour=11, minute=30, second=0),
        )

        result = build_timetable_lesson(db_session, fill_users[0], single_lesson)

        assert result == f"{e_clock} 10:00 - 11:30\n" \
                         f"{e_books} <b>{single_lesson.lesson.name}</b>  " \
                         f"{e_person} {single_lesson.lesson.teachers[0].short_name}"

    def test_build_timetable_day(self, db_session, fill_lessons, fill_users):
        # TODO: use SingleLessons from a fixture
        # TODO: make dependencies more clear
        date = dt.date(year=2021, month=1, day=26)
        lessons = [
            # Jan 26
            SingleLesson(
                lesson=fill_lessons[0],
                date=date,
                starts_at=dt.time(hour=10, minute=0, second=0),
                ends_at=dt.time(hour=11, minute=30, second=0),
            ),
            SingleLesson(
                lesson=fill_lessons[0],
                date=date,
                starts_at=dt.time(hour=12, minute=0, second=0),
                ends_at=dt.time(hour=13, minute=30, second=0),
            ),
            # odd lesson (Jan 30)
            SingleLesson(
                lesson=fill_lessons[0],
                date=dt.datetime.strptime("2021-01-30", "%Y-%m-%d").date(),
                starts_at=dt.time(hour=14, minute=0, second=0),
                ends_at=dt.time(hour=15, minute=30, second=0),
            ),
        ]
        for i in lessons:
            db_session.add(i)
        db_session.commit()

        result = build_timetable_day(db_session, fill_users[0], date)

        assert result == f"""\
{e_clock} 10:00 - 11:30
{e_books} <b>{lessons[0].lesson.name}</b>  {e_person} {lessons[0].lesson.teachers[0].short_name}

{e_clock} 12:00 - 13:30
{e_books} <b>{lessons[1].lesson.name}</b>  {e_person} {lessons[1].lesson.teachers[0].short_name}\
"""

