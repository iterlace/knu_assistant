from sqlalchemy.orm import Session

from app.tests.factories import LessonFactory, TeacherFactory


class TestLesson:

    def test_str_without_teachers(self, db_session: Session):
        lesson = LessonFactory(name="Math")
        db_session.commit()
        assert str(lesson) == "Math"

    def test_str_with_teacher(self, db_session: Session):
        tom = TeacherFactory(first_name="Tom", middle_name="O", last_name="Peterson")
        lesson = LessonFactory(name="Math", subgroup="1", teachers=[tom])
        db_session.commit()
        assert str(lesson) == "Math ({lesson_format}, Peterson T. O.)" \
            .format(lesson_format=lesson.represent_lesson_format())

    def test_str_with_multiple_teachers(self, db_session: Session):
        tom = TeacherFactory(first_name="Tom", middle_name="O", last_name="Peterson")
        jack = TeacherFactory(first_name="Jack", middle_name="O", last_name="Smith")
        lesson = LessonFactory(name="Math", subgroup="1", teachers=[tom, jack])
        db_session.commit()
        assert str(lesson) == "Math ({lesson_format}, Peterson T. O., Smith J. O.)" \
            .format(lesson_format=lesson.represent_lesson_format())


class TestTeacher:

    def test_str(self):
        teacher = TeacherFactory()
        assert str(teacher) == teacher.full_name

    def test_full_name(self):
        tom = TeacherFactory(first_name="Tom", middle_name="O", last_name="Peterson")
        assert tom.full_name == "Peterson Tom O"

    def test_short_name(self):
        tom = TeacherFactory(first_name="Tom", middle_name="O", last_name="Peterson")
        assert tom.short_name == "Peterson T. O."

    def test_poor_short_name(self):
        peterson = TeacherFactory(first_name="", middle_name="", last_name="Peterson")
        assert peterson.short_name == "Peterson"

        smith = TeacherFactory(first_name="Tom", middle_name="", last_name="Smith")
        assert smith.short_name == "Smith"

        jones = TeacherFactory(first_name="", middle_name="O", last_name="Jones")
        assert jones.short_name == "Jones"
