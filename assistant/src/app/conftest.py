import importlib
import logging
import os
import threading
from functools import wraps
from html import escape
from time import sleep

import mock
import pytest
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig
from pytest import mark
from sqlalchemy import event
from sqlalchemy.orm import Session as SqaSession
from telethon import TelegramClient
from telethon.extensions.html import _add_surrogate, _del_surrogate, helpers
from telethon.sessions import StringSession
from telethon.tl.types import (
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityCode,
    MessageEntityEmail,
    MessageEntityItalic,
    MessageEntityMentionName,
    MessageEntityPre,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUrl,
)

from app.database import Session

logger = logging.getLogger(__name__)

# Your API ID, hash and session string here
API_ID = int(os.environ["TELEGRAM_APP_ID"])
API_HASH = os.environ["TELEGRAM_APP_HASH"]
TG_SESSION = os.environ["TELETHON_SESSION"]

session = Session()


@event.listens_for(session, "after_transaction_end")
def restart_savepoint(session, transaction):
    """ Each time that SAVEPOINT ends, reopen it """
    if transaction.nested and not transaction._parent.nested:
        session.begin_nested()


def reload_db_session_decorator():
    import app
    importlib.reload(app.bot.commands.basic)
    importlib.reload(app.bot.commands.user)
    importlib.reload(app.bot.commands.timetable)
    importlib.reload(app.bot.commands.moderation)
    importlib.reload(app.bot.commands.utils)
    importlib.reload(app.bot.commands)


@pytest.fixture(scope="function")
def use_bot(db_session):
    """ Runs a telegram bot, which uses db session from the fixture """

    # Mock app.bot.decorators.db_session to be able to rollback the session after test
    # completed
    def mock_db_session(func):
        """ Pushes session, controlled by the fixture """

        @wraps(func)
        def inner(*args, **kwargs):
            kwargs["session"] = db_session
            return func(*args, **kwargs)

        return inner

    db_session_mock = mock.patch("app.bot.decorators.db_session", mock_db_session)
    db_session_mock.start()
    reload_db_session_decorator()

    # Start the bot in a separate thread

    stop_event = threading.Event()

    def bot_thread():
        from app.bot.worker import run
        updater = run()
        # stop the bot on signal
        stop_event.wait()

        # A trick to speed up updater.stop (9s vs 1ms)
        # Job queue and httpd, which can break further tests, are stopped in blocking mode,
        # but other parts would be terminated in a separate daemon.

        updater._stop_httpd()
        updater.job_queue.stop()
        stop_thread = threading.Thread(target=updater.stop, daemon=True)
        stop_thread.start()

    thread = threading.Thread(target=bot_thread)
    thread.start()

    yield

    stop_event.set()
    db_session_mock.stop()
    importlib.invalidate_caches()
    reload_db_session_decorator()

    while thread.is_alive():
        sleep(0.01)


@pytest.fixture()
@mark.asyncio
async def client() -> TelegramClient:
    def unparse(text, entities, _offset=0, _length=None) -> str:
        """
        Modification of telethon.extensions.html.unparse
        Bold is now interpreted as <b></b>
        Italic is now interpreted as <i></i>
        """
        if not text:
            return text
        elif not entities:
            return escape(text)

        text = _add_surrogate(text)
        if _length is None:
            _length = len(text)
        html = []
        last_offset = 0
        for i, entity in enumerate(entities):
            if entity.offset >= _offset + _length:
                break
            relative_offset = entity.offset - _offset
            if relative_offset > last_offset:
                html.append(escape(text[last_offset:relative_offset]))
            elif relative_offset < last_offset:
                continue

            skip_entity = False
            length = entity.length

            while helpers.within_surrogate(text, relative_offset, length=_length):
                relative_offset += 1

            while helpers.within_surrogate(text, relative_offset + length, length=_length):
                length += 1

            entity_text = unparse(text=text[relative_offset:relative_offset + length],
                                  entities=entities[i + 1:],
                                  _offset=entity.offset, _length=length)
            entity_type = type(entity)

            if entity_type == MessageEntityBold:
                html.append('<b>{}</b>'.format(entity_text))
            elif entity_type == MessageEntityItalic:
                html.append('<i>{}</i>'.format(entity_text))
            elif entity_type == MessageEntityCode:
                html.append('<code>{}</code>'.format(entity_text))
            elif entity_type == MessageEntityUnderline:
                html.append('<u>{}</u>'.format(entity_text))
            elif entity_type == MessageEntityStrike:
                html.append('<del>{}</del>'.format(entity_text))
            elif entity_type == MessageEntityBlockquote:
                html.append('<blockquote>{}</blockquote>'.format(entity_text))
            elif entity_type == MessageEntityPre:
                if entity.language:
                    html.append(
                        "<pre>\n    <code class='language-{}'>\n        {}\n    </code>\n</pre>"
                            .format(entity.language, entity_text))
                else:
                    html.append('<pre><code>{}</code></pre>'.format(entity_text))
            elif entity_type == MessageEntityEmail:
                html.append('<a href="mailto:{0}">{0}</a>'.format(entity_text))
            elif entity_type == MessageEntityUrl:
                html.append('<a href="{0}">{0}</a>'.format(entity_text))
            elif entity_type == MessageEntityTextUrl:
                html.append('<a href="{}">{}</a>'.format(escape(entity.url), entity_text))
            elif entity_type == MessageEntityMentionName:
                html.append('<a href="tg://user?id={}">{}</a>'.format(entity.user_id, entity_text))
            else:
                skip_entity = True
            last_offset = relative_offset + (0 if skip_entity else length)

        while helpers.within_surrogate(text, last_offset, length=_length):
            last_offset += 1

        html.append(escape(text[last_offset:]))
        return _del_surrogate(''.join(html))

    unparse_mock = mock.patch("telethon.extensions.html.unparse", unparse)
    unparse_mock.start()
    client = TelegramClient(
        StringSession(TG_SESSION), API_ID, API_HASH,
        sequential_updates=True,
    )
    client.parse_mode = "html"

    # Connect to the server
    await client.connect()
    # Issue a high level command to start receiving message
    await client.get_me()
    # Fill the entity cache
    await client.get_dialogs()

    yield client

    unparse_mock.stop()
    await client.disconnect()
    await client.disconnected


@pytest.fixture(scope="session")
def db():
    alembic_config = AlembicConfig("migrations/alembic.ini")
    # Run alembic migrations
    alembic_upgrade(alembic_config, "head")

    yield


@pytest.fixture(scope="function", autouse=True)
def db_session(db) -> SqaSession:
    global session
    session.invalidate()
    session.begin_nested()  # Savepoint

    yield session

    session.rollback()
    session.invalidate()
