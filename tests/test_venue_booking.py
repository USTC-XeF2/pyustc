"""venue_booking 子包的单元测试. 不触网."""

import asyncio
import base64
import json
import os

import httpx

from pyustc.venue_booking.core.client import USTCSportClient
from pyustc.venue_booking.core.sign import build_sign

# httpx 不支持 socks:// 代理协议(用户机常驻), 测试全程离线, 先清掉代理环境变量
for _key in ("all_proxy", "ALL_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_key, None)

HONEYPOT_CODE = 403


def test_sign_known_output():
    # 由实现离线算出的固定结果, 防止签名算法被无意改动.
    assert build_sign({"a": "1", "b": 2}) == "3a06093e67b9a38bec3ff2194ccce7a4"


def test_sign_skips_none_and_empty():
    base = build_sign({"a": "1"})
    assert build_sign({"a": "1", "z": None}) == base
    assert build_sign({"a": "1", "e": ""}) == base


def test_sign_bool_serialization():
    assert build_sign({"f": True}) == build_sign({"f": "true"})


def test_sign_nested_json():
    assert build_sign({"d": {"x": 1}}) == build_sign({"d": '{"x":1}'})


def _client_with_handler(handler) -> USTCSportClient:
    client = USTCSportClient("tok", "oid")
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


def test_async_get_signs_query():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"code": 0, "data": "ok"})

    async def scenario():
        client = _client_with_handler(handler)
        result = await client.get("/sport/index", {"page": 1})
        await client.aclose()
        return result

    result = asyncio.run(scenario())
    assert result["code"] == 0
    assert captured["path"] == "/api/sport/index"
    params = captured["params"]
    assert params["sign"]
    expected = build_sign({k: v for k, v in params.items() if k != "sign"})
    assert params["sign"] == expected


def test_async_post_base64_body():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"code": 0})

    async def scenario():
        client = _client_with_handler(handler)
        result = await client.post("/login/cas", {"ticket": "ST-1"})
        await client.aclose()
        return result

    result = asyncio.run(scenario())
    assert result["code"] == 0
    payload = json.loads(base64.b64decode(captured["body"]).decode())
    params = payload["all_params"]
    assert params["sign"]
    expected = build_sign({k: v for k, v in params.items() if k != "sign"})
    assert params["sign"] == expected


def test_parse_honeypot():
    client = USTCSportClient()
    parsed = client._parse_response(httpx.Response(200, text="honeypot trap"))
    assert parsed["code"] == HONEYPOT_CODE
