"""
API 客户端
==========
底层请求封装: 签名注入、请求发送、响应解析

使用 httpx.AsyncClient, 与 pyustc 其它子包保持异步风格一致。
"""

import base64
import json
import time
from types import TracebackType
from typing import Any, cast

from httpx import AsyncClient, Response

from pyustc.venue_booking.core.sign import build_sign

BASE_URL = "https://sport.ustc.edu.cn/api"

HEADERS_BASE = {
    "Platform": "MiniProgram",
    "Wx-Env": "",
}


class USTCSportClient:
    """核心 API 客户端"""

    def __init__(self, token: str = "", open_id: str = ""):
        self.token = token
        self.open_id = open_id
        self._client = AsyncClient(timeout=15)

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self):
        headers = {**HEADERS_BASE, "content-type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _sign_params(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        ts = int(time.time() * 1000)
        params: dict[str, Any] = {
            **(data or {}),
            "open_id": self.open_id,
            "version": "1.0.0",
            "timestamp": ts,
        }
        params["sign"] = build_sign(params)
        return params

    def _parse_response(self, resp: Response) -> dict[str, Any]:
        text = resp.text
        if not text or "honeypot" in text.lower():
            return {
                "code": 403,
                "message": "蜜罐 Blocked",
                "_raw": text[:100] if text else "(empty)",
            }
        try:
            return cast(dict[str, Any], resp.json())
        except json.JSONDecodeError:
            return {"code": resp.status_code, "message": text[:200]}

    async def login_cas(
        self, ticket: str, wl: str = "", scene: str = ""
    ) -> dict[str, Any]:
        """用 CAS ticket 交换场馆 token。"""
        return await self.post(
            "/login/cas", {"ticket": ticket, "wl_code": wl, "scene": scene}
        )

    async def login_join(
        self, ci: dict[str, Any], pi: dict[str, Any], cp: dict[str, Any]
    ) -> dict[str, Any]:
        """补全用户信息后换取场馆 token。"""
        return await self.post(
            "/login/join", {"cas_info": ci, "player_info": pi, "cas_player": cp}
        )

    async def get(
        self, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """GET: 签名参数通过 URL query 传递"""
        params = self._sign_params(data)
        resp = await self._client.get(
            f"{BASE_URL}{path}", headers=self._headers(), params=params
        )
        return self._parse_response(resp)

    async def post(
        self, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST: 参数签名后 base64 编码放 body"""
        params = self._sign_params(data)
        body = base64.b64encode(
            json.dumps(
                {"all_params": params}, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).decode()
        resp = await self._client.post(
            f"{BASE_URL}{path}", content=body, headers=self._headers()
        )
        return self._parse_response(resp)

    async def request(
        self, method: str, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """通用请求(PUT/DELETE 等非 POST/GET 方法)"""
        params = self._sign_params(data)
        url = f"{BASE_URL}{path}"
        resp = await self._client.request(
            method, url, headers=self._headers(), params=params
        )
        return self._parse_response(resp)
