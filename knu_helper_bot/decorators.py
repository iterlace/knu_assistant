from functools import wraps

from telegram import Update
from sqlalchemy.sql import select, insert, update, delete

from database import Session
from database import User


def db_session(func):
    """ Pushes 'session' argument to a function """

    @wraps(func)
    def inner(*args, **kwargs):
        if "session" in kwargs:
            return func(*args, **kwargs)

        kwargs.update({
            "session": Session(),
        })
        return func(*args, **kwargs)
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

        update: Update = kwargs.get("update", args[0])
        session: Session = kwargs.get("session")

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

        kwargs.update({
            "user": user,
        })
        return func(*args, **kwargs)

    return inner
