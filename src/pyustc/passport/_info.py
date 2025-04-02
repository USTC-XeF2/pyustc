class UserInfo:
    """
    The user's information in the CAS system.
    """
    def __init__(self, id: str, data: dict[str, str], get_nomask):
        self.id = id
        self.name = data["XM"] 
        self.gid = data["GID"]
        self.email = data["MBEMAIL"]
        self._get_nomask = get_nomask

    @property
    def idcard(self) -> str:
        return self._get_nomask("IDCARD")

    @property
    def phone(self) -> str:
        return self._get_nomask("TEL")

    def __repr__(self):
        return f"<UserInfo {self.id} {self.name}>"
