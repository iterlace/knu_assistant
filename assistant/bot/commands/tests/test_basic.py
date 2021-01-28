from datetime import datetime

from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from assistant import config
from assistant.database import User
from assistant.bot.commands.tests.utils import flatten_keyboard
from assistant.database import StudentsGroup, Faculty


class TestStart:

    @mark.asyncio
    async def test_full_conversation(self, client: TelegramClient, db_session, use_bot,
                                     fill_groups, fill_faculties):

        async with client.conversation("@{}".format(config.BOT_NAME), timeout=5) as conv:
            await conv.send_message("/start")
            r: Message

            r = await conv.get_response()
            assert "Привіт!" in r.raw_text
            assert db_session.query(User).get((await client.get_me()).id) is not None

            # skip the second message
            await conv.get_response()

            # course choice
            r = await conv.get_response()
            kb = flatten_keyboard(await r.get_buttons())
            assert "курс" in r.raw_text.lower()
            assert len(kb) == 1  # only one course is present in the database
            # select 1st course
            await kb[0].click()

            # faculty choice
            r = await conv.get_edit()
            kb = flatten_keyboard(await r.get_buttons())
            assert "факультет" in r.raw_text.lower()
            assert len(kb) == len(fill_faculties)
            # select "CSC"
            selected_faculty_id = kb[0].data.decode("utf-8")
            await r.click(data=selected_faculty_id.encode("utf-8"))

            # group choice
            r = await conv.get_edit()
            kb = flatten_keyboard(await r.get_buttons())
            available_groups = db_session.query(StudentsGroup).filter_by(faculty_id=selected_faculty_id)
            selected_group = available_groups.first()
            assert "груп" in r.raw_text.lower()
            assert len(kb) == available_groups.count()
            # select "K-11"
            await r.click(data=str(selected_group.id).encode("utf-8"))

            # TODO: subgroup tests
            # real_group_id = (
            #     db_session
            #     .query(User.students_group_id)
            #     .filter(User.tg_id==(await client.get_me()).id)
            #     .first()[0]
            # )
            # assert real_group_id == selected_group.id


