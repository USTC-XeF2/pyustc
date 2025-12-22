from typing import Literal

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from httpx import AsyncClient

from .._url import generate_url, root_url
from ..cas import CASClient
from ._course import CourseTable
from ._grade import GradeManager
from .adjust import CourseAdjustmentSystem
from .select import CourseSelectionSystem

_ua = UserAgent(platforms="desktop")

Semester = tuple[int, Literal["春", "夏", "秋"]] | Literal["now"]


class EAMSClient:
    def __init__(self, client: AsyncClient):
        self._client = client
        self._student_id: int = 0
        self._semesters: dict[Semester, int] = {}

    @classmethod
    async def create(cls, cas_client: CASClient, user_agent: str | None = None):
        client = AsyncClient(
            base_url=root_url["eams"],
            follow_redirects=True,
            headers={"User-Agent": user_agent or _ua.random},
        )

        ticket = await cas_client.get_ticket(generate_url("eams", "/ucas-sso/login"))
        res = await client.get("/ucas-sso/login", params={"ticket": ticket})
        if not res.url.path.endswith("home"):
            raise RuntimeError("Failed to login")

        return cls(client)

    async def _get_student_id_and_semesters(self):
        if not (self._student_id and self._semesters):
            res = await self._client.get("/for-std/course-table")
            student_id = res.url.path.split("/")[-1]
            if not student_id.isdigit():
                raise RuntimeError("Failed to get student id")
            self._student_id = int(student_id)
            if not self._semesters:
                self._set_semesters(res.text)

        return self._student_id, self._semesters

    def _set_semesters(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        for option in soup.select("#allSemesters > option"):
            value = int(str(option["value"]))
            year, season = option.text.split("年")
            self._semesters[(int(year), season[0])] = value
            if "selected" in option.attrs:
                self._semesters["now"] = value

    async def get_current_teach_week(self) -> int:
        """
        Get the current teaching week.
        """
        res = await self._client.get("/home/get-current-teach-week")
        return res.json()["weekIndex"]

    async def get_course_table(
        self, week: int | None = None, semester: Semester = "now"
    ):
        """
        Get the course table for the specified week and semester.
        """
        student_id, semesters = await self._get_student_id_and_semesters()
        url = f"/for-std/course-table/semester/{semesters[semester]}/print-data/{student_id}"
        params = {"weekIndex": week or ""}
        res = await self._client.get(url, params=params)
        return CourseTable(res.json()["studentTableVm"], week)

    def get_grade_manager(self):
        return GradeManager(self._client)

    async def get_open_turns(self) -> dict[int, str]:
        """
        Get the open turns for course selection.
        """
        student_id, _ = await self._get_student_id_and_semesters()
        res = await self._client.post(
            "/ws/for-std/course-select/open-turns",
            data={"bizTypeId": 2, "studentId": student_id},
        )
        return {i["id"]: i["name"] for i in res.json()}

    async def get_course_selection_system(self, turn_id: int):
        student_id, _ = await self._get_student_id_and_semesters()
        return CourseSelectionSystem(turn_id, student_id, self._client)

    async def get_course_adjustment_system(self, turn_id: int, semester: Semester):
        student_id, semesters = await self._get_student_id_and_semesters()
        return CourseAdjustmentSystem(
            turn_id, semesters[semester], student_id, self._client
        )
