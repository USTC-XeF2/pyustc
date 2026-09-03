"""
场馆查询
========
仅包含已确认可用的只读查询接口。
"""

from typing import Any

from pyustc.venue_booking.core.client import USTCSportClient


async def sport_index(client: USTCSportClient) -> dict[str, Any]:
    """运动项目列表"""
    return await client.get("/sport/index")


async def kind_enum(client: USTCSportClient) -> dict[str, Any]:
    """运动类型枚举"""
    return await client.get("/kind-enum")


async def venue_daily(client: USTCSportClient, kind: str) -> dict[str, Any]:
    """日视图(daily 类型场馆)"""
    return await client.get(f"/venue/daily/{kind}")


async def venue_weekly(client: USTCSportClient, kind: str) -> dict[str, Any]:
    """周视图"""
    return await client.get(f"/venue/weekly/{kind}")


async def venue_info(client: USTCSportClient, kind: str) -> dict[str, Any]:
    """场馆信息(block 类型)"""
    return await client.get(f"/venue/{kind}")


async def venue_warn(client: USTCSportClient, kind: str) -> dict[str, Any]:
    """场馆警告"""
    return await client.get(f"/venue/warn/{kind}")
