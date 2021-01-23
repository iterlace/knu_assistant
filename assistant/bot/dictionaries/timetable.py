import re
from typing import Dict

time_span_pattern = re.compile(r"^\s*?((\d{,2})[.:](\d{2}))\s*?-?\s*?((\d{,2})[.:](\d{2}))\s*?$")


class LessonType(str):
    name = None     # Full name
    abbr = None     # Abbreviation
    keyword = None  # Latin name

    def __new__(cls, keyword, name, abbr):
        """
        """
        obj = super().__new__(cls, keyword)
        obj.keyword = keyword
        obj.name = name
        obj.abbr = abbr
        return obj


LECTURE = LessonType("lecture", "Лекція", "лек")
PRACTICAL = LessonType("practice", "Практика", "прак")
LABORATORY_WORK = LessonType("laboratory_work", "Лабораторна", "лаб")
FACULTATIVE = LessonType("facultative", "Факультатив", "фак")

LESSON_TYPES: Dict[str, LessonType] = {i.keyword: i for i in (LECTURE, PRACTICAL, LABORATORY_WORK, FACULTATIVE)}
