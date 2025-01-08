import requests

from ..url import generate_url

class Portal:
    def __init__(self):
        self._session = requests.Session()

    def _request(self, url: str, method: str = "get", **kwargs):
        return self._session.request(
            method,
            generate_url("portal", url),
            **kwargs
        )

    def login(self, username: str, password: str):
        res = self._request("demo/common/tmpLogin", "post", data = {
            "ue": username,
            "pd": password
        }).json()
        if not res["d"]:
            raise ValueError(res["m"])

    def authorize(self, redirect_uri: str, state: str):
        return self._request("demo/site/connect/oauth2/authorize", params = {
            "appid": ".",
            "redirect_uri": redirect_uri,
            "state": f"app-{state}"
        }, allow_redirects = False)
