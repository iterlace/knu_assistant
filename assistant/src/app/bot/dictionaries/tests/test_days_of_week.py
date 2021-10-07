from app.bot.dictionaries import week


class TestDayOfWeek:

    def test_new(self):
        day = week.DayOfWeek(0, "Monday")
        assert day == 0
        assert day.name == "Monday"
        assert isinstance(day, int)
