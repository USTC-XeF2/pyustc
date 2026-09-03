"""
场馆预约 - 订单管理
==================
取消、删除、同意/拒绝邀请、退出订单。

预订与改签接口需要客户端环境生成的验证字段, Python 端无法构造, 故不在此提供。
"""

from typing import Any

from pyustc.venue_booking.core.client import USTCSportClient


async def cancel_order(client: USTCSportClient, order_no: str) -> dict[str, Any]:
    """取消订单(order_no 在 URL 路径中, 不带额外参数)"""
    return await client.post(f"/order/cancel/{order_no}")


async def delete_order(client: USTCSportClient, order_no: str) -> dict[str, Any]:
    """删除订单(order_no 在 URL 路径中, 不带额外参数)"""
    return await client.post(f"/order/delete/{order_no}")


async def join_order(
    client: USTCSportClient, order_no: str, agree: bool
) -> dict[str, Any]:
    """同意/拒绝加入邀请"""
    return await client.post(f"/order/join/{order_no}", {"agree": agree})


async def quit_order(client: USTCSportClient, order_no: str) -> dict[str, Any]:
    """退出订单"""
    return await client.post(f"/order/quit/{order_no}")
