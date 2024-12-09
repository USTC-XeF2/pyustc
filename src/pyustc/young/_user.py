from ._interface import Interface

class User:
    _interface: Interface = None
    def __init__(self, data: dict[str]):
        self.name: str = data["realname"]
        self.id: str = data["id"]
        self.gender: str = data["sex_dictText"]
        self.avatar: str = data["avatar"]
        self.grade: str = data["grade"]
        self.college: str = data["college"]
        self.scientificValue: int = data["scientificqiValue"]
        self.birthday: str = data["birthday"]

    def __repr__(self):
        return f"<User {self.id} {repr(self.name)}>"
