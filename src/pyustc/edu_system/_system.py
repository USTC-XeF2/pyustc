import requests
from typing import Literal
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ..url import generate_url
from ..passport import Passport
from ._course import CourseTable
from ._grade import GradeManager
from ._select import CourseSelectionSystem
from ._adjust import CourseAdjustmentSystem

_ua = UserAgent(platforms="desktop")

SEMESTER = tuple[int, Literal["春", "夏", "秋"]] | Literal["now"]

class EduSystem:
    _semesters = dict[SEMESTER, int]()
    def __init__(self, passport: Passport):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = _ua.random
        ticket = passport.get_ticket(generate_url("edu_system", "ucas-sso/login"))
        res = self._request("ucas-sso/login", params = {"ticket": ticket})
        if not res.url.endswith("home"):
            msg = "Failed to login, maybe the passport doesn't have the permission and you need to login by browser"
            raise RuntimeError(msg)

        res = self._request("for-std/course-table")
        self._student_id = res.url.split("/")[-1]
        if not self._student_id.isdigit():
            raise RuntimeError("Failed to get student id")
        if not self._semesters:
            self._set_semesters(res.text)

    @classmethod
    def _set_semesters(cls, html: str):
        soup = BeautifulSoup(html, "html.parser")
        for option in soup.select("#allSemesters > option"):
            value = int(option["value"])
            year, season = option.text.split("年")
            cls._semesters[(int(year), season[0])] = value
            if "selected" in option.attrs:
                cls._semesters["now"] = value

    def _request(self, url: str, method: str = "get", **kwargs):
        return self.session.request(
            method,
            generate_url("edu_system", url),
            **kwargs
        )

    def get_current_teach_week(self) -> int:
        """
        Get the current teaching week.
        """
        res = self._request("home/get-current-teach-week")
        return res.json()["weekIndex"]

    def get_course_table(self, week: int = None, semester: SEMESTER = "now"):
        """
        Get the course table for the specified week and semester.
        """
        url = f"for-std/course-table/semester/{self._semesters[semester]}/print-data/{self._student_id}"
        params = {
            "weekIndex": week or ""
        }
        res = self._request(url, params = params)
        return CourseTable(res.json()["studentTableVm"], week)

    def get_grade_manager(self):
        return GradeManager(self._request)

    def get_open_turns(self) -> dict[int, str]:
        """
        Get the open turns for course selection.
        """
        data = {
            "bizTypeId": 2,
            "studentId": self._student_id
        }
        self._request("for-std/course-select", allow_redirects=False)
        res = self._request("ws/for-std/course-select/open-turns", "post", data=data)
        return {i["id"]: i["name"] for i in res.json()}

    def get_course_selection_system(self, turn_id: int):
        return CourseSelectionSystem(turn_id, self._student_id, self._request)

    def get_course_adjustment_system(self, turn_id: int, semester: SEMESTER):
        return CourseAdjustmentSystem(turn_id, self._semesters[semester], self._student_id, self._request)
