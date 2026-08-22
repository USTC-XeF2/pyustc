"""示例: 场馆预约(sport)模块用法. 异步版本.

两种登录方式任选其一:

1) 直接用已保存的 Token/OpenID:
     VENUE_TOKEN=... VENUE_OPEN_ID=... python examples/venue_booking.py
2) 交互式 CAS 账密登录, 自动换取 token:
     python examples/venue_booking.py

本示例仅使用只读接口: 个人信息、订单、运动项目列表、场馆日视图。
"""

import asyncio
import os
from getpass import getpass

from pyustc.venue_booking.core.auth import cas_login, login_with_token
from pyustc.venue_booking.core.client import USTCSportClient
from pyustc.venue_booking.personal import profile
from pyustc.venue_booking.venue.query import sport_index, venue_daily


async def _login() -> USTCSportClient:
    token = os.environ.get("VENUE_TOKEN", "")
    open_id = os.environ.get("VENUE_OPEN_ID", "")
    if token and open_id:
        print(f"使用 Token 登录, open_id={open_id!r}")
        return login_with_token(token, open_id)
    username = input("学号: ")
    password = getpass("CAS 密码: ")
    return await cas_login(username, password)


async def main() -> None:
    client = await _login()
    try:
        me = await profile.my_current(client)
        player = (me.get("data") or {}).get("player") or {}
        print(f"用户: {player.get('nickname', '?')}")

        orders = await profile.my_orders(client, page=1)
        print(f"orders code: {orders.get('code')}")

        sports = await sport_index(client)
        print(f"sports code: {sports.get('code')}")

        daily = await venue_daily(client, "tennis")
        print(f"daily tennis code: {daily.get('code')}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
