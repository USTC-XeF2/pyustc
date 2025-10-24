import base64
import contextvars
import json
import time
from typing import Any

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

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
        self._access_token: str = data["result"]["token"]
        self._session.headers.update({"X-Access-Token": self._access_token})

    def __enter__(self):
        self._token = _current_service.set(self)
        return self

    def __exit__(self, *_):
        _current_service.reset(self._token)

    def _encrypt(self, data: dict[str, Any], timestamp: int):
        access_token = getattr(
            self, "_access_token", "kPBNkx0sSO3aIBaKDt9d2GJURVJfzFuP"
        )
        cipher = AES.new(
            access_token[-16:].encode(), AES.MODE_CBC, access_token[-32:-16].encode()
        )
        json_string = json.dumps(data | {"_t": timestamp})
        return base64.b64encode(
            cipher.encrypt(pad(json_string.encode(), AES.block_size))
        ).decode()

    def request(
        self,
        url: str,
        method: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timestamp = int(time.time() * 1000)
        return self._session.request(
            method,
            generate_url("young", f"login/wisdom-group-learning-bg/{url}"),
            params={
                "requestParams": self._encrypt(params or {}, timestamp),
                "_t": timestamp,
            },
            json={"requestParams": self._encrypt(json or {}, timestamp)},
        ).json()

    def get_result(self, url: str, params: dict[str, Any] | None = None):
        error = RuntimeError("Max retry reached")
        for _ in range(self.retry):
            try:
                data = self.request(url, "get", params)
            except Exception as e:
                error = e
                continue
            if data["success"]:
                return data["result"]
            error = RuntimeError(data["message"])
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


_current_service = contextvars.ContextVar[YouthService]("youth_service")


def get_service():
    try:
        return _current_service.get()
    except LookupError:
        raise RuntimeError(
            "Not in context, please use 'with YouthService(CASClient)' to create a context"
        )
