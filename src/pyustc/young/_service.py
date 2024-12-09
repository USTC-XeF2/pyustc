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
        url = "sys/user/getPersonInChargeUser"
        params = {
            "realname": key
        }
        try:
            yield from map(User, self._interface.page_search(url, params, max, size))
        except RuntimeError as e:
            e.args = ("Failed to get user info",)
            raise e

    def get_second_class(self, name: str = None, filter: SCFilter = None, participated: bool = False, ended: bool = False, max: int = -1, size: int = 20):
        """
        Get second class list.

        The arg `name` is valid when `filter` is `None` or `filter.name` is unset.

        The arg `ended` will be ignored if `participated` is True.
        """
        if participated:
            url = "item/scParticipateItem/list"
        else:
            url = f"item/scItem/{'endList' if ended else 'enrolmentList'}"
        if not filter:
            filter = SCFilter()
        if name and not filter.name:
            filter.name = name
        params = filter.generate_params()
        try:
            for i in self._interface.page_search(url, params, -1, size):
                if participated: del i["applyNum"]
                sc = SecondClass.from_dict(i)
                if filter.check(sc, only_strict = True):
                    yield sc
                    max -= 1
                    if not max:
                        break
        except RuntimeError as e:
            e.args = ("Failed to get second class",)
            raise e
