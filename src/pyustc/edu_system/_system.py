import requests

from ..url import generate_url
from ..passport import Passport
from ._course import CourseTable

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

class EduSystem:
    def __init__(self, passport: Passport):
        self.session = requests.Session()
        self.session.headers.update(headers)
        ticket = passport.get_ticket(generate_url("edu_system", "ucas-sso/login"))
        res = self._request("ucas-sso/login", params = {"ticket": ticket})
        if res.status_code != 302:
            raise RuntimeError("Failed to login")

    def _request(self, url: str, method: str = "get", params: dict[str] = {}):
        return self.session.request(
            method,
            generate_url("edu_system", url),
            params = params,
            allow_redirects = False
        )

    def get_current_teach_week(self) -> int:
        """
        Get the current teaching week.
        """
        res = self._request("home/get-current-teach-week")
        return res.json()["weekIndex"]

    def get_course_table(self, week: int = None, semester: int = 362):
        """
        Get the course table for the specified week and semester.
        """
        if not student_id:
            res = self._request("for-std/course-table")
            if res.status_code != 302:
                raise RuntimeError("Failed to get course table")
            student_id = res.headers["Location"].split("/")[-1]
        params = {
            "weekIndex": week or ""
        }
        res = self._request(f"for-std/course-table/semester/{semester}/print-data/{student_id}", params = params)
        return CourseTable(res.json()["studentTableVm"], week)
