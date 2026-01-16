from collections.abc import Callable, Hashable
from typing import Any, TypeVar

T = TypeVar("T", bound=Hashable)


def singleton_by_key_meta(key_func: Callable[..., T]):
    class SingletonMeta(type):
        def __init__(cls, *args: Any, **kwargs: Any):
            cls._instance_cache: dict[T, Any] = {}
            cls._key_func = key_func
            super().__init__(*args, **kwargs)

        def __call__(cls, *args: Any, **kwargs: Any):
            try:
                cache_key = cls._key_func(*args, **kwargs)
            except Exception as e:
                raise ValueError(f"Key function failed for {cls.__name__}: {e}") from e

            if cache_key not in cls._instance_cache:
                instance = super().__call__(*args, **kwargs)
                cls._instance_cache[cache_key] = instance

            return cls._instance_cache[cache_key]

    return SingletonMeta


def singleton_by_field_meta(data_field: str):
    def key_func(data: dict[str, Any], *args: Any, **kwargs: Any):
        return data[data_field]

    return singleton_by_key_meta(key_func)
