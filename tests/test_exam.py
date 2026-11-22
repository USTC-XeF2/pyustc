"""EAMS 考试安排与课表新增字段的单元测试. 不触网."""

from collections.abc import Callable
from datetime import datetime

from pyustc.eams._course import Course
from pyustc.eams._exam import Exam, parse_exams, parse_period

EXAM_HTML = """
<html><body>
<table class="table table-striped" id="exams">
  <thead>
    <tr>
      <th>课堂号</th><th>考试类型</th><th>课程名称</th><th>日期时间</th>
      <th>考场</th><th>教学楼</th><th>考场所在校区</th><th>考试说明</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>PHYS1004C.05</td><td>期中考试</td><td>电磁学C</td>
      <td>2026-11-07 14:30~16:30</td><td>2121</td>
      <td>第二教学楼</td><td>东区</td><td></td>
    </tr>
    <tr>
      <td>EE2506A.01</td><td>期末考试</td><td>模拟与数字电路A</td>
      <td>2026-12-20 09:00~2026-12-20 11:00</td><td>3C102</td>
      <td>第三教学楼</td><td>西区</td><td>带计算器</td>
    </tr>
  </tbody>
</table>
</body></html>
"""


def test_parse_exams_reads_all_columns() -> None:
    exams = parse_exams(EXAM_HTML)
    assert len(exams) == 2

    first = exams[0]
    assert first.class_id == "PHYS1004C.05"
    assert first.exam_type == "期中考试"
    assert first.course_name == "电磁学C"
    assert first.room == "2121"
    assert first.building == "第二教学楼"
    assert first.campus == "东区"
    assert first.note == ""

    # 结束时间省略日期时沿用开始日期.
    assert first.start == datetime(2026, 11, 7, 14, 30)
    assert first.end == datetime(2026, 11, 7, 16, 30)


def test_parse_exams_keeps_full_end_datetime() -> None:
    second = parse_exams(EXAM_HTML)[1]
    assert second.start == datetime(2026, 12, 20, 9, 0)
    assert second.end == datetime(2026, 12, 20, 11, 0)
    assert second.note == "带计算器"


def test_parse_exams_ignores_unrelated_tables() -> None:
    html = (
        """
    <table id="odd"><tr><td>忽略我</td></tr></table>
    """
        + EXAM_HTML
    )
    assert len(parse_exams(html)) == 2


def _expect_error(call: Callable[[str], list[Exam]], argument: str, match: str) -> None:
    try:
        call(argument)
    except RuntimeError as exc:
        assert match in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_parse_exams_without_table_raises() -> None:
    _expect_error(parse_exams, "<html><body>无考试安排</body></html>", "exam table")


def test_parse_exams_rejects_unknown_headers() -> None:
    html = '<table id="exams"><tr><th>课程名称</th><th>时间</th></tr><tr><td>A</td><td>B</td></tr></table>'
    _expect_error(parse_exams, html, "layout")


def test_parse_period_returns_none_for_unparsable_text() -> None:
    assert parse_period("待定") == (None, None)
    assert parse_period("") == (None, None)


def _course_data() -> dict[str, object]:
    return {
        "lessonCode": "CS2502A.02",
        "courseCode": "CS2502A",
        "courseName": "数据结构A",
        "room": "3A311",
        "customPlace": None,
        "building": "第三教学楼",
        "campus": "西区",
        "weekday": 4,
        "teacherDeepVms": [],
        "stdCount": 56,
        "startDate": "19:30",
        "endDate": "21:55",
        "startUnit": 11,
        "endUnit": 13,
        "credits": 4.0,
        "weeksArray": [2, 3, 6, 7, 9, 10, 11, 12, 13, 14],
        "weeksStr": "2-3,6-7,9-14",
    }


def test_course_exposes_weeks_and_credits() -> None:
    course = Course(_course_data())
    assert course.course_code == "CS2502A"
    assert course.credits == 4.0
    assert course.weeks == [2, 3, 6, 7, 9, 10, 11, 12, 13, 14]
    assert course.weeks_str == "2-3,6-7,9-14"


def test_course_tolerates_missing_week_fields() -> None:
    data = _course_data()
    for key in ("weeksArray", "weeksStr", "courseCode", "credits"):
        del data[key]
    course = Course(data)
    assert course.weeks == []
    assert course.weeks_str == ""
    assert course.course_code == ""
    assert course.credits == 0.0
