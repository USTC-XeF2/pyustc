import base64
import json
import os
import re
from collections.abc import Awaitable, Callable
from types import TracebackType
from urllib.parse import parse_qs, urlparse

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from httpx import AsyncClient

from pyustc._url import root_url

from .info import UserInfo

AsyncTokenSetter = Callable[[AsyncClient], Awaitable[bool]]


class CASClient:
    """
    The Central Authentication Service (CAS) client for USTC.
    """

    def __init__(
        self, token_setter: AsyncTokenSetter | None = None, base_url: str | None = None
    ):
        self._token_setter = token_setter
        self._client = AsyncClient(base_url=base_url or root_url["id"])

    async def __aenter__(self):
        await self._client.__aenter__()

        should_check = True
        if self._token_setter is not None:
            should_check = await self._token_setter(self._client)
        del self._token_setter

        if should_check:
            res = await self._client.get("/cas/login")
            if not res.is_redirect:
                raise RuntimeError("Failed to login with the token")

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ):
        await self._client.__aexit__(exc_type, exc_value, traceback)

    @staticmethod
    async def _set_token_by_pwd(
        client: AsyncClient, usr: str | None = None, pwd: str | None = None
    ):
        if not usr:
            usr = os.getenv("USTC_CAS_USR")
        if not pwd:
            pwd = os.getenv("USTC_CAS_PWD")
        if not (usr and pwd):
            raise ValueError("Username and password are required")

        page = await client.get("/cas/login")
        crypto = re.search(r'<p id="login-croypto">(.+)</p>', page.text)
        flow_key = re.search(r'<p id="login-page-flowkey">(.+)</p>', page.text)
        if not (crypto and flow_key):
            raise RuntimeError("Failed to get login parameters")

        crypto = crypto.group(1)
        flow_key = flow_key.group(1)
        cipher = AES.new(base64.b64decode(crypto), AES.MODE_ECB)

        def aes_encrypt(data: str):
            return base64.b64encode(
                cipher.encrypt(pad(data.encode(), AES.block_size))
            ).decode()

        data: dict[str, str] = {
            "type": "UsernamePassword",
            "_eventId": "submit",
            "croypto": crypto,
            "username": usr,
            "password": aes_encrypt(pwd),
            "captcha_payload": aes_encrypt("{}"),
            "execution": flow_key,
        }
        res = await client.post("/cas/login", data=data)
        if not res.is_redirect:
            pattern = r'<div\s+class="alert alert-danger"\s+id="login-error-msg">\s*<span>([^<]+)</span>\s*</div>'
            match = re.search(pattern, res.text)
            raise RuntimeError(match.group(1) if match else "Login failed")

        return False

    @classmethod
    def login_by_pwd(cls, username: str | None = None, password: str | None = None):
        """
        Login to the system using username and password directly.

        Arguments:
            username: The username to login. If not set, will use the environment variable `USTC_CAS_USR`.
            password: The password to login. If not set, will use the environment variable `USTC_CAS_PWD`.
        """
        return cls(lambda client: cls._set_token_by_pwd(client, username, password))

    @classmethod
    def load_token(cls, path: str, fallback_to_pwd: bool = True):
        """
        Load the token from the file and create a CASClient instance.

        Arguments:
            path: The path to the token file.
            fallback_to_pwd: Whether to fallback to username/password login if the token is invalid.
        """
        with open(path) as rf:
            token = json.load(rf)

        async def login_by_token(client: AsyncClient):
            client.cookies.set(
                "SOURCEID_TGC", token["tgc"], domain=token.get("domain", "")
            )
            if not fallback_to_pwd:
                return True

            res = await client.get("/cas/login")
            if not res.is_redirect:
                client.cookies.delete("SOURCEID_TGC", domain=token.get("domain"))
                return await cls._set_token_by_pwd(client)
            return False

        return cls(login_by_token)

    def save_token(self, path: str):
        """
        Save the token to the file.
        """
        for cookie in self._client.cookies.jar:
            if cookie.name == "SOURCEID_TGC":
                with open(path, "w") as wf:
                    json.dump({"domain": cookie.domain, "tgc": cookie.value}, wf)
                return
        raise RuntimeError("Failed to get token")

    async def logout(self):
        """
        Logout from the system.
        """
        await self._client.get("/gate/logout")

    async def get_info(self):
        """
        Get the user's information. If the user is not logged in, an error will be raised.
        """
        user: dict[str, str] = (
            await self._client.get("/gate/getUser", follow_redirects=True)
        ).json()
        if object_id := user.get("objectId"):
            person_id = (
                await self._client.get(f"/gate/linkid/api/user/getPersonId/{object_id}")
            ).json()["data"]
            info = (
                await self._client.post(
                    f"/gate/linkid/api/aggregate/user/userInfo/{person_id}"
                )
            ).json()["data"]

            async def get_nomask(key: str):
                return (
                    await self._client.post(
                        "/gate/linkid/api/aggregate/user/getNoMaskData",
                        json={"indentityId": object_id, "standardKey": key},
                    )
                ).json()["data"]

            return UserInfo(user["username"], info, get_nomask)
        raise RuntimeError("Failed to get info")

    async def get_ticket(self, service: str):
        res = await self._client.get("cas/login", params={"service": service})
        if res.has_redirect_location:
            location = res.headers["Location"]
            query = parse_qs(urlparse(location).query)
            if "ticket" in query:
                return query["ticket"][0]
        raise RuntimeError("Failed to get ticket")
