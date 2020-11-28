from pytest import mark

from knu_helper_bot.dictionaries.days_of_week import DayOfWeek


class TestDayOfWeek:

    def test_new(self):
        day = DayOfWeek(0, "Monday")
        assert day == 0
        assert day.name == "Monday"
        assert isinstance(day, int)
