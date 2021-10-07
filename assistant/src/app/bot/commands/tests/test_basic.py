import asyncio

from pytest import mark, raises
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from app.core.config import settings
from app.bot.commands.tests.utils import flatten_keyboard
from app.database import User
from app.tests.factories import (
    FacultyFactory,
    LessonFactory,
    StudentsGroupFactory,
    TeacherFactory,
    UserFactory,
)


class TestStart:

    @mark.asyncio
    async def test_full_conversation(self, client: TelegramClient, db_session, use_bot):
        """ Test /start """

        # faculty that would be selected
        csc = FacultyFactory(name="CSC", shortcut="CSC")

        # group that would be selected
        group = StudentsGroupFactory(course=1, faculty=csc)

        # Programming lesson, divided into 2 subgroups
        koval = TeacherFactory()
        kondratyuk = TeacherFactory()
        programming_1 = LessonFactory(teachers=[koval], subgroup="1",
                                      name="P", lesson_format=1, students_group=group)
        programming_2 = LessonFactory(teachers=[kondratyuk], subgroup="2",
                                      name="P", lesson_format=1, students_group=group)
        db_session.commit()

        async with client.conversation("@{}".format(settings.TELEGRAM_BOT_NAME), timeout=5) as conv:
            await conv.send_message("/start")
            r: Message

            r = await conv.get_response()
            assert "КНУ.Органайзер" in r.raw_text
            assert db_session.query(User).get((await client.get_me()).id) is not None

            # skip the second message
            await conv.get_response()

            # course choice
            r = await conv.get_response()
            # TODO: assert change_group was called
            kb = flatten_keyboard(r.buttons)
            assert "курс" in r.raw_text.lower()
            assert len(kb) == 1  # only 1st course is present
            await r.click(data=b"1")

            # faculty choice
            r = await conv.get_edit()
            kb = flatten_keyboard(r.buttons)
            assert "факультет" in r.raw_text.lower()
            assert len(kb) == 1  # only CSC is present
            # select "CSC"
            await r.click(data=str(csc.id).encode("utf-8"))

            # group choice
            r = await conv.get_edit()
            kb = flatten_keyboard(r.buttons)
            assert "груп" in r.raw_text.lower()
            assert len(kb) == 1  # ensure extra_groups are excluded from this list
            # select group
            await r.click(data=str(group.id).encode("utf-8"))

            r = await conv.get_edit()
            assert r.text == "Групу встановлено!"

            # programming subgroup choice
            r = await conv.get_response()
            kb = flatten_keyboard(r.buttons)
            assert "підгрупу з {name} ({format})".format(name=programming_1.name,
                                                         format=programming_1.lesson_format) \
                   in r.raw_text
            await kb[0].click()

            r = await conv.get_edit()
            assert r.text == "Підгрупи визначено!"

    @mark.asyncio
    async def test_active_user(self, client: TelegramClient, db_session, use_bot):
        """ Test /start by already registered user """

        # group that would be selected
        group = StudentsGroupFactory(course=1)

        # Current user
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)

        db_session.commit()

        async with client.conversation("@{}".format(settings.TELEGRAM_BOT_NAME), timeout=5) as conv:
            await conv.send_message("/start")
            r = await conv.get_response()
            # Ensure it is not common response
            assert "Привіт!" not in r.raw_text

            # ensure only one message is sent
            with raises(asyncio.TimeoutError):
                await conv.get_response(timeout=1)
