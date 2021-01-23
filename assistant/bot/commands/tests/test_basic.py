from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from assistant import config
from assistant.database import User


class TestStart:

    @mark.asyncio
    async def test_start(self, client: TelegramClient, db_session, use_bot):

        async with client.conversation("@{}".format(config.BOT_NAME), timeout=5) as conv:
            await conv.send_message("/start")
            resp: Message = await conv.get_response()

            assert "Привіт!" in resp.raw_text
            assert db_session.query(User).get((await client.get_me()).id) is not None

