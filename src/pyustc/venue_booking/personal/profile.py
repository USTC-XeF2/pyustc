"""
个人信息 - 个人数据相关 API
=======================
"""

from typing import Any

from pyustc.venue_booking.core.client import USTCSportClient


async def my_orders(
    client: USTCSportClient, page: int = 1, scene: str = "all", partner: int = 0
) -> dict[str, Any]:
    """我的预约记录

    Args:
        client: API 客户端
        page:   页码
        scene:  筛选场景(all/upcoming/finished 等)
        partner: 是否只看同伴邀请(0/1)

    Returns:
        {code, data: {list: [...], kind_list_v2: {...}}}
    """
    return await client.get(
        "/order", {"page": page, "scene": scene, "partner": partner}
    )


async def order_result(client: USTCSportClient, order_no: str) -> dict[str, Any]:
    """查询订单结果"""
    return await client.get("/order/result/", {"order_no": order_no})


async def my_current(client: USTCSportClient) -> dict[str, Any]:
    """个人信息"""
    return await client.get("/my/current")


async def friend_list(client: USTCSportClient) -> dict[str, Any]:
    """好友列表 + 待处理请求"""
    return await client.get("/friend")


async def friend_search(client: USTCSportClient, keyword: str) -> dict[str, Any]:
    """搜索用户(按昵称/学号搜索可添加的好友)"""
    return await client.get("/friend/search", {"keyword": keyword, "scene": "friend"})


async def friend_request(
    client: USTCSportClient, player: dict[str, Any]
) -> dict[str, Any]:
    """发送好友请求(直接传 player 对象, 如 {id, nickname, avatar, pinyin, salary_no})"""
    return await client.post("/friend/request", player)


async def friend_accept(
    client: USTCSportClient, request_id: int, confirm: bool = True
) -> dict[str, Any]:
    """同意/拒绝好友请求"""
    return await client.request(
        "PUT", f"/friend/request/{request_id}", {"id": request_id, "confirm": confirm}
    )


async def friend_delete(client: USTCSportClient, friend_id: int) -> dict[str, Any]:
    """删除好友(friend_id 在 URL 路径中)"""
    return await client.post(f"/friend/delete/{friend_id}")


async def overflow(client: USTCSportClient) -> dict[str, Any]:
    """违约记录"""
    return await client.get("/overflow")


async def punish(
    client: USTCSportClient, kind_id: int = 0, page: int = 1
) -> dict[str, Any]:
    """惩罚/违规详情"""
    return await client.get(f"/punish/{kind_id}", {"kind_id": kind_id, "page": page})


async def chart(
    client: USTCSportClient, tag: str = "", scene: str = "month"
) -> dict[str, Any]:
    """统计数据"""
    return await client.get("/chart", {"sport_id": tag, "scene": scene})
