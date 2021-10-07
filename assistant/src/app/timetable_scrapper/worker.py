"""
3rd-party timetable scrapper
Includes an entrypoint to run the program

Usage:
$ python assistant/timetable_scrapper/worker.py
"""

import datetime as dt
import json
import logging
import re
import urllib.parse
from typing import Any, Dict, Optional

import requests
from sqlalchemy.orm.session import Session as SqaSession

from app.database import (
    Faculty,
    Lesson,
    Session,
    SingleLesson,
    StudentsGroup,
    Teacher,
)

logger = logging.getLogger(__name__)
full_name_mask = re.compile(r"^\s*?([а-яїєі']+)\s*?([а-яїєі']+)\.?\s*?([а-яїєі']+)\.?\s*?$", re.I)


class TimetableScrapper:

    def __init__(self, db_session: Optional[SqaSession] = None):
        if db_session is None:
            db_session = Session()
        self.db = db_session

        self.session = requests.Session()

    def __del__(self):
        self.session.close()

    def run(self):
        self.db.query(SingleLesson).delete()

        raw_groups = self.get("https://api.mytimetable.live/rest/groups/", {"univ": 1})
        for raw_group in raw_groups["results"]:
            try:
                if not raw_group["name"].startswith("К-"):
                    continue

                raw_timetable = self.get("https://api.mytimetable.live/rest/timetable/",
                                         {"group": raw_group["slug"]})
                if raw_timetable is None or "lessons" not in raw_timetable.keys():
                    continue

                # Get/Create a faculty
                raw_faculty = raw_timetable["lessons"][0]["faculty"]
                faculty = self.db.query(Faculty).filter(Faculty.name == raw_faculty["name"]).first()
                if faculty is None:
                    faculty = Faculty(
                        name=raw_faculty["name"],
                        shortcut=raw_faculty["short_name"] or raw_faculty["name"],
                    )
                    self.db.add(faculty)
                    self.db.flush()

                # Get/Create a group
                group = self.db.query(StudentsGroup).filter_by(
                    name=raw_group["name"],
                    course=int(raw_group["course_name"]),
                    faculty=faculty,
                ).first()
                if group is None:
                    group = StudentsGroup(
                        name=raw_group["name"],
                        course=int(raw_group["course_name"]),
                        faculty=faculty,
                    )
                    self.db.add(group)
                    self.db.flush()
                group_timetable = dict()  # {(theme, teachers, subgroup, format): [raw_lessons]}

                for raw_lesson in raw_timetable["lessons"]:
                    subgroup = (raw_lesson["subgroup"] or "").strip() or None

                    # Unique Lesson key
                    lesson_key = (raw_lesson["name_full"], subgroup, raw_lesson["format"])
                    if group_timetable.get(lesson_key, None) is None:
                        lesson = self.db.query(Lesson).filter_by(
                            name=raw_lesson["name_full"],
                            students_group=group,
                            subgroup=subgroup,
                            lesson_format=raw_lesson["format"],
                        ).first()
                        if lesson is None:
                            lesson = Lesson(
                                name=raw_lesson["name_full"],
                                students_group=group,
                                subgroup=subgroup,
                                lesson_format=raw_lesson["format"],
                            )
                            self.db.add(lesson)
                            # Attach teachers to the lesson
                            for raw_teacher in raw_lesson["teachers"]:
                                match = full_name_mask.match(raw_teacher["full_name"])
                                if match is not None:
                                    last_name, first_name, middle_name = match.groups()
                                else:
                                    last_name, first_name, middle_name = raw_teacher["full_name"], "", ""
                                teacher = self.db.query(Teacher) \
                                    .filter_by(last_name=last_name, first_name=first_name,
                                               middle_name=middle_name) \
                                    .first()
                                if teacher is None:
                                    teacher = Teacher(
                                        last_name=last_name,
                                        first_name=first_name,
                                        middle_name=middle_name,
                                    )
                                    self.db.add(teacher)
                                lesson.teachers.append(teacher)
                            self.db.flush()
                        group_timetable[lesson_key] = lesson

                    starts_at = None
                    ends_at = None
                    for lesson_time in raw_timetable["lesson_time"]:
                        if lesson_time["id"] == raw_lesson["lesson_time"]:
                            starts_at = dt.datetime.strptime(lesson_time["start"], "%H:%M").time()
                            ends_at = dt.datetime.strptime(lesson_time["end"], "%H:%M").time()
                            break

                    for date in raw_lesson["dates"]:
                        single_lesson = SingleLesson(
                            lesson=group_timetable[lesson_key],
                            date=dt.datetime.strptime(date, "%Y-%m-%d").date(),
                            starts_at=starts_at,
                            ends_at=ends_at,
                        )
                        # l = group_timetable[lesson_key]
                        # if dt.datetime.strptime(date, "%Y-%m-%d").date() == dt.date(2021, 1, 27) \
                        #         and starts_at == dt.time(12, 20) \
                        #         and ends_at == dt.time(13, 55) \
                        #         and l.name == "Чисельний аналіз":
                        #     logger.info("{} {} ({})".format(single_lesson.lesson,
                        #     single_lesson, raw_lesson))
                        self.db.add(single_lesson)
                        self.db.flush()
            except Exception as e:
                logger.error("got error while parsing %s: %s", raw_group.get("name", None), str(e))
                continue
            else:
                continue
        self.db.commit()

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if params is not None and len(params) > 0:
            parts = list(urllib.parse.urlparse(url))
            q = dict(urllib.parse.parse_qsl(parts[4]))
            q.update(params)
            parts[4] = urllib.parse.urlencode(q)
            url = urllib.parse.urlunparse(parts)

        response = self.session.get(url)
        if response.status_code < 200 or response.status_code >= 300:
            # logger.error("got error fetching {} ({}): {}".format(url, response.status_code,
            # response.content))
            return None
        try:
            body: Dict = response.json()
            # processing multiple pages
            if body.get("next", None) is not None:
                extension = self.get(body["next"])
                if extension is not None:
                    # join two responses
                    for k, v in extension.items():
                        if k in body.keys():
                            if isinstance(v, dict):
                                for vk, vv in v.items():
                                    if vk not in body[k].keys():
                                        body[k][vk] = vv
                            elif isinstance(v, list):
                                for vv in v:
                                    if vv not in body[k]:
                                        body[k].append(vv)
                        else:
                            body[k] = v
            return body
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("got error parsing json %s: %s", url, str(e))
            return None


if __name__ == '__main__':
    # TODO: argparse
    scrapper = TimetableScrapper()
    scrapper.run()
