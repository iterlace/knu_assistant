import datetime as dt

import mock
from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

import app
from app.core.config import settings
from app.bot.commands.tests.utils import flatten_keyboard
from app.bot.commands.timetable import (
    build_timetable_day,
    build_timetable_lesson,
    build_timetable_week,
)
from app.bot.dictionaries import states
from app.bot.dictionaries.phrases import *
from app.tests.factories import (
    LessonFactory,
    SingleLessonFactory,
    StudentsGroupFactory,
    TeacherFactory,
    UserFactory,
)


class TestTimetableBuilders:

    def test_build_timetable_lesson(self, db_session):
        # TODO: use a SingleLesson from a fixture
        single_lesson = SingleLessonFactory(
            starts_at=dt.time(hour=10, minute=0, second=0),
            ends_at=dt.time(hour=11, minute=30, second=0),
        )
        lesson = single_lesson.lesson
        user = UserFactory(students_group=single_lesson.lesson.students_group)
        db_session.commit()

        result = build_timetable_lesson(db_session, user, single_lesson)

        assert result == f"""\
10:00 - 11:30
{E_BOOKS} <b>{single_lesson.lesson.name}</b> ({single_lesson.lesson.represent_lesson_format()})
{E_TEACHER} {single_lesson.lesson.teachers[0].short_name}
Встановити посилання: /link@{lesson.id}\
"""

    def test_build_timetable_day(self, db_session):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)

        date = dt.date(year=2021, month=1, day=26)

        # Teachers
        koval = TeacherFactory()
        kondratyuk = TeacherFactory()

        # Lessons
        math = LessonFactory(name="M", lesson_format=0, students_group=group)
        # Programming practices are divided into 2 subgroups
        programming_1 = LessonFactory(teachers=[koval], subgroup="1",
                                      name="P", lesson_format=1, students_group=group)
        programming_2 = LessonFactory(teachers=[kondratyuk], subgroup="2",
                                      name="P", lesson_format=1, students_group=group)

        # User belongs to programming_1 subgroup
        user.subgroups.append(programming_1)

        # SingleLessons
        # Math SL
        SingleLessonFactory(
            lesson=math,
            date=date,
            starts_at=dt.time(8, 40),
            ends_at=dt.time(10, 15),
        )
        # Programming#1 SL
        SingleLessonFactory(
            lesson=programming_1,
            date=date,
            starts_at=dt.time(10, 35),
            ends_at=dt.time(12, 10),
        )
        # Programming#2 SL
        SingleLessonFactory(
            lesson=programming_2,
            date=date,
            starts_at=dt.time(10, 35),
            ends_at=dt.time(12, 10),
        )
        # Extra SL
        SingleLessonFactory(date=date)

        db_session.commit()

        result = build_timetable_day(db_session, user, date)
        assert result == f"""\
08:40 - 10:15
{E_BOOKS} <b>M</b> ({math.represent_lesson_format()})
{E_TEACHER} {math.teachers[0].short_name}
Встановити посилання: /link@{math.id}

10:35 - 12:10
{E_BOOKS} <b>P</b> ({programming_1.represent_lesson_format()})
{E_TEACHER} {koval.short_name}
Встановити посилання: /link@{programming_1.id}\
"""

    def test_build_timetable_week(self, db_session):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)

        monday = dt.date(year=2021, month=2, day=1)

        # Lessons
        math = LessonFactory(name="M", lesson_format=0, students_group=group)
        # SingleLessons
        math_sl = SingleLessonFactory(
            lesson=math,
            date=monday,
            starts_at=dt.time(8, 40),
            ends_at=dt.time(10, 15),
        )
        db_session.commit()

        with mock.patch("app.bot.commands.timetable.build_timetable_day",
                        side_effect=build_timetable_day) as build_day_mock:
            # from app.bot.commands.timetable import build_timetable_week, build_timetable_day
            result = build_timetable_week(db_session, user, monday)
            assert build_day_mock.call_count == 7
        assert result == f"""\
[ <b>Понеділок</b> ]
08:40 - 10:15
{E_BOOKS} <b>M</b> ({math.represent_lesson_format()})
{E_TEACHER} {math.teachers[0].short_name}
Встановити посилання: /link@{math.id}\
"""


class TestTimetableCommands:

    @mark.asyncio
    async def test_day(self, db_session, client: TelegramClient, use_bot):
        group = StudentsGroupFactory()
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)

        today = dt.date(2021, 2, 1)
        yesterday = today - dt.timedelta(days=1)
        tomorrow = today + dt.timedelta(days=1)

        with mock.patch("app.bot.commands.timetable.dt") as dt_mock:
            dt_mock.date.today = mock.MagicMock(return_value=today)
            dt_mock.datetime = dt.datetime
            dt_mock.timedelta = dt.timedelta

            # Lessons
            math = LessonFactory(name="M", lesson_format=0, students_group=group)
            # SingleLessons
            # Today math
            SingleLessonFactory(
                lesson=math,
                date=today,
                starts_at=dt.time(8, 40),
                ends_at=dt.time(10, 15),
            )
            # Yesterday math
            SingleLessonFactory(
                lesson=math,
                date=yesterday,
                starts_at=dt.time(12, 20),
                ends_at=dt.time(13, 55),
            )
            db_session.commit()

            async with client.conversation("@{}".format(settings.TELEGRAM_BOT_NAME), timeout=5) as conv:
                await conv.send_message("/day")
                r: Message

                r = await conv.get_response()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_day(db_session, user, today)
                assert r.text == "<b>Понеділок</b> (01.02)\n\n{}".format(expected_timetable)
                assert kb[0].text == "< {}".format(yesterday.strftime("%d.%m.%Y"))
                assert kb[1].text == "Сьогодні".format(today.strftime("%d.%m.%Y"))
                assert kb[2].text == "{} >".format(tomorrow.strftime("%d.%m.%Y"))

                # Select previous day
                await kb[0].click()

                r = await conv.get_edit()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_day(db_session, user, yesterday)
                assert r.text == "<b>Неділя</b> (31.01)\n\n{}".format(expected_timetable)

                # Select today
                await kb[1].click()

                r = await conv.get_edit()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_day(db_session, user, today)
                assert r.text == "<b>Понеділок</b> (01.02)\n\n{}".format(expected_timetable)

    @mark.asyncio
    async def test_empty_day(self, db_session, client: TelegramClient, use_bot):
        group = StudentsGroupFactory()
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)
        db_session.commit()

        today = dt.date(2021, 2, 1)
        yesterday = today - dt.timedelta(days=1)
        tomorrow = today + dt.timedelta(days=1)

        with mock.patch("app.bot.commands.timetable.dt") as dt_mock:
            dt_mock.date.today = mock.MagicMock(return_value=today)
            dt_mock.datetime = dt.datetime
            dt_mock.timedelta = dt.timedelta

            async with client.conversation("@{}".format(settings.TELEGRAM_BOT_NAME), timeout=5) as \
                    conv:
                await conv.send_message("/day")
                r: Message

                r = await conv.get_response()
                kb = flatten_keyboard(r.buttons)
                assert r.text == "<b>Понеділок</b> (01.02)\n\nЗаняття відсутні"
                assert kb[0].text == "< {}".format(yesterday.strftime("%d.%m.%Y"))
                assert kb[1].text == "Сьогодні".format(today.strftime("%d.%m.%Y"))
                assert kb[2].text == "{} >".format(tomorrow.strftime("%d.%m.%Y"))

    @mark.asyncio
    async def test_week(self, db_session, client: TelegramClient, use_bot):
        group = StudentsGroupFactory()
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)

        current_monday = dt.date(2021, 2, 1)
        prev_monday = current_monday - dt.timedelta(days=7)
        next_monday = current_monday + dt.timedelta(days=7)

        with mock.patch("app.bot.commands.timetable.dt") as dt_mock:
            dt_mock.date.today = mock.MagicMock(return_value=current_monday)
            dt_mock.datetime = dt.datetime
            dt_mock.timedelta = dt.timedelta

            # Lessons
            math = LessonFactory(name="M", lesson_format=0, students_group=group)
            # SingleLessons
            math_current_monday_sl = SingleLessonFactory(
                lesson=math,
                date=current_monday,
                starts_at=dt.time(8, 40),
                ends_at=dt.time(10, 15),
            )
            math_prev_monday_sl = SingleLessonFactory(
                lesson=math,
                date=prev_monday,
                starts_at=dt.time(12, 20),
                ends_at=dt.time(13, 55),
            )
            db_session.commit()

            async with client.conversation("@{}".format(settings.TELEGRAM_BOT_NAME), timeout=5) as conv:
                await conv.send_message("/week")
                r: Message

                r = await conv.get_response()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_week(db_session, user, current_monday)
                assert r.text == expected_timetable
                assert kb[0].text == "< {}".format(prev_monday.strftime("%d.%m.%Y"))
                assert kb[1].text == "Сьогодні".format(current_monday.strftime("%d.%m.%Y"))
                assert kb[2].text == "{} >".format(next_monday.strftime("%d.%m.%Y"))

                # Select previous day
                await kb[0].click()

                r = await conv.get_edit()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_week(db_session, user, prev_monday)
                assert r.text == expected_timetable

                # Select today
                await kb[1].click()

                r = await conv.get_edit()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_week(db_session, user, current_monday)
                assert r.text == expected_timetable

    @mark.asyncio
    async def test_empty_week(self, db_session, client: TelegramClient, use_bot):
        group = StudentsGroupFactory()
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)
        db_session.commit()

        current_monday = dt.date(2021, 2, 1)
        prev_monday = current_monday - dt.timedelta(days=7)
        next_monday = current_monday + dt.timedelta(days=7)

        with mock.patch("app.bot.commands.timetable.dt") as dt_mock:
            dt_mock.date.today = mock.MagicMock(return_value=current_monday)
            dt_mock.datetime = dt.datetime
            dt_mock.timedelta = dt.timedelta

            async with client.conversation("@{}".format(settings.TELEGRAM_BOT_NAME), timeout=5) as conv:
                await conv.send_message("/week")
                r: Message

                r = await conv.get_response()
                kb = flatten_keyboard(r.buttons)
                assert r.text == "На цьому тижні немає занять"
                assert kb[0].text == "< {}".format(prev_monday.strftime("%d.%m.%Y"))
                assert kb[1].text == "Сьогодні".format(current_monday.strftime("%d.%m.%Y"))
                assert kb[2].text == "{} >".format(next_monday.strftime("%d.%m.%Y"))


class TestLinkRequest:

    # TODO: /link integration test

    def test_link(self, db_session, mocker):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)
        moderator = UserFactory(students_group=group, is_group_moderator=True)
        lesson = LessonFactory(students_group=group)
        db_session.commit()

        update = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.match.group.return_value = lesson.id  # /link@<Lesson.id>
        ctx.user_data = dict()
        link = mocker.patch("app.bot.commands.timetable.link",
                            side_effect=app.bot.commands.timetable.link)
        set_lesson_link = mocker.patch("app.bot.commands.timetable.set_lesson_link")

        link(update=update, ctx=ctx, session=db_session, user=user)
        assert set_lesson_link.call_count == 1
        assert ctx.user_data == {"lesson_id": lesson.id, "init": True}

    def test_link_without_permission(self, db_session, mocker):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)
        moderator = UserFactory(students_group=group, is_group_moderator=True)
        lesson = LessonFactory()
        db_session.commit()

        update = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.match.group.return_value = lesson.id  # /link@<Lesson.id>
        link = mocker.patch("app.bot.commands.timetable.link",
                            side_effect=app.bot.commands.timetable.link)
        set_lesson_link = mocker.patch("app.bot.commands.timetable.set_lesson_link")

        link(update=update, ctx=ctx, session=db_session, user=user)
        assert set_lesson_link.call_count == 0
        assert update.message.reply_text.call_count == 1  # Error notification sent

    def test_link_without_moderator(self, db_session, mocker):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)
        lesson = LessonFactory(students_group=group)
        db_session.commit()

        update = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.match.group.return_value = lesson.id  # /link@<Lesson.id>
        link = mocker.patch("app.bot.commands.timetable.link",
                            side_effect=app.bot.commands.timetable.link)
        set_lesson_link = mocker.patch("app.bot.commands.timetable.set_lesson_link")

        link(update=update, ctx=ctx, session=db_session, user=user)
        assert set_lesson_link.call_count == 0

        assert update.message.reply_text.call_count == 1  # Error notification sent
        missing_moderator = update.message.reply_text.call_args_list[0]
        assert "Ваша група наразі не має модератора!" in missing_moderator.kwargs["text"]

    def test_set_lesson_link_init(self, db_session, mocker):
        """ Test `set_lesson_link` as it was called from `link` """

        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)
        lesson = LessonFactory(students_group=group)
        db_session.commit()

        update = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.user_data = {"lesson_id": lesson.id, "init": True}
        set_lesson_link = mocker.patch("app.bot.commands.timetable.set_lesson_link",
                                       side_effect=app.bot.commands.timetable.set_lesson_link)

        output = set_lesson_link(update=update, ctx=ctx, session=db_session, user=user)
        assert update.message.reply_text.call_count == 1
        assert output == states.LinkWait

        link_input = update.message.reply_text.call_args_list[0]
        assert link_input.kwargs["text"] == "Введіть посилання:"

    def test_set_lesson_link_request(self, db_session, mocker):
        """ Test `set_lesson_link` as it was called from `link` """

        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)
        lesson = LessonFactory(students_group=group)
        db_session.commit()

        update = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.user_data = {"lesson_id": lesson.id, "init": False}
        update.message.text = link = "https://zoom.com"
        set_lesson_link = mocker.patch("app.bot.commands.timetable.set_lesson_link",
                                       side_effect=app.bot.commands.timetable.set_lesson_link)
        send_request = mocker.patch("app.bot.commands.timetable.send_request")

        output = set_lesson_link(update=update, ctx=ctx, session=db_session, user=user)

        assert output == states.END
        assert send_request.call_count == 1

        request = send_request.call_args_list[0].kwargs["request"]

        assert request.initiator == user
        assert request.message == "@{username} хоче встановити нове посилання для <b>{" \
                                  "lesson}</b>:\n{link}" \
            .format(username=user.tg_username, lesson=str(lesson), link=link)
        assert request.meta == {"lesson_id": lesson.id, "link": link}
        assert request.students_group == user.students_group

    # TODO test end button
