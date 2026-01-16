from collections.abc import Awaitable, Callable


class UserInfo:
    """The user's information in the CAS system."""

    def __init__(
        self, id: str, data: dict[str, str], get_nomask: Callable[[str], Awaitable[str]]
    ):
        self.id = id
        self.name = data["XM"]
        self.gid = data["GID"]
        self.email = data["MBEMAIL"]
        self._get_nomask = get_nomask

    async def get_idcard(self) -> str:
        return await self._get_nomask("IDCARD")

    async def get_phone(self) -> str:
        return await self._get_nomask("TEL")

    def __repr__(self):
        return f"<UserInfo {self.id} {self.name}>"
