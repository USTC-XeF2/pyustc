from urllib.parse import urljoin

_root_url = {
    "passport": "https://passport.ustc.edu.cn",
    "edu_system": "https://jw.ustc.edu.cn",
    "blackboard": "https://www.bb.ustc.edu.cn",
    "young": "https://young.ustc.edu.cn",
}

def generate_url(website: str, path: str) -> str:
    return urljoin(_root_url[website], path)

def get_root_url(website: str) -> str:
    if website not in _root_url:
        raise ValueError("Invalid website")
    return _root_url[website]

def set_root_url(website: str, url: str):
    if website not in _root_url:
        raise ValueError("Invalid website")
    _root_url[website] = url

__all__ = ["get_root_url", "set_root_url"]
