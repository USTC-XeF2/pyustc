import os
import re
import json
import base64
import requests
import urllib.parse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from ..url import generate_url
from ._info import UserInfo

class CASClient:
    """
    The Central Authentication Service (CAS) client for USTC.
    """
    def __init__(self):
        self._session = requests.Session()

    @classmethod
    def load_token(cls, path: str, check: bool = True):
        """
        Load the token from the file and create a CASClient instance.

        Arguments:
            path: The path to the token file.
            check: Whether to check the login status after loading the token, raise an error if not logged in.
        """
        with open(path) as rf:
            token = json.load(rf)
        client = cls()
        client.login_by_token(token["tgc"], domain=token["domain"], check=check)
        return client

    def _request(self, url: str, method: str = "get", **kwargs):
        return self._session.request(method, generate_url("id", url), **kwargs)

    def login_by_token(self, token: str, domain: str = "", check: bool = True):
        """
        Login to the system with the given token.

        Arguments:
            token: The token to login.
            domain: The domain of the token, if not set, will use the default domain.
            check: Whether to check the login status after setting the token, raise an error if not logged in.
        """
        self._session.cookies.clear()
        self._session.cookies.set("SOURCEID_TGC", token, domain=domain) # type: ignore
        if check and not self.is_login:
            raise RuntimeError("Failed to login with the token")

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

        page = self._request("cas/login").text
        crypto = re.search(r'<p id="login-croypto">(.+)</p>', page).group(1)
        flow_key = re.search(r'<p id="login-page-flowkey">(.+)</p>', page).group(1)

        cipher = AES.new(base64.b64decode(crypto), AES.MODE_ECB)
        aes_encrypt = lambda data: base64.b64encode(
            cipher.encrypt(pad(data.encode(), AES.block_size))
        ).decode()

        data = {
            "type": "UsernamePassword",
            "_eventId": "submit",
            "croypto": crypto,
            "username": usr,
            "password": aes_encrypt(pwd),
            "captcha_payload": aes_encrypt("{}"),
            "execution": flow_key,
        }
        res = self._request(
            "cas/login",
            method = "post",
            data = data,
            allow_redirects = False
        )
        if res.status_code != 302:
            pattern = r'<div\s+class="alert alert-danger"\s+id="login-error-msg">\s*<span>([^<]+)</span>\s*</div>'
            match = re.search(pattern, res.text)
            raise RuntimeError(match.group(1) if match else "Login failed")

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
        for cookie in self._session.cookies:
            if cookie.name == "SOURCEID_TGC":
                with open(path, "w") as wf:
                    json.dump({"domain": cookie.domain, "tgc": cookie.value}, wf)
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
        res = self._request("cas/login", allow_redirects=False)
        return res.status_code == 302

    def get_info(self):
        """
        Get the user's information. If the user is not logged in, an error will be raised.
        """
        user: dict[str, str] = self._request("gate/getUser").json()
        if (objectId := user.get("objectId")):
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
            return UserInfo(user["username"], info, get_nomask)
        raise RuntimeError("Failed to get info")

    def get_ticket(self, service: str):
        res = self._request(
            "cas/login",
            params={"service": service},
            allow_redirects=False
        )
        if res.status_code == 302:
            location = res.headers["Location"]
            query = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
            if "ticket" in query:
                return query["ticket"][0]
        raise RuntimeError("Failed to get ticket")
