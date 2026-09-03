"""venue_booking 子包的单元测试. 不触网."""

import asyncio
import base64
import json
import os
from collections.abc import Callable
from typing import Any, cast

import httpx

from pyustc.venue_booking.core.client import USTCSportClient
from pyustc.venue_booking.core.sign import build_sign

# httpx 不支持 socks:// 代理协议(用户机常驻), 测试全程离线, 先清掉代理环境变量
for _key in ("all_proxy", "ALL_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_key, None)

HONEYPOT_CODE = 403


def test_sign_known_output() -> None:
    # 由实现离线算出的固定结果, 防止签名算法被无意改动.
    assert build_sign({"a": "1", "b": 2}) == "3a06093e67b9a38bec3ff2194ccce7a4"


def test_sign_skips_none_and_empty() -> None:
    base = build_sign({"a": "1"})
    assert build_sign({"a": "1", "z": None}) == base
    assert build_sign({"a": "1", "e": ""}) == base


def test_sign_bool_serialization() -> None:
    assert build_sign({"f": True}) == build_sign({"f": "true"})


def test_sign_nested_json() -> None:
    assert build_sign({"d": {"x": 1}}) == build_sign({"d": '{"x":1}'})


def _client_with_handler(
    handler: Callable[[httpx.Request], httpx.Response],
) -> USTCSportClient:
    return USTCSportClient("tok", "oid", transport=httpx.MockTransport(handler))


def test_async_get_signs_query() -> None:
    captured_path: str | None = None
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_path, captured_params
        captured_path = request.url.path
        captured_params = dict(request.url.params)
        return httpx.Response(200, json={"code": 0, "data": "ok"})

    async def scenario() -> dict[str, Any]:
        client = _client_with_handler(handler)
        result = await client.get("/sport/index", {"page": 1})
        await client.aclose()
        return result

    result = asyncio.run(scenario())
    assert result["code"] == 0
    assert captured_path == "/api/sport/index"
    params = captured_params
    assert params["sign"]
    expected = build_sign({k: v for k, v in params.items() if k != "sign"})
    assert params["sign"] == expected


def test_async_post_base64_body() -> None:
    captured_body: str | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = request.content.decode()
        return httpx.Response(200, json={"code": 0})

    async def scenario() -> dict[str, Any]:
        client = _client_with_handler(handler)
        result = await client.post("/login/cas", {"ticket": "ST-1"})
        await client.aclose()
        return result

    result = asyncio.run(scenario())
    assert result["code"] == 0
    assert captured_body is not None
    payload = cast(dict[str, Any], json.loads(base64.b64decode(captured_body).decode()))
    params = cast(dict[str, Any], payload["all_params"])
    assert params["sign"]
    expected = build_sign({k: v for k, v in params.items() if k != "sign"})
    assert params["sign"] == expected


def test_parse_honeypot() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="honeypot trap")

    async def scenario() -> dict[str, Any]:
        client = _client_with_handler(handler)
        result = await client.get("/sport/index")
        await client.aclose()
        return result

    parsed = asyncio.run(scenario())
    assert parsed["code"] == HONEYPOT_CODE
