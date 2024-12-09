from bs4 import BeautifulSoup

class PassportInfo:
    """
    The user's information in passport.
    """
    def __init__(self, text: str):
        soup = BeautifulSoup(text, "html.parser")
        self.name = soup.find("span", text="姓名").find_next_sibling("span", class_="field_value").text
        self.gid = int(soup.find("span", text="GID").find_next_sibling("span", class_="field_value").text)
        self.id = soup.find("div", text="证件号码").find_next("span", class_="field_value").text
        self.email = soup.find("div", text="邮箱").find_next("span", class_="field_value").text
        self.phone = soup.find("div", text="手机号").find_next("span", class_="field_value").text

    def __repr__(self):
        return f"<PassportInfo {self.id} {self.name}>"
