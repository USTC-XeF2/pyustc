import base64
import contextvars
import json
import time
from types import TracebackType
from typing import Any
from urllib.parse import urljoin

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from httpx import AsyncClient

from pyustc._url import generate_url, root_url
from pyustc.cas import CASClient


class YouthService:
    def __init__(self, retry: int = 3):
        self.retry = retry
        self._client = AsyncClient(base_url=root_url["young"], follow_redirects=True)

    async def __aenter__(self):
        await self._client.__aenter__()
        self._token = _current_service.set(self)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ):
        _current_service.reset(self._token)
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def login(self, client: CASClient):
        service_url = generate_url("young", "/login/sc-wisdom-group-learning/")
        data = await self.request(
            "/cas/client/checkSsoLogin",
            "get",
            params={"ticket": client.get_ticket(service_url), "service": service_url},
            need_token=False,
        )
        if not data["success"]:
            raise RuntimeError(data["message"])
        self._access_token: str = data["result"]["token"]
        self._client.headers.update({"X-Access-Token": self._access_token})
        return self

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

    async def request(
        self,
        url: str,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        need_token: bool = True,
    ) -> dict[str, Any]:
        if need_token and not hasattr(self, "_access_token"):
            raise RuntimeError("Not logged in")

        timestamp = int(time.time() * 1000)
        return (
            await self._client.request(
                method,
                urljoin("/login/wisdom-group-learning-bg", url),
                params={
                    "requestParams": self._encrypt(params or {}, timestamp),
                    "_t": timestamp,
                },
                json={"requestParams": self._encrypt(json or {}, timestamp)},
            )
        ).json()

    async def get_result(self, url: str, *, params: dict[str, Any] | None = None):
        error = RuntimeError("Max retry reached")
        for _ in range(self.retry):
            try:
                data = await self.request(url, "get", params=params)
            except Exception as e:
                error = e
                continue
            if data["success"]:
                return data["result"]
            error = RuntimeError(data["message"])
        raise error

    async def page_search(self, url: str, params: dict[str, Any], max: int, size: int):
        page = 1
        while max:
            new_params = params.copy()
            new_params["pageNo"] = page
            new_params["pageSize"] = size
            result = await self.get_result(url, params=new_params)
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
            "Not in context, please use 'with YouthService()' to create a context"
        ) from None
