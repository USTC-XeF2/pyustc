from urllib.parse import urljoin

root_url = {
    "id": "https://id.ustc.edu.cn",
    "eams": "https://jw.ustc.edu.cn",
    "young": "https://young.ustc.edu.cn",
}


def generate_url(website: str, path: str) -> str:
    return urljoin(root_url[website], path)
