"""
认证模块
========
CAS 登录 / Token 管理
"""

try:
    import pyustc
except ImportError:  # pragma: no cover
    pyustc = None

from pyustc.venue_booking.core.client import USTCSportClient


async def cas_login(username: str, password: str) -> USTCSportClient:
    """CAS 统一认证登录, 自动获取 token 和 open_id。

    返回的 client 已带 token, 使用完毕后需 await client.aclose()。
    """
    if pyustc is None:
        raise ImportError("pyustc is required for CAS login")

    async with pyustc.CASClient.login_by_pwd(username, password) as cli:
        ticket = await cli.get_ticket("https://sport.ustc.edu.cn/mp/cas")

    client = USTCSportClient()
    try:
        r = await client.login_cas(ticket)
        d = r.get("data", r) if r.get("code") == 0 else r
        cp = d.get("cas_player") or {}
        ci = d.get("cas_info") or {}
        oid = cp.get("open_id", "")

        if r.get("token") or d.get("token"):
            client.token = r.get("token") or d.get("token")
            client.open_id = oid
            return client

        if oid:
            client.open_id = oid
            jr = await client.login_join(
                ci,
                {
                    "avatar": cp.get("avatar", ""),
                    "mobile": cp.get("mobile", ""),
                    "email": ci.get("email", cp.get("email", "")),
                },
                cp,
            )
            jd = jr.get("data", jr) if jr.get("code") == 0 else jr
            if jd.get("token"):
                client.token = jd["token"]
    except Exception:
        await client.aclose()
        raise

    return client


def login_with_token(token: str, open_id: str) -> USTCSportClient:
    """使用已有的 Token 和 OpenID 登录"""
    return USTCSportClient(token, open_id)
