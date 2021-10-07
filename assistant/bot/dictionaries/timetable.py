"""
Basic timetable constants
Contains:
 - LESSON_TYPES - University lessons types with their names and representations
"""

import re
from typing import Dict

time_span_pattern = re.compile(r"^\s*?((\d{,2})[.:](\d{2}))\s*?-?\s*?((\d{,2})[.:](\d{2}))\s*?$")

__all__ = ["LECTURE", "PRACTICAL", "LABORATORY_WORK", "FACULTATIVE", "LESSON_TYPES"]


class LessonType(str):
    # Full name
    name = None

    # Abbreviation
    abbr = None

    # Latin name
    keyword = None

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

LESSON_TYPES: Dict[str, LessonType] = {i.keyword: i for i in
                                       (LECTURE, PRACTICAL, LABORATORY_WORK, FACULTATIVE)}
