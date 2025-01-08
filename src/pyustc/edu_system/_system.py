import requests
from typing import Literal
from bs4 import BeautifulSoup

from ..url import generate_url
from ..passport import Passport
from ._course import CourseTable
from ._select import CourseSelectionSystem
from ._adjust import CourseAdjustmentSystem

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

SEMESTER = tuple[int, Literal["春", "夏", "秋"]] | Literal["now"]

class EduSystem:
    def __init__(self, passport: Passport):
        self.session = requests.Session()
        self.session.headers.update(headers)
        ticket = passport.get_ticket(generate_url("edu_system", "ucas-sso/login"))
        res = self._request("ucas-sso/login", params = {"ticket": ticket})
        if res.status_code != 302:
            raise RuntimeError("Failed to login")
        # Get student id
        res = self._request("for-std/course-table")
        if res.status_code != 302:
            raise RuntimeError("Failed to get student id")
        self._student_id = res.headers["Location"].split("/")[-1]
        # Get semesters
        self._semesters = dict[SEMESTER, int]()
        sem_res = self._request(f"for-std/course-table/info/{self._student_id}")
        soup = BeautifulSoup(sem_res.text, "html.parser")
        for option in soup.select("#allSemesters > option"):
            value = int(option["value"])
            text = option.text
            year, season = text.split("年")
            self._semesters[(int(year), season[0])] = value
            if "selected" in option.attrs:
                self._semesters["now"] = value

    def _request(self, url: str, method: str = "get", **args):
        return self.session.request(
            method,
            generate_url("edu_system", url),
            **args,
            allow_redirects = False
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

    def get_open_turns(self) -> dict[int, str]:
        data = {
            "bizTypeId": 2,
            "studentId": self._student_id
        }
        res = self._request("ws/for-std/course-select/open-turns", method="post", data=data)
        return {i["id"]: i["name"] for i in res.json()}

    def get_course_selection_system(self, turn_id: int):
        return CourseSelectionSystem(turn_id, self._student_id, self._request)

    def get_course_adjustment_system(self, turn_id: int, semester: SEMESTER):
        return CourseAdjustmentSystem(turn_id, self._semesters[semester], self._student_id, self._request)
