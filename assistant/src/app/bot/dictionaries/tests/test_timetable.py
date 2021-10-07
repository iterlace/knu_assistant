import pytest

from app.bot.dictionaries import timetable


class TestLessonType:

    def test_new(self):
        keyword = "test"
        name = "Test"
        abbr = "t."

        lesson_type = timetable.LessonType(keyword, name, abbr)
        assert lesson_type == keyword
        assert lesson_type.keyword == keyword
        assert lesson_type.name == name
        assert lesson_type.abbr == abbr
        assert isinstance(lesson_type, str)


@pytest.mark.parametrize("value", [
    "10:10 - 13:50",
    "10.10 - 13:50",
    "10.10 - 13.50",
    "  10:10-13:50  ",
])
def test_time_span_pattern(value):
    match = timetable.time_span_pattern.match(value)
    assert match is not None
    groups = match.groups()
    assert groups[1] == "10"
    assert groups[2] == "10"
    assert groups[4] == "13"
    assert groups[5] == "50"
