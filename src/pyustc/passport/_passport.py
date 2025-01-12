import os
import json
import requests
import urllib.parse

from ..url import generate_url
from ._portal import Portal
from ._info import PassportInfo

class Passport:
    """
    The Unified Identity Authentication System of USTC.
    """
    def __init__(self, path: str = None):
        """
        Initialize a Passport object.

        If `path` is set, the token will be loaded from the file, but it will not be verified. Please use `is_login` to check the login status.
        """
        self._session = requests.Session()
        if path:
            with open(path, "rb") as rf:
                token = json.load(rf)
            self._session.cookies.set("TGC", token["tgc"], domain = token["domain"])

    def _request(self, url: str, method: str = "get", **kwargs):
        return self._session.request(
            method,
            generate_url("passport", url),
            allow_redirects = False,
            **kwargs
        )

    def login(self, username: str = None, password: str = None, auto_logout: bool = False):
        """
        Login to the system with the given `username` and `password`.

        If `username` or `password` is not set, the environment variable `USTC_PASSPORT_USR` or `USTC_PASSPORT_PWD` will be used.

        If `auto_logout` is True, the previous login will be logged out automatically, otherwise an error will be raised.
        """
        if not username:
            
            username = os.getenv("USTC_PASSPORT_USR")
        if not password:
            password = os.getenv("USTC_PASSPORT_PWD")
        if self.is_login:
            if auto_logout:
                self.logout()
            else:
                raise RuntimeError("Already login, please logout first")
        portal = Portal()
        portal.login(username, password)
        res = portal.authorize(
            generate_url("passport", "login"),
            generate_url("passport", "getInfo")
        )
        if res.status_code == 302:
            location = res.headers["Location"]
            self._session.get(location)
        else:
            raise RuntimeError("Failed to login")

    def save_token(self, path: str):
        """
        Save the token to the file.
        """
        for domain in self._session.cookies.list_domains():
            tgc = self._session.cookies.get("TGC", domain = domain)
            if tgc:
                with open(path, "w") as wf:
                    json.dump({"domain": domain, "tgc": tgc}, wf)
                return
        raise RuntimeError("Failed to get token")

    def logout(self):
        """
        Logout from the system.
        """
        self._request("logout")

    @property
    def is_login(self):
        """
        Check if the user has logged in.
        """
        res = self._request("getInfo")
        return res.status_code == 200

    def get_info(self):
        """
        Get the user's information. If the user is not logged in, an error will be raised.
        """
        res = self._request("getInfo")
        if res.status_code == 200:
            return PassportInfo(res.text)
        raise RuntimeError("Failed to get info")

    def get_ticket(self, service: str):
        res = self._request("login", params = {"service": service})
        if res.status_code == 302:
            location = res.headers["Location"]
            query = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
            if "ticket" in query:
                return query["ticket"][0]
        raise RuntimeError("Failed to get ticket")
