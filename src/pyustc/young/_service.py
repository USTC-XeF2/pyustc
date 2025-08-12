from typing import Any

import requests

from ..cas import CASClient
from ..url import generate_url


class YouthService:
    def __init__(self, client: CASClient, retry: int = 3):
        self.retry = retry
        self._session = requests.Session()
        service_url = generate_url("young", "login/sc-wisdom-group-learning/")
        data = self.request(
            "cas/client/checkSsoLogin",
            "get",
            {"ticket": client.get_ticket(service_url), "service": service_url},
        )
        if not data["success"]:
            raise RuntimeError(data["message"])
        self._session.headers.update({"X-Access-Token": data["result"]["token"]})

    def __enter__(self):
        self._origin_service = globals().get("service")
        global service
        service = self
        return self

    def __exit__(self, *_):
        if self._origin_service:
            global service
            service = self._origin_service

    def request(
        self,
        url: str,
        method: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._session.request(
            method,
            generate_url("young", f"login/wisdom-group-learning-bg/{url}"),
            params=params,
            json=json,
        ).json()

    def get_result(self, url: str, params: dict[str, Any] | None = None):
        error = RuntimeError("Max retry reached")
        for _ in range(self.retry):
            try:
                data = self.request(url, "get", params)
                if data["success"]:
                    return data["result"]
                raise RuntimeError(data["message"])
            except Exception as e:
                error = e
        raise error

    def page_search(self, url: str, params: dict[str, Any], max: int, size: int):
        page = 1
        while max:
            new_params = params.copy()
            new_params["pageNo"] = page
            new_params["pageSize"] = size
            result = self.get_result(url, new_params)
            for i in result["records"]:
                yield i
                max -= 1
                if not max:
                    break
            if page * size >= result["total"]:
                break
            page += 1


def get_service() -> YouthService:
    try:
        return service
    except NameError:
        msg = "Not in context, please use 'with YouthService(CASClient)' to create a context"
        raise RuntimeError(msg)
