import asyncio
from collections.abc import Iterator
from typing import Any

from httpx import AsyncClient

from .select import AddDropResponse, Lesson


class CourseAdjustmentSystem:
    def __init__(
        self,
        turn_id: int,
        semester_id: int,
        student_id: int,
        client_pool: Iterator[AsyncClient],
    ):
        self._turn_id = turn_id
        self._semester_id = semester_id
        self._student_id = student_id
        self._client_pool = client_pool

    @property
    def turn_id(self):
        return self._turn_id

    @property
    def semester_id(self):
        return self._semester_id

    @property
    def student_id(self):
        return self._student_id

    async def _get(self, url: str, **kwargs: Any):
        return (
            await next(self._client_pool).post(
                "/for-std/course-adjustment-apply/" + url, **kwargs
            )
        ).json()

    async def add(self, lesson: Lesson, reason: str, confirm_retake: bool = False):
        data: dict[str, Any] = {
            "newLessonAssoc": lesson.id,
            "studentAssoc": self.student_id,
            "semesterAssoc": self.semester_id,
            "bizTypeAssoc": 2,
            "applyTypeAssoc": 1,
            "applyReason": reason,
            "retake": False,
            "scheduleGroupAssoc": None,
        }
        precheck_res = await self._get("preCheck", json=[data])
        if error := precheck_res["errors"]["allErrors"]:
            raise RuntimeError(error[0])
        retake_res = await next(self._client_pool).get(
            "/for-std/course-adjustment-apply/getRetake",
            params={
                "lessonIds": lesson.id,
                "studentId": self.student_id,
                "bizTypeId": 2,
            },
        )
        if len(retake_res.json()) > 0 and not confirm_retake:
            raise RuntimeError("Retake detected. Set confirm_retake=True to confirm.")
        await self._get("selection-apply/save", json=data)

    async def change_class(
        self,
        old_lesson: Lesson,
        new_lesson: Lesson,
        reason: str,
        retry: int = 3,
        sleep: float = 1.0,
    ):
        data = {
            "studentAssoc": self.student_id,
            "semesterAssoc": self.semester_id,
            "bizTypeAssoc": 2,
            "applyTypeAssoc": 5,
        }
        res = await self._get(
            "change-class-request",
            json={
                **data,
                "courseSelectTurnAssoc": self.turn_id,
                "saveCmds": [
                    {
                        "oldLessonAssoc": old_lesson.id,
                        "newLessonAssoc": new_lesson.id,
                        "applyReason": reason,
                        **data,
                        "scheduleGroupAssoc": None,
                    }
                ],
            },
        )
        if res["errors"]["allErrors"]:
            return AddDropResponse(
                "change-class",
                {"success": False, "errorMessage": res["errors"]["allErrors"][0]},
            )
        elif res["saveApply"]:
            return AddDropResponse("change-class", {"success": True})
        for _ in range(retry):
            r = await self._get(
                "add-drop-response",
                data={"studentId": self.student_id, "requestId": res["requestId"]},
            )
            if r:
                return AddDropResponse("change-class", r)
            await asyncio.sleep(sleep)
