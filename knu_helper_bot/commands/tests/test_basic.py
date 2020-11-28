from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from knu_helper_bot import config


@mark.asyncio
async def test_start(client: TelegramClient, db_session):

    async with client.conversation("@{}".format(config.BOT_NAME), timeout=5) as conv:
        await conv.send_message("/start")
        resp: Message = await conv.get_response()

        assert "Привіт!" in resp.raw_text
