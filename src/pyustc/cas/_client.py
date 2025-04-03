import os
import json
import requests
import urllib.parse

from ..url import generate_url
from ._info import UserInfo

class CASClient:
    """
    The Central Authentication Service (CAS) client for USTC.
    """
    def __init__(self):
        self._session = requests.Session()

    @classmethod
    def load_token(cls, path: str):
        """
        The token will not be verified, please use `client.is_login` to check the login status.
        """
        with open(path) as rf:
            token = json.load(rf)
        client = cls()
        client.login_by_token(token["tgc"], domain = token["domain"])
        return client

    def _request(self, url: str, site: str = "id", method: str = "get", **kwargs):
        return self._session.request(method, generate_url(site, url), **kwargs)

    def login_by_token(self, token: str, domain: str = ""):
        """
        Login to the system with the given token.
        """
        self._session.cookies.clear()
        self._session.cookies.set("SOURCEID_TGC", token, domain = domain)
        self._request("gate/login")

    def _get_usr_and_pwd(self, usr: str | None, pwd: str | None):
        if not usr:
            usr = os.getenv("USTC_CAS_USR")
        if not pwd:
            pwd = os.getenv("USTC_CAS_PWD")
        if not (usr and pwd):
            raise ValueError("Username and password are required")
        return usr, pwd

    def login_by_pwd(self, username: str = None, password: str = None):
        """
        Login to the system using username and password directly.

        Arguments:
            username: The username to login. If not set, will use the environment variable `USTC_CAS_USR`.
            password: The password to login. If not set, will use the environment variable `USTC_CAS_PWD`.
        """
        usr, pwd = self._get_usr_and_pwd(username, password)
        self._session.cookies.clear()

        login_res = self._request("demo/common/tmpLogin", "portal", "post", data = {
            "ue": usr,
            "pd": pwd
        }).json()
        if not login_res["d"]:
            raise ValueError(login_res["m"])
        self._request("cas/clientredirect", params = {
            "client_name": "ssoOauth",
            "service": generate_url("id", "cas/oauth2.0/callbackAuthorize")
        })

    def login_by_browser(
            self,
            username: str = None,
            password: str = None,
            driver_type: str = "chrome",
            headless: bool = False,
            timeout: int = 20
        ):
        """
        Login to the system using a browser.

        Arguments:
            username: The username to login. If not set, will use the environment variable `USTC_CAS_USR`.
            password: The password to login. If not set, will use the environment variable `USTC_CAS_PWD`.
            driver_type: The type of the browser driver to use.
            headless: Whether to run the browser in headless mode.
            timeout: The timeout for the browser login.
        """
        usr, pwd = self._get_usr_and_pwd(username, password)

        from ._browser_login import login
        token = login(usr, pwd, driver_type, headless, timeout)
        self.login_by_token(token)

    def save_token(self, path: str):
        """
        Save the token to the file.
        """
        for domain in self._session.cookies.list_domains():
            tgc = self._session.cookies.get("SOURCEID_TGC", domain = domain)
            if tgc:
                with open(path, "w") as wf:
                    json.dump({"domain": domain, "tgc": tgc}, wf)
                return
        raise RuntimeError("Failed to get token")

    def logout(self):
        """
        Logout from the system.
        """
        self._request("gate/logout")

    @property
    def is_login(self):
        """
        Check if the user has logged in.
        """
        res = self._request("gate/login")
        return res.url.endswith("index.html")

    def get_info(self):
        """
        Get the user's information. If the user is not logged in, an error will be raised.
        """
        user: dict[str, str] = self._request("gate/getUser").json()
        if (objectId := user.get("objectId")):
            username = user.get("username")
            personId = self._request(f"gate/linkid/api/user/getPersonId/{objectId}").json()["data"]
            info = self._request(
                f"gate/linkid/api/aggregate/user/userInfo/{personId}",
                method = "post"
            ).json()["data"]
            get_nomask = lambda key: self._request(
                "gate/linkid/api/aggregate/user/getNoMaskData",
                method = "post",
                json = {
                    "indentityId": objectId,
                    "standardKey": key
                }
            ).json()["data"]
            return UserInfo(username, info, get_nomask)
        raise RuntimeError("Failed to get info")

    def get_ticket(self, service: str):
        res = self._request(
            "cas/login",
            params = {"service": service},
            allow_redirects = False
        )
        if res.status_code == 302:
            location = res.headers["Location"]
            query = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
            if "ticket" in query:
                return query["ticket"][0]
        raise RuntimeError("Failed to get ticket")
