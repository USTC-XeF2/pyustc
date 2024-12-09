from abc import ABC, abstractmethod
from typing import TypeVar

class Tag(ABC):
    _T = TypeVar("_T", bound = 'Tag')
    @classmethod
    def from_dict(cls: type[_T], data: dict) -> _T:
        pass

class BaseFilter(ABC):
    @abstractmethod
    def check(self, data: dict[str]) -> bool:
        pass
