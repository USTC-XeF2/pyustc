import datetime
from abc import ABC, abstractmethod
from typing import Generator, TypeVar
try:
    from typing import Self
except:
    Self = TypeVar("Self", bound = "TimePeriod")

from ._service import get_service

class TimePeriod:
    def __init__(self, start: datetime.datetime | str, end: datetime.datetime | str = None):
        if isinstance(start, str):
            start = self._strptime(start)
        if not end:
            end = start
        elif isinstance(end, str):
            end = self._strptime(end)
        if start > end:
            raise ValueError("The start time should be earlier than the end time")
        self.start = start
        self.end = end

    @staticmethod
    def _strptime(s: str) -> datetime.datetime:
        if not s: return
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

    def is_contain(self, other: Self):
        return self.start <= other.start and self.end >= other.end

    def is_overlap(self, other: Self):
        return self.start <= other.end and self.end >= other.start

    def __contains__(self, time: datetime.datetime):
        return self.start <= time <= self.end

    def __repr__(self):
        return f"<TimePeriod {self.start} - {self.end}>"

class Tag(ABC):
    @classmethod
    @abstractmethod
    def _get_url(cls) -> str:
        pass

    _T = TypeVar("_T", bound = "Tag")
    @classmethod
    @abstractmethod
    def from_dict(cls: type[_T], data: dict) -> _T:
        pass

    @classmethod
    def get_available_tags(cls, **kwargs):
        tags = list[cls]()
        for data in get_service().get_result(cls._get_url()):
            tag = cls.from_dict(data)
            if all(getattr(tag, k) == v for k, v in kwargs.items()):
                tags.append(tag)
        return tags

class Module(Tag):
    def __init__(self, value: str, text: str):
        self.value = value
        self.text = text

    @classmethod
    def _get_url(cls):
        return "sys/dict/getDictItems/item_module"

    @classmethod
    def from_dict(cls, data: dict[str]):
        return cls(data["value"], data["text"])

    def __repr__(self):
        return f"<Module {repr(self.text)}>"

class Department(Tag):
    """
    The department of a second class.
    
    Use `find` to search for the children of a department.
    """
    def __init__(self, id: str, name: str, children: list[dict[str]] = None, level: int = 0):
        self.id = id
        self.name = name
        self.level = level
        self.children = [Department.from_dict(i, level + 1) for i in children] if children else []

    @classmethod
    def _get_url(cls):
        return "sysdepart/sysDepart/queryTreeList"

    @classmethod
    def from_dict(cls, data: dict[str], level: int = 0):
        return cls(data["id"], data["departName"], data.get("children"), level)

    def find(self, name: str, max_level: int = -1) -> Generator[Self, None, None]:
        if max_level != -1 and self.level > max_level:
            return
        if name in self.name:
            yield self
        for i in self.children:
            yield from i.find(name, max_level)

    def find_one(self, name: str, max_level: int = -1):
        return next(self.find(name, max_level), None)

    def __repr__(self):
        return f"<Department {repr(self.name)} level={self.level}>"

class Label(Tag):
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    @classmethod
    def _get_url(cls):
        return "paramdesign/scLabel/queryListLabel"

    @classmethod
    def from_dict(cls, data: dict[str]):
        return cls(data["id"], data["name"])

    def __repr__(self):
        return f"<Label {repr(self.name)}>"

class SCFilter:
    """
    The filter for the second class.
    """
    def __init__(
            self,
            name: str = None,
            time_period: TimePeriod = None,
            module: Module = None,
            department: Department = None,
            labels: list[Label] = None,
            fuzzy_name: bool = True,
            strict_time: bool = False
        ):
        """
        The arg `fuzzy_name` is used to determine whether the name should be fuzzy matched.
        """
        self.name = name or ""
        self.time_period = time_period
        self.module = module
        self.department = department
        self.labels = labels or []
        self.fuzzy_name = fuzzy_name
        self.strict_time = strict_time

    def add_label(self, label: Label):
        if not self.labels:
            self.labels = []
        self.labels.append(label)

    def generate_params(self) -> dict[str]:
        params = {}
        if self.name: params["itemName"] = self.name
        if self.module: params["module"] = self.module.value
        if self.department: params["businessDeptId"] = self.department.id
        if self.labels: params["itemLable"] = ",".join(i.id for i in self.labels)
        return params

    def check(self, sc, only_strict: bool = False) -> bool:
        """
        Check if the second lesson meets the requirements.

        If `only_strict` is True, only the requirements that cannot be provided by the second course platform will be checked.
        """
        if not only_strict:
            if self.fuzzy_name and self.name.lower() not in sc.name.lower():
                return False
            if self.module and self.module.value != sc.module.value:
                return False
            if self.department and self.department.id != sc.department.id:
                return False
            if self.labels and not any(i in sc.labels for i in self.labels):
                return False
        if not self.fuzzy_name and self.name != sc.name:
            return False
        if self.time_period:
            if self.strict_time:
                if not self.time_period.is_contain(sc.hold_time):
                    return False
            elif not self.time_period.is_overlap(sc.hold_time):
                return False
        return True
