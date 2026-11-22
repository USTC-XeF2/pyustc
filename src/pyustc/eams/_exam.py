"""Exam arrangements of the current semester."""

from datetime import datetime
from html.parser import HTMLParser

_EXAM_TABLE_ID = "exams"

_CLASS_ID = "课堂号"
_EXAM_TYPE = "考试类型"
_COURSE_NAME = "课程名称"
_TIME = "日期时间"
_ROOM = "考场"
_BUILDING = "教学楼"
_CAMPUS = "考场所在校区"
_NOTE = "考试说明"

_REQUIRED_HEADERS = (_CLASS_ID, _EXAM_TYPE, _COURSE_NAME, _TIME)

_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")
_TIME_FORMATS = ("%H:%M", "%H:%M:%S")


def _parse_datetime(text: str, date_hint: datetime | None = None) -> datetime | None:
    value = text.strip()
    if not value:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    if date_hint is not None:
        prefix = date_hint.strftime("%Y-%m-%d")
        for fmt in _TIME_FORMATS:
            try:
                return datetime.strptime(f"{prefix} {value}", f"%Y-%m-%d {fmt}")
            except ValueError:
                continue
    return None


def parse_period(text: str) -> tuple[datetime | None, datetime | None]:
    """Parse an exam time cell such as `2026-11-07 14:30~16:30`.

    The end may omit the date, in which case the start date is reused.
    """
    parts = [
        part.strip() for part in text.replace("\uff5e", "~").split("~") if part.strip()
    ]
    if not parts:
        return None, None
    start = _parse_datetime(parts[0])
    end = _parse_datetime(parts[1], start) if len(parts) > 1 else None
    return start, end


class _ExamTableParser(HTMLParser):
    """Collect the rows of the `<table id="exams">` element."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._depth = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._closed = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._closed:
            return
        if tag == "table":
            if self._depth or dict(attrs).get("id") == _EXAM_TABLE_ID:
                self._depth += 1
            return
        if not self._depth:
            return
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if self._closed or not self._depth:
            return
        if tag == "table":
            self._depth -= 1
            if not self._depth:
                self._closed = True
            return
        if tag in ("td", "th"):
            if self._cell is not None and self._row is not None:
                text = " ".join("".join(self._cell).replace("\xa0", " ").split())
                self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def _cell(row: list[str], columns: dict[str, int], name: str) -> str:
    index = columns.get(name)
    if index is None or index >= len(row):
        return ""
    return row[index]


class Exam:
    """One exam arrangement of the current semester."""

    def __init__(
        self,
        class_id: str,
        exam_type: str,
        course_name: str,
        time_text: str,
        room: str,
        building: str,
        campus: str,
        note: str,
    ):
        self.class_id = class_id
        self.exam_type = exam_type
        self.course_name = course_name
        self.time_text = time_text
        self.start, self.end = parse_period(time_text)
        self.room = room
        self.building = building
        self.campus = campus
        self.note = note

    def __repr__(self) -> str:
        return f"<Exam {self.course_name!r} {self.time_text!r}>"


def parse_exams(html: str) -> list[Exam]:
    """Parse the exam table out of an EAMS exam page."""
    parser = _ExamTableParser()
    parser.feed(html)
    parser.close()

    rows = parser.rows
    if not rows:
        raise RuntimeError("Failed to find the exam table")
    columns = {name: index for index, name in enumerate(rows[0])}
    missing = [name for name in _REQUIRED_HEADERS if name not in columns]
    if missing:
        raise RuntimeError(
            f"Unexpected exam table layout: missing {', '.join(missing)}"
        )

    exams: list[Exam] = []
    for row in rows[1:]:
        if not any(row):
            continue
        exams.append(
            Exam(
                class_id=_cell(row, columns, _CLASS_ID),
                exam_type=_cell(row, columns, _EXAM_TYPE),
                course_name=_cell(row, columns, _COURSE_NAME),
                time_text=_cell(row, columns, _TIME),
                room=_cell(row, columns, _ROOM),
                building=_cell(row, columns, _BUILDING),
                campus=_cell(row, columns, _CAMPUS),
                note=_cell(row, columns, _NOTE),
            )
        )
    return exams
