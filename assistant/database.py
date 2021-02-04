
import logging

import sqlalchemy as sqa
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Sequence, UniqueConstraint
from sqlalchemy.sql.sqltypes import *
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.sql import text

import assistant.config as config

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
    students_group_id = Column(
        Integer,
        ForeignKey("students_groups.id"),
        nullable=True,
    )
    is_admin = Column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_group_moderator = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    students_group = relationship("StudentsGroup", back_populates="students")
    subgroups = relationship("Lesson",
                             secondary="lessons_subgroups_members",
                             backref=backref("students", lazy="dynamic"),
                             )

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
    course = Column(
        Integer,
        nullable=False,
    )
    faculty_id = Column(
        Integer,
        ForeignKey("faculties.id"),
        nullable=False,
    )

    students = relationship("User", order_by=User.tg_id, back_populates="students_group")
    lessons = relationship("Lesson", back_populates="students_group")
    faculty = relationship("Faculty", back_populates="groups")

    def __repr__(self):
        return "<StudentsGroup(id={}, name={})>".format(self.id, self.name)


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(
        Integer,
        primary_key=True,
    )
    name = Column(
        String,
        nullable=False,
        unique=True,
    )
    shortcut = Column(
        String,
        nullable=False,
    )

    groups = relationship("StudentsGroup", back_populates="faculty")

    def __repr__(self):
        return "<Faculty(id={}, name={})>".format(self.id, self.name)


class SingleLesson(Base):
    __tablename__ = "single_lessons"

    id = Column(
        Integer,
        primary_key=True,
    )
    date = Column(
        Date,
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
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id"),
        nullable=False,
    )

    lesson = relationship("Lesson")

    __table_args__ = (
        UniqueConstraint("lesson_id", "date", "starts_at", "ends_at", name="timetable_lesson_complex_key"),
    )

    def __repr__(self):
        return "<SingleLesson(id={}, lesson_id={}, date={}, starts_at={})>"\
            .format(self.id, self.lesson_id, self.date, self.starts_at)


LessonTeacher = Table(
    "lessons_teachers", Base.metadata,
    Column("lesson_id", Integer, ForeignKey("lessons.id")),
    Column("teacher_id", Integer, ForeignKey("teachers.id")),
)


# If lesson is divided into subgroups, match each one with its members (users)
LessonSubgroupMember = Table(
    "lessons_subgroups_members", Base.metadata,
    Column("lesson_id", Integer, ForeignKey("lessons.id")),
    Column("user_id", Integer, ForeignKey("users.tg_id")),
)


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
    students_group_id = Column(
        Integer,
        ForeignKey("students_groups.id"),
        nullable=False,
    )
    subgroup = Column(
        String,
        nullable=True,
    )
    # 0 - lecture, 1 - seminar, 2 - practical, 3 - lab, 4 - other
    lesson_format = Column(
        Integer,
        nullable=False,
    )
    teachers = relationship(
        "Teacher",
        secondary=LessonTeacher,
        backref="lessons",
    )

    students_group = relationship("StudentsGroup", back_populates="lessons")

    __table_args__ = (
        UniqueConstraint("name", "subgroup", "students_group_id", "lesson_format", name="lesson_complex_key"),
    )

    def represent_lesson_format(self):
        # TODO: move to enum with representation ability
        names = {
            0: "лекція",
            1: "семінар",
            2: "практика",
            3: "лабораторна",
            4: "інш.",
        }
        return names[self.lesson_format]

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

    @property
    def full_name(self):
        return " ".join((self.last_name, self.first_name, self.middle_name)).strip()

    @property
    def short_name(self):
        if self.first_name and self.middle_name:
            return "{} {}. {}.".format(self.last_name, self.first_name[0], self.middle_name[0])
        else:
            return self.last_name
