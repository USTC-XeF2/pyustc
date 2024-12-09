import requests

from ..url import generate_url
from ..passport import Passport

class Interface:
    retry = 3
    def __init__(self, passport: Passport):
        self.session = requests.Session()
        service = generate_url("young", "login/sc-wisdom-group-learning/")
        data = self.request("cas/client/checkSsoLogin", "get", {
            "ticket": passport.get_ticket(service),
            "service": service
        })
        if not data["success"]:
            raise RuntimeError(data["message"])
        self.session.headers.update({
            "X-Access-Token": data["result"]["token"]
        })

    def request(self, url: str, method: str, params: dict[str] = {}) -> dict[str]:
        return self.session.request(
            method,
            generate_url("young", f"login/wisdom-group-learning-bg/{url}"),
            params = params,
            json = {}
        ).json()

    def get_result(self, url: str, params: dict[str] = {}):
        retry = self.retry
        while retry:
            try:
                data = self.request(url, "get", params)
                if not data["success"]:
                    raise
                return data["result"]
            except Exception as e:
                retry -= 1
        raise RuntimeError

    def page_search(self, url: str, params: dict[str], max: int, size: int):
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
            if page >= result["pages"]:
                break
            page += 1
