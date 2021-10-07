import datetime as dt
import logging
from functools import wraps

from sqlalchemy.orm import Session as SqaSession
from telegram import Update

from app.database import Session, User

logger = logging.getLogger()


def db_session(func):
    """ Pushes 'session' argument to a function """

    @wraps(func)
    def inner(*args, **kwargs):
        if "session" in kwargs:
            return func(*args, **kwargs)
        session = Session()
        kwargs.update({
            "session": session,
        })
        output = func(*args, **kwargs)
        session.close()
        return output

    return inner


def acquire_user(func):
    """
    Pushes 'user' argument to a function.
    Creates or updates User if needed.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        if "user" in kwargs:
            return func(*args, **kwargs)

        update: Update = kwargs.get("update", None)
        if update is None:
            update = args[0]
        session: SqaSession = kwargs.get("session")

        user = session.query(User).get(update.effective_user.id)
        if user is None:
            user = User(
                tg_id=update.effective_user.id,
                tg_username=update.effective_user.username,
            )
            session.add(user)
            session.commit()

        if user.tg_username != update.effective_user.username:
            user.tg_username = update.effective_user.username
            session.commit()

        user.last_active = dt.datetime.now()
        session.commit()

        kwargs.update({
            "user": user,
        })
        return func(*args, **kwargs)

    return inner


def moderators_only(func):
    @wraps(func)
    def inner(*args, user, **kwargs):
        if user.is_group_moderator:
            return func(*args, user=user, **kwargs)
        return None

    return inner


def admins_only(func):
    @wraps(func)
    def inner(*args, user, **kwargs):
        if user.is_admin:
            return func(*args, user=user, **kwargs)
        return None

    return inner


# TODO
def moderation_accept(func):
    @wraps(func)
    def inner(update, ctx, session, **kwargs):
        pass

    return inner


# TODO
def moderation_reject(func):
    @wraps(func)
    def inner(update, ctx, session, **kwargs):
        pass

    return inner
