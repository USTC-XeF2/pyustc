import datetime
try:
    from typing import Self
except:
    from typing import TypeVar
    Self = TypeVar("Self")

from ._filter import Tag, BaseFilter
from ._interface import Interface

def strptime(s: str) -> datetime.datetime:
    if not s: return
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

class Module(Tag):
    def __init__(self, value: str, text: str):
        self.value = value
        self.text = text

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
    def from_dict(cls, data: dict[str], level: int = 0):
        return cls(data["id"], data["departName"], data.get("children"), level)

    def find(self, name: str, max_level: int = -1):
        if max_level != -1 and self.level > max_level:
            return
        if name in self.name:
            yield self
        for i in self.children:
            yield from i.find(name, max_level)

    def __repr__(self):
        return f"<Department {repr(self.name)} level={self.level}>"

class Label(Tag):
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    @classmethod
    def from_dict(cls, data: dict[str]):
        return cls(data["id"], data["name"])

    def __repr__(self):
        return f"<Label {repr(self.name)}>"

status_list = {
    26: "报名中",
    28: "报名已结束",
    30: "学时公示中",
    31: "追加学时公示",
    32: "公示已结束",
    33: "学时申请中",
    34: "学时审核通过",
    35: "学时驳回",
    40: "结项"
}

class SecondClass:
    """
    The second class of the Youth Service.
    """
    _interface: Interface = None
    _second_class_cache = dict[str, Self]()
    def __new__(cls, id: str, *args, **kwargs):
        if id in cls._second_class_cache:
            obj: cls = cls._second_class_cache[id]
        else:
            obj = super(SecondClass, cls).__new__(cls)
            cls._second_class_cache[id] = obj
        return obj

    def __init__(self, id: str, interface: Interface = None, data: dict[str] = None):
        self.id = id
        if isinstance(interface, Interface):
            self._interface = interface
        self.data = {}
        self.update(data)
        self._children = list[SecondClass]()

    @classmethod
    def bind_interface(cls, interface: Interface):
        cls._interface = interface

    @classmethod
    def from_dict(cls, data: dict[str], interface: Interface = None):
        return cls(data["id"], interface = interface, data = data)

    @property
    def name(self) -> str:
        return self.data["itemName"]

    @property
    def status_code(self) -> int:
        return self.data["itemStatus"]

    @property
    def status(self):
        return status_list.get(self.status_code, self.status_code)

    @property
    def create_time(self):
        return strptime(self.data["createTime"])

    @property
    def apply_endtime(self):
        return strptime(self.data["applyEt"])

    @property
    def tel(self) -> str:
        return self.data["tel"]

    @property
    def valid_hour(self) -> float:
        return self.data["validHour"]

    @property
    def apply_num(self) -> int:
        if "applyNum" not in self.data:
            self.update()
        return self.data["applyNum"]

    @property
    def apply_limit(self) -> int:
        return self.data["peopleNum"]

    @property
    def applyable(self):
        """
        This method will check the status and the number of applicants.
        """
        return self.status_code == 26 and self.apply_num < (self.apply_limit or 0)

    @property
    def module(self):
        if "moduleName" not in self.data:
            self.update()
        return Module(self.data["module"], self.data["moduleName"])

    @property
    def department(self):
        if "businessDeptName" not in self.data:
            self.update()
        return Department(self.data["businessDeptId"], self.data["businessDeptName"], level = -1)

    @property
    def labels(self):
        if "lableNames" not in self.data:
            self.update()
        return [Label(i, j) for i, j in zip(self.data["itemLable"].split(","), self.data["lableNames"])]

    @property
    def conceive(self) -> str:
        return self.data["conceive"]

    @property
    def is_category(self) -> bool:
        return self.data["itemCategory"] == "1"

    @property
    def children(self):
        if self._children or not self.is_category:
            return self._children
        url = "item/scItem/selectSignChirdItem"
        params = {
            "id": self.id
        }
        try:
            self._children = [SecondClass.from_dict(i, self._interface) for i in self._interface.get_result(url, params)]
            return self._children
        except RuntimeError as e:
            e.args = ("Failed to get children",)
            raise e

    def update(self, data: dict[str] = None):
        if not data:
            url = "item/scItem/queryById"
            params = {
                "id": self.id
            }
            try:
                data = self._interface.get_result(url, params)
            except RuntimeError as e:
                e.args = ("Failed to update",)
                raise e
        self.data.update(data)

    def apply(self, force: bool = False) -> bool:
        """
        Apply for this second class.

        If `force` is True, apply even if it's not applyable.
        """
        if not (force or self.applyable):
            return False
        url = f"item/scItemRegistration/enter/{self.id}"
        data = self._interface.request(url, "post")
        if data["success"]: return True
        raise RuntimeError(data["message"])

    def __repr__(self):
        if self.is_category:
            return f"<SecondClass {repr(self.name)} Category>"
        return f"<SecondClass {repr(self.name)}>"

class SCFilter(BaseFilter):
    """
    The filter for the second class.
    """
    def __init__(self, name: str = None, module: Module = None, department: Department = None, labels: list[Label] = None, fuzzy_name: bool = True):
        self.name = name or ""
        self.module = module
        self.department = department
        self.labels = labels or []
        self.fuzzy_name = fuzzy_name

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

    def check(self, sc: SecondClass, only_strict: bool = False) -> bool:
        """
        Check if the second lesson meets the requirements.

        If `only_strict` is True, only the requirements that cannot be provided by the second course platform will be checked.
        """
        if not only_strict:
            if self.fuzzy_name and self.name.lower() not in sc.name.lower():
                return False
            if self.module and self.module.value != sc.module.value:
                return False
            # if self.deptid and self.deptid != sc.data["businessDeptId"]:
            #     return False
            if self.labels and not any(i in sc.labels for i in self.labels):
                return False
        if not self.fuzzy_name and self.name != sc.name:
            return False
        return True
