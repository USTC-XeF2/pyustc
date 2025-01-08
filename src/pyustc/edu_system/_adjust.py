import time
import requests

from ._select import Lesson, AddDropResponse

class CourseAdjustmentSystem:
    def __init__(self, turn_id: int, semester_id: int, student_id: str, request_func):
        self._turn_id = turn_id
        self._semester_id = semester_id
        self._student_id = int(student_id)
        self._request_func = request_func

    @property
    def turn_id(self):
        return self._turn_id

    @property
    def semester_id(self):
        return self._semester_id

    @property
    def student_id(self):
        return self._student_id

    def _get(self, url: str, **kwargs) -> requests.Response:
        return self._request_func("for-std/course-adjustment-apply/" + url, method="post", **kwargs)

    def change_class(self, lesson: Lesson, new_lesson: Lesson, reason: str):
        data = {
            "studentAssoc": self.student_id,
            "semesterAssoc": self.semester_id,
            "bizTypeAssoc": 2,
            "applyTypeAssoc": 5,
        }
        res = self._get("change-class-request", json={
            **data,
            "courseSelectTurnAssoc": self.turn_id,
            "saveCmds": [{
                "oldLessonAssoc": lesson.id,
                "newLessonAssoc": new_lesson.id,
                "applyReason": reason,
                **data,
                "scheduleGroupAssoc": None
            }]
        }).json()
        if res["errors"]["allErrors"]:
            return AddDropResponse("change-class", {
                "success": False,
                "errorMessage" : res["errors"]["allErrors"][0]
            })
        elif res["saveApply"]:
            return AddDropResponse("change-class", {
                "success": True
            })
        for _ in range(3):
            r = self._get("add-drop-response", data={
                "studentId": self.student_id,
                "requestId": res["requestId"]
            }).json()
            if r:
                return AddDropResponse("change-class", r)
            time.sleep(1)
