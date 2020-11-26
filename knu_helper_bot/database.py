
import logging

import sqlalchemy as sqa
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Sequence, UniqueConstraint
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
    timetable_lessons = relationship("TimetableLesson", back_populates="students_group")

    def __repr__(self):
        return "<StudentsGroup(id={}, name={})>".format(self.id, self.name)


class TimetableLesson(Base):
    __tablename__ = "timetable_lessons"

    id = Column(
        Integer,
        primary_key=True,
    )
    day_of_week = Column(
        SmallInteger,
        nullable=False,
    )
    starts_at = Column(
        Time,
        nullable=False,
    )
    ends_at = Column(
        Time,
        nullable=False,
    )
    students_group_id = Column(
        Integer,
        ForeignKey("students_groups.id"),
        nullable=False,
    )
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id"),
        nullable=False,
    )
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id"),
        nullable=False,
    )

    students_group = relationship("StudentsGroup", back_populates="timetable_lessons")
    teacher = relationship("Teacher")
    lesson = relationship("Lesson")

    __table_args__ = (
        # UniqueConstraint("day_of_week", "students_group_id", name="timetable_dow_students_group_key"),
    )

    def __repr__(self):
        return "<TimetableDay(id={}, day_of_week={}, group={})>"\
            .format(self.id, self.day_of_week, self.students_group_id)


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(
        Integer,
        primary_key=True,
    )
    name = Column(
        String,
        nullable=False,
    )

    def __repr__(self):
        return "<Lesson(id={}, name={})>".format(self.id, self.name)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(
        Integer,
        primary_key=True,
    )
    first_name = Column(
        String,
        nullable=False,
    )
    last_name = Column(
        String,
        nullable=False,
    )
    middle_name = Column(
        String,
        nullable=False,
    )

    def __repr__(self):
        return "<Lesson(id={}, first_name={}, last_name={}, middle_name={})>"\
            .format(self.id, self.first_name, self.last_name, self.middle_name)

    def full_name(self):
        return " ".join((self.last_name, self.first_name, self.middle_name))

