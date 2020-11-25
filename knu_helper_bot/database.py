
import logging

import sqlalchemy as sqa
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Sequence
from sqlalchemy.sql.sqltypes import *
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import knu_helper_bot.config as config

logger = logging.getLogger(__name__)


db = create_engine(config.DB_STRING, pool_size=20, max_overflow=0)
Base = declarative_base()
meta = MetaData(db)
Session = sessionmaker(bind=db)


class User(Base):
    __tablename__ = "users"

    tg_id = Column(
        Integer,
        autoincrement=False,
        primary_key=True,
    )
    tg_username = Column(
        String,
        nullable=False,
    )
    is_admin = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    students_group_id = Column(
        Integer,
        ForeignKey("students_groups.id"),
        nullable=True,
    )
    current_state = Column(
        String,
        nullable=True,
        default=None,
    )
    state_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    students_group = relationship("StudentsGroup", back_populates="students")

    def __repr__(self):
        return "<User(tg_id={}, tg_username={})".format(self.tg_id, self.tg_username)


class StudentsGroup(Base):
    __tablename__ = "students_groups"

    id = Column(
        Integer,
        primary_key=True,
    )
    name = Column(
        String,
        nullable=False,
    )

    students = relationship("User", order_by=User.tg_id, back_populates="students_group")

    def __repr__(self):
        return "<StudentsGroup(id={}, name={})>".format(self.id, self.name)


