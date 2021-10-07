import datetime as dt
import random
import string

import factory
import factory.fuzzy as fuzzy
from factory.alchemy import SQLAlchemyModelFactory

from app.conftest import session
from app.database import (  # M2M
    Faculty,
    Lesson,
    Request,
    SingleLesson,
    StudentsGroup,
    Teacher,
    User,
)


class FacultyFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Faculty
        sqlalchemy_session = session

    name = fuzzy.FuzzyText(length=20, chars=string.ascii_letters + " ")
    shortcut = fuzzy.FuzzyText(length=4, chars=string.ascii_uppercase)


class TeacherFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Teacher
        sqlalchemy_session = session

    first_name = fuzzy.FuzzyText(length=7, chars=string.ascii_letters)
    last_name = fuzzy.FuzzyText(length=7, chars=string.ascii_letters)
    middle_name = fuzzy.FuzzyText(length=7, chars=string.ascii_letters)


class StudentsGroupFactory(SQLAlchemyModelFactory):
    class Meta:
        model = StudentsGroup
        sqlalchemy_session = session

    name = fuzzy.FuzzyText(length=4, chars=string.ascii_uppercase + string.digits)
    course = fuzzy.FuzzyInteger(low=1, high=4)
    faculty = factory.SubFactory(FacultyFactory)


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = session

    tg_id = fuzzy.FuzzyInteger(low=100000000)
    tg_username = fuzzy.FuzzyText()
    is_admin = factory.LazyFunction(lambda: False)
    is_group_moderator = factory.LazyFunction(lambda: False)
    students_group = factory.SubFactory(StudentsGroupFactory)


class LessonFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Lesson
        sqlalchemy_session = session

    name = fuzzy.FuzzyText(length=15, chars=string.ascii_letters + " ")
    students_group = factory.SubFactory(StudentsGroupFactory)
    subgroup = factory.LazyFunction(lambda: None)
    lesson_format = fuzzy.FuzzyInteger(low=0, high=4)

    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            for teacher in extracted:
                self.teachers.append(teacher)
        else:
            teacher = TeacherFactory.create()
            self.teachers.append(teacher)


class SingleLessonFactory(SQLAlchemyModelFactory):
    class Meta:
        model = SingleLesson
        sqlalchemy_session = session

    date = fuzzy.FuzzyDate(start_date=dt.date(2021, 1, 25),
                           end_date=dt.date(2021, 2, 25))
    lesson = factory.SubFactory(LessonFactory)

    @factory.post_generation
    def starts_at(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            self.starts_at = extracted
        else:
            choices = [
                dt.time(hour=8, minute=40),
                dt.time(hour=10, minute=35),
                dt.time(hour=12, minute=20),
                dt.time(hour=14, minute=5),
            ]
            self.starts_at = random.choice(choices)

    @factory.post_generation
    def ends_at(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            self.ends_at = extracted
        else:
            starts_dt = dt.datetime(1970, 1, 1, self.starts_at.hour, self.starts_at.minute)
            ends_dt = starts_dt + dt.timedelta(hours=1, minutes=30)
            self.ends_at = ends_dt.time()


class RequestFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Request
        sqlalchemy_session = session

    initiator = factory.SubFactory(UserFactory)
    moderator = factory.SubFactory(UserFactory)
    message = fuzzy.FuzzyText(length=50)
    accept_callback = "accept_test_1"
    reject_callback = "reject_test_1"
    meta = factory.LazyFunction(lambda: dict())
    is_resolved = False

    @factory.post_generation
    def students_group(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            self.students_group = extracted
        else:
            if self.initiator is not None:
                self.students_group = self.initiator.students_group
            else:
                self.students_group = StudentsGroupFactory()
