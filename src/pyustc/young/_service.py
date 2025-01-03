from typing import TypeVar

from ..passport import Passport
from ._filter import Tag
from ._interface import Interface
from ._user import User
from ._second_class import Module, Department, Label, SCFilter, SecondClass

_T = TypeVar("_T", bound = Tag)

class YouthService:
    def __init__(self, passport: Passport, bound_second_class: bool = True):
        self._interface = Interface(passport)
        if bound_second_class:
            SecondClass.bind_interface(self._interface)

    def get_available_tags(self, tag_cls: type[_T], **kwargs):
        url = {
            Module: "sys/dict/getDictItems/item_module",
            Department: "sysdepart/sysDepart/queryTreeList",
            Label: "paramdesign/scLabel/queryListLabel"
        }.get(tag_cls)
        if not url:
            raise ValueError("Invalid tag class")
        tags = list[tag_cls]()
        try:
            for data in self._interface.get_result(url):
                tag = tag_cls.from_dict(data)
                if all(getattr(tag, k) == v for k, v in kwargs.items()):
                    tags.append(tag)
        except RuntimeError:
            pass
        return tags

    def get_users(self, key: str, max: int = -1, size: int = 50):
        url = "sys/user/list"
        params = {
            "realname": key
        }
        try:
            yield from map(User, self._interface.page_search(url, params, max, size))
        except RuntimeError as e:
            e.args = ("Failed to get user info",)
            raise e

    def _get_second_class(self, name: str, filter: SCFilter, url: str, size: int):
        if not filter:
            filter = SCFilter()
        if name and not filter.name:
            filter.name = name
        params = filter.generate_params()
        try:
            for i in self._interface.page_search(url, params, -1, size):
                sc = SecondClass.from_dict(i)
                if filter.check(sc, only_strict = True):
                    yield sc
        except RuntimeError as e:
            e.args = ("Failed to get second class",)
            raise e

    def get_second_class(
            self,
            name: str = None,
            filter: SCFilter = None,
            apply_ended: bool = False,
            expand_series: bool = False,
            max: int = -1,
            size: int = 20
        ):
        """
        Get second class list.

        The arg `name` is valid when `filter` is `None` or `filter.name` is unset.

        If `expand_series` is True, the function will return all the children of the series.
        And the `filter` will be applied to both the series and the children.
        """
        if not max: return
        url = f"item/scItem/{'endList' if apply_ended else 'enrolmentList'}"
        for sc in self._get_second_class(name, filter, url, size):
            if expand_series and sc.is_series:
                for i in sc.children:
                    if filter.check(i, only_strict = True) and (apply_ended ^ (i.status_code <= 26)):
                        yield i
                        max -= 1
                    if not max:
                        break
            else:
                yield sc
                max -= 1
            if not max:
                break

    def get_participated_second_class(
            self,
            name: str = None,
            filter: SCFilter = None,
            max: int = -1,
            size: int = 20
        ):
        """
        Get the specific second class list that the user has participated in.
        """
        if not max: return
        for sc in self._get_second_class(name, filter, "item/scParticipateItem/list", size):
            del sc.data["applyNum"]
            yield sc
            max -= 1
            if not max:
                break

    def auto_cancel_and_apply(self, sc: SecondClass, force: bool = False) -> bool:
        """
        Cancel the application if applied, otherwise apply for it.

        If `force` is True, apply even if it's not applyable.
        """
        try:
            return sc.apply(force)
        except RuntimeError as e:
            if "时间冲突" not in e.args[0]:
                raise e
            for i in self.get_second_class(
                filter = SCFilter(time_period = sc.hold_time),
                participated = True
            ):
                i.cancel_apply()
        return sc.apply(force)
