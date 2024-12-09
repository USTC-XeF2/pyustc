import re
import json
import requests
import urllib.parse

from ..url import generate_url
from .code_processor import code_processer
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
        self.session = requests.Session()
        if path:
            with open(path, "rb") as rf:
                token = json.load(rf)
            self.session.cookies.set("TGC", token["tgc"], domain = token["domain"])

    def _request(self, url: str, method: str = "get", params: dict[str] = {}, data: dict[str] = {}):
        return self.session.request(
            method,
            generate_url("passport", url),
            params = params,
            data = data,
            allow_redirects = False
        )

    def login(self, username: str, password: str, auto_logout: bool = False, code_retry: int = 3):
        """
        Login to the system with the given `username` and `password`.

        If `auto_logout` is True, the previous login will be logged out automatically, otherwise an error will be raised.

        For more details about the validate code, see `pyustc.passport.code_processer`.
        """
        service_url = generate_url("passport", "getInfo")
        res = self._request("login", params = {"service": service_url})
        if res.status_code == 302:
            if auto_logout:
                self.logout()
            else:
                raise RuntimeError("Already login, please logout first")
        # Get LT
        pattern = r'"LT-[a-z0-9]+"'
        try:
            lt = re.search(pattern, res.text).group(0).strip('"')
        except AttributeError:
            raise RuntimeError("Failed to get LT")
        data = {
            "CAS_LT": lt,
            "service": service_url,
            "username": username,
            "password": password
        }
        # Get code
        if "var showCode = '1';" in res.text:
            while (code_retry + 1):
                code_res = self._request("validatecode.jsp", params = {"type": "login"})
                code = code_processer(code_res.content)
                if code:
                    data["LT"] = code
                    break
                code_retry -= 1
            else:
                raise RuntimeError("Failed to get code")
        # Login
        post_res = self._request("login", "post", data = data)
        if post_res.status_code == 302:
            return
        # Check error
        if (match := re.search(r'var msg = "(.*?)"', post_res.text)):
            msg = match.group(1)
            if "验证码错误" in msg and code_retry > 1:
                self.login(username, password, auto_logout, code_retry - 1)
                return
            raise ValueError(msg)
        count = re.search(r'var count = "\d"', post_res.text)
        if count:
            count = int(count.group(0).split('"')[1])
            raise ValueError(f"Login password error, account will be locked after {5 - count} attempts")
        raise RuntimeError("Failed to get ticket")

    def save_token(self, path: str):
        """
        Save the token to the file.
        """
        for domain in self.session.cookies.list_domains():
            tgc = self.session.cookies.get("TGC", domain = domain)
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
