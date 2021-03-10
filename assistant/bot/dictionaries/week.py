""" Days of week constants with their indexes and representations """


class DayOfWeek(int):
    name = None

    def __new__(cls, idx: int, name: str):
        obj = super().__new__(cls, idx)
        obj.name = name
        return obj


MONDAY = DayOfWeek(0, "Понеділок")
TUESDAY = DayOfWeek(1, "Вівторок")
WEDNESDAY = DayOfWeek(2, "Середа")
THURSDAY = DayOfWeek(3, "Четвер")
FRIDAY = DayOfWeek(4, "П'ятниця")
SATURDAY = DayOfWeek(5, "Субота")
SUNDAY = DayOfWeek(6, "Неділя")

LIST = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
