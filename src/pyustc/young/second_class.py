from enum import Enum
from typing import Any, Self

from pyustc._singleton import singleton_by_key_meta

from ._user import User
from .filter import Department, Label, Module, SCFilter, TimePeriod
from .service import get_service


class Status(Enum):
    APPLYING = 26, "报名中"
    APPLY_ENDED = 28, "报名已结束"
    HOUR_PUBLIC = 30, "学时公示中"
    HOUR_APPEND_PUBLIC = 31, "追加学时公示"
    PUBLIC_ENDED = 32, "公示已结束"
    HOUR_APPLYING = 33, "学时申请中"
    HOUR_APPROVED = 34, "学时审核通过"
    HOUR_REJECTED = 35, "学时驳回"
    FINISHED = 40, "结项"

    @property
    def code(self):
        return self.value[0]

    @property
    def text(self):
        return self.value[1]

    @classmethod
    def from_code(cls, code: int):
        for status in cls:
            if status.code == code:
                return status
        raise ValueError(f"Unknown status code: {code}")

    def __repr__(self):
        return f"<Status {self.code} {self.text!r}>"


class SignInfo:
    def __init__(
        self, college: str, classes: str, phone: str, email: str = "", remarks: str = ""
    ):
        self.college = college
        self.classes = classes
        self.phone = phone
        self.email = email
        self.remarks = remarks

    @classmethod
    async def get_self(cls):
        user = await User.get()
        return cls(user.college or "", user.classes, await user.get_phone() or "")

    def json(self):
        return {
            "college": self.college,
            "classes": self.classes,
            "phone": self.phone,
            "email": self.email,
            "remarks": self.remarks,
        }


class SecondClass(metaclass=singleton_by_key_meta(lambda id, data: id)):  # type: ignore
    def __init__(self, id: str, data: dict[str, Any] | None = None):
        self.id = id
        self.data: dict[str, Any] = {}
        if data is not None:
            self.data.update(data)
        self._children: list[Self] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(data["id"], data=data)

    @staticmethod
    def _get_filter(name_or_filter: str | SCFilter | None):
        if isinstance(name_or_filter, SCFilter):
            return name_or_filter
        return SCFilter(name=name_or_filter)

    @classmethod
    async def _fetch(cls, filter: SCFilter, url: str, size: int):
        params = filter.generate_params()
        async for i in get_service().page_search(url, params, -1, size):
            sc = cls.from_dict(i)
            if filter.check(sc, only_strict=True):
                yield sc

    @classmethod
    async def find(
        cls,
        name_or_filter: str | SCFilter | None = None,
        apply_ended: bool = False,
        expand_series: bool = False,
        max: int = -1,
        size: int = 20,
    ):
        """
        Find the second class that meets the conditions.

        Arguments:
            name: The name of the second class. If `filter.name` is set, this argument will be ignored.
            filter: The filter for the second class, which will be used for both the series and the children.
            apply_ended: Whether to show the second class that has ended or not.
            expand_series: Whether to expand the series to get all second classes in the series.
        """
        if not max:
            return
        filter = cls._get_filter(name_or_filter)
        url = f"/item/scItem/{'endList' if apply_ended else 'enrolmentList'}"
        async for sc in cls._fetch(filter, url, size):
            if expand_series and sc.is_series:
                for i in await sc.get_children():
                    if filter.check(i, only_strict=True) and (
                        apply_ended ^ (i.status == Status.APPLYING)
                    ):
                        yield i
                        max -= 1
                    if not max:
                        break
            else:
                yield sc
                max -= 1
            if not max:
                break

    @classmethod
    async def get_participated(
        cls,
        name_or_filter: str | SCFilter | None = None,
        max: int = -1,
        size: int = 20,
    ):
        """
        Get the specific second class list that the user has participated in.
        """
        if not max:
            return
        async for sc in cls._fetch(
            cls._get_filter(name_or_filter), "/item/scParticipateItem/list", size
        ):
            del sc.data["applyNum"]
            yield sc
            max -= 1
            if not max:
                break

    @property
    def name(self) -> str:
        return self.data["itemName"]

    @property
    def status(self):
        return Status.from_code(self.data["itemStatus"])

    @property
    def create_time(self):
        return TimePeriod.parse_time(self.data["createTime"])

    @property
    def apply_time(self):
        return TimePeriod(self.data["applySt"], self.data["applyEt"])

    @property
    def hold_time(self):
        return TimePeriod(self.data["st"], self.data["et"])

    @property
    def tel(self) -> str:
        return self.data["tel"]

    @property
    def valid_hour(self) -> float:
        return self.data["validHour"]

    @property
    def apply_num(self) -> int | None:
        return self.data.get("applyNum")

    @property
    def apply_limit(self) -> int:
        return self.data["peopleNum"]

    @property
    def applied(self) -> bool:
        return self.data["booleanRegistration"] == 1

    @property
    def applyable(self):
        """
        This method will check the status and the number of applicants.
        """
        return (
            self.status == Status.APPLYING
            and not self.applied
            and self.apply_num is not None
            and self.apply_num < (self.apply_limit or 0)
        )

    @property
    def need_sign_info(self) -> bool:
        return self.data["needSignInfo"] == "1"

    @property
    def module(self):
        if "moduleName" not in self.data:
            return None
        return Module(self.data["module"], self.data["moduleName"])

    @property
    def department(self):
        if "businessDeptName" not in self.data:
            return None
        return Department(
            self.data["businessDeptId"], self.data["businessDeptName"], level=-1
        )

    @property
    def labels(self):
        if "lableNames" not in self.data:
            return None
        return list(
            map(Label, self.data["itemLable"].split(","), self.data["lableNames"])
        )

    @property
    def conceive(self) -> str:
        return self.data["conceive"]

    @property
    def is_series(self) -> bool:
        return self.data["itemCategory"] == "1"

    async def get_children(self) -> list[Self]:
        if not self.is_series:
            return []

        if self._children is not None:
            return self._children

        url = "/item/scItem/selectSignChirdItem"
        params = {"id": self.id}
        try:
            self._children = [
                self.from_dict(i)
                for i in await get_service().get_result(url, params=params)
            ]
            return self._children
        except RuntimeError as e:
            e.args = ("Failed to get children",)
            raise e

    async def update(self):
        url = "/item/scItem/queryById"
        params = {"id": self.id}
        try:
            self.data.update(await get_service().get_result(url, params=params))
        except RuntimeError as e:
            e.args = ("Failed to update",)
            raise e

    async def get_applicants(self, max: int = -1, size: int = 50):
        url = "/item/scItemRegistration/list"
        params = {"itemId": self.id}
        async for i in get_service().page_search(url, params, max, size):
            yield str(i["username"])

    async def apply(
        self,
        force: bool = False,
        auto_cancel: bool = False,
        sign_info: SignInfo | None = None,
    ) -> bool:
        """
        Apply for this second class.

        Arguments:
            force: Whether to force apply even if the second class is not applyable.
            auto_cancel: Whether to cancel the application with time conflict and apply again.
            sign_info: The sign info for the second class. If `need_sign_info` is False, this argument will be ignored.
        """
        if not (force or self.applyable):
            return False
        url = f"/mobile/item/enter/{self.id}"
        data = await get_service().request(
            url,
            "post",
            json=(
                (sign_info or await SignInfo.get_self()).json()
                if self.need_sign_info
                else {}
            ),
        )
        if data["success"]:
            return True
        if auto_cancel and "时间冲突" in data["message"]:
            async for i in SecondClass.get_participated(
                SCFilter(time_period=self.hold_time)
            ):
                await i.cancel_apply()
            return await self.apply(force)
        raise RuntimeError(data["message"])

    async def cancel_apply(self) -> bool:
        """
        Cancel the application.
        """
        url = f"/mobile/item/cancellRegistration/{self.id}"
        data = await get_service().request(url, "post")
        if data["success"]:
            return True
        raise RuntimeError(data["message"])

    def __repr__(self):
        if self.is_series:
            return f"<SecondClass {self.name!r} Series>"
        return f"<SecondClass {self.name!r}>"
