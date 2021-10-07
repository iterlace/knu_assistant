import datetime as dt
import logging

from sqlalchemy import (
    Column,
    ForeignKey,
    MetaData,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Integer, String, Text, Time

from app.core.config import settings

logger = logging.getLogger(__name__)

db = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_size=40, max_overflow=10)
Base = declarative_base()
meta = MetaData(db)
Session = sessionmaker(bind=db, autoflush=False)


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
    last_active = Column(
        DateTime,
        nullable=False,
        default=dt.datetime.now,
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
    requests = relationship("Request", back_populates="students_group")

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
    comment = Column(
        String,
        nullable=True,
    )

    lesson = relationship("Lesson")

    __table_args__ = (
        UniqueConstraint("lesson_id", "date", "starts_at", "ends_at",
                         name="timetable_lesson_complex_key"),
    )

    def __repr__(self):
        return "<SingleLesson(id={}, lesson_id={}, date={}, starts_at={})>" \
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
    link = Column(
        String,
        nullable=True,
    )
    teachers = relationship(
        "Teacher",
        secondary=LessonTeacher,
        backref="lessons",
    )

    students_group = relationship("StudentsGroup", back_populates="lessons")

    __table_args__ = (
        UniqueConstraint("name", "subgroup", "students_group_id", "lesson_format",
                         name="lesson_complex_key"),
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

    def __str__(self):
        name = "{}".format(self.name)
        if self.subgroup is not None:
            teachers = ", ".join([t.short_name for t in self.teachers])
            name += " ({}, {})".format(self.represent_lesson_format(), teachers)

        return name


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
        return "<Teacher(id={}, first_name={}, last_name={}, middle_name={})>" \
            .format(self.id, self.first_name, self.last_name, self.middle_name)

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return " ".join((self.last_name, self.first_name, self.middle_name)).strip()

    @property
    def short_name(self):
        if self.first_name and self.middle_name:
            return "{} {}. {}.".format(self.last_name, self.first_name[0], self.middle_name[0])
        return self.last_name


class Request(Base):
    """
    Requests from common users to students group moderator
    to change something in a timetable, post some messages to the channel, etc
    """
    __tablename__ = "requests"

    id = Column(
        Integer,
        primary_key=True,
    )

    # student group this request relates to
    students_group_id = Column(
        Integer,
        ForeignKey("students_groups.id"),
        nullable=False,
    )

    # user who proposed this request
    initiator_id = Column(
        Integer,
        ForeignKey("users.tg_id"),
        nullable=False,
    )

    # moderator who received this request
    moderator_id = Column(
        Integer,
        ForeignKey("users.tg_id"),
        nullable=False,
    )

    # text of the moderator message
    message = Column(
        Text,
        nullable=False,
    )

    # callback data for the 'Accept' button
    accept_callback = Column(
        Text,
        nullable=False,
    )

    # callback data for the 'Reject' button
    reject_callback = Column(
        Text,
        nullable=False,
    )

    # request meta (e.g. {"lesson_id": 1, "link": "https://dc.zoom.us/xxx"})
    meta = Column(
        pg.JSONB,
        nullable=False,
    )

    is_resolved = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    students_group = relationship("StudentsGroup", back_populates="requests")
    initiator = relationship("User", foreign_keys=[initiator_id])
    moderator = relationship("User", foreign_keys=[moderator_id])

    def __repr__(self):
        return "<Request(id={}, students_group_id={})>" \
            .format(self.id, self.students_group_id)
