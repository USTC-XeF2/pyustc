"""
认证模块
========
CAS 登录 / Token 管理
"""

from typing import Any, cast

import pyustc
from pyustc.venue_booking.core.client import USTCSportClient


def _as_response_data(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


async def cas_login(username: str, password: str) -> USTCSportClient:
    """CAS 统一认证登录, 自动获取 token 和 open_id。

    返回的 client 已带 token, 使用完毕后需 await client.aclose()。
    """
    async with pyustc.CASClient.login_by_pwd(username, password) as cli:
        ticket = await cli.get_ticket("https://sport.ustc.edu.cn/mp/cas")

    client = USTCSportClient()
    try:
        r = await client.login_cas(ticket)
        d = _as_response_data(r.get("data", r)) if r.get("code") == 0 else r
        cp = _as_response_data(d.get("cas_player"))
        ci = _as_response_data(d.get("cas_info"))
        oid_value: object = cp.get("open_id", "")
        oid = oid_value if isinstance(oid_value, str) else ""

        token_value: object = r.get("token") or d.get("token")
        if isinstance(token_value, str) and token_value:
            client.token = token_value
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
            jd = _as_response_data(jr.get("data", jr)) if jr.get("code") == 0 else jr
            joined_token: object = jd.get("token")
            if isinstance(joined_token, str) and joined_token:
                client.token = joined_token
    except Exception:
        await client.aclose()
        raise

    return client


def login_with_token(token: str, open_id: str) -> USTCSportClient:
    """使用已有的 Token 和 OpenID 登录"""
    return USTCSportClient(token, open_id)
